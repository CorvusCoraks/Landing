""" Модуль конкретного проекта. """
from torch import Tensor, cuda, tensor
from torch.nn import Module, Sequential
from fl_store.store_nn import ModuleStorage
from state import State
from fl_store.store_st import StateStorage
from typing import Dict, Optional, List, Tuple, Union
from net import NetSeq
from tools import Reinforcement, Finish, action_variants, Bit, zo
from basics import TestId, TENSOR_DTYPE, EVAL, GRAVITY_ACCELERATION_ABS, CUDA0, CPU, ZeroOne
from structures import RealWorldStageStatusN
from math import atan2, pi
from nn_iface.norm import ListMinMaxNormalization, MinMax, MinMaxXY
from point import VectorComplex
from nn_iface.projects import AbstractProject
from app_cfg import PROJECT_CONFIG_FILE, PROJECT_DIRECTORY_PATH
from DevTmpPr.cfg import ACTOR_INPUT, ACTOR_HIDDEN, ACTOR_OUTPUT, ACTOR_OPTIONS
from DevTmpPr.cfg import CRITIC_INPUT, CRITIC_HIDDEN, CRITIC_OUTPUT, CRITIC_OPTIONS
from DevTmpPr.cfg import POSITION_MINMAX, LINE_VELOCITY_MINMAX, LINE_ACCELERATION_MINMAX
from DevTmpPr.cfg import ORIENTATION_MINMAX, ANGULAR_VELOCITY_MINMAX, ANGULAR_ACCELERATION_MINMAX
from DevTmpPr.cfg import NN_STORAGE_FILENAME, STATE_STORAGE_FILENAME
from DevTmpPr.cfg import JETS_COUNT


class ProjectMainClass(AbstractProject):
    """ Конкретный проект испытываемой системы управления. Конкретизирующие настроечные параметры тут. """
    def __init__(self):
        super().__init__()

        nn_filename = PROJECT_DIRECTORY_PATH + NN_STORAGE_FILENAME
        state_filename = PROJECT_DIRECTORY_PATH + STATE_STORAGE_FILENAME

        # Хранилища для модуля НС
        self._load_storage_model = ModuleStorage(nn_filename)
        self._save_storage_model = self._load_storage_model
        # Хранилище для состояния процесса обучения.
        self._load_storage_training_state = StateStorage(state_filename)
        self._save_storage_training_state = self._load_storage_training_state
        # Хранилище для состояния НС
        self._load_storage_model_state = self._load_storage_training_state
        self._save_storage_model_state = self._load_storage_training_state

        self._training_state = State()

        # В хранилище состояния процесса сохраняться не будет.
        self._device = CUDA0 if cuda.is_available() else CPU

        self._reinforcement = Reinforcement()

        self._finish = Finish()

        self.__normaliaztion: ListMinMaxNormalization = ListMinMaxNormalization([
            POSITION_MINMAX, LINE_VELOCITY_MINMAX, LINE_ACCELERATION_MINMAX,
            ORIENTATION_MINMAX, ANGULAR_VELOCITY_MINMAX, ANGULAR_ACCELERATION_MINMAX
        ])

    def load_nn(self) -> None:
        try:
            super().load_nn()
        except FileNotFoundError:
            # Создание нейросетей.
            #
            # Актор.
            inp: Sequential = Sequential(*ACTOR_INPUT)
            hid: Sequential = Sequential(*ACTOR_HIDDEN)
            out: Sequential = Sequential(*ACTOR_OUTPUT)
            self._actor: Module = NetSeq(inp, hid, out, **ACTOR_OPTIONS)

            #
            # Критик.
            # размерность ac_input уже включает в себя размерность входных данных плюс один вход на подкрепление
            # Но в данном случае, на вход критика уже подаётся подкрепление ставшее результатом данного шага,
            # а не предыдущего.
            # вход критика = выход актора + вход актора
            inp: Sequential = Sequential(*CRITIC_INPUT)
            hid: Sequential = Sequential(*CRITIC_HIDDEN)
            out: Sequential = Sequential(*CRITIC_OUTPUT)
            self._critic: Module = NetSeq(inp, hid, out, **CRITIC_OPTIONS)

    def load_state(self) -> None:
        try:
            # # загружаем состояние из хранилища
            super().load_state()
        except FileNotFoundError:
            # Задание начальных состояний для параметров испытаний.
            self._training_state.batch_size = 1
            self._training_state.epoch_start = 0
            self._training_state.epoch_current = 0
            self._training_state.epoch_stop = 2
            self._training_state.prev_q_max = 0

    def actor_input_preparation(self, raw_batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:
        """

        :param raw_batch: raw steak (сырое мясо) - словарь неподготовленных исходных данных
        :return: входной тензор актора, и список идентификаторов теста, соответствующий порядку элементов в тензоре.
        """
        # Список-заготовка (rare steak, стейк с кровью) входных данных, список списков,
        # элемент которого является состоянием изделия.
        rare_list: List[List[Optional[ZeroOne]]] = [[] for a in range(len(raw_batch))]
        # Список-заготовка идентификаторов испытаний (Необходим в будущем для состыковки результатов с идентификаторами)
        # test_id_list: List[TestId] = [0 for a in range(len(raw_batch))]

        for index, test_id in enumerate(s_order):
            # Из списка идентификаторов тестов по очерёдно извлекаем индексы и идентификаторы.

            # Ориентация изделия (угол отклонения в радианах от оси OY в СКЦМ)
            orientation_rad: float = 0 if raw_batch[test_id].orientation.x == 0 \
                else atan2(-raw_batch[test_id].orientation.x, raw_batch[test_id].orientation.y)

            # Проверка знака угла для правой и левой координатной полуплоскости
            # В правой полуплоскости знак угла отрицательный, в левой - положительный (отсчёт от оси OY СКЦМ)
            assert (raw_batch[test_id].orientation.x > 0 and orientation_rad < 0) \
                   or (raw_batch[test_id].orientation.x < 0 and orientation_rad > 0) \
                   or (raw_batch[test_id].orientation.x == 0 and orientation_rad == 0), \
                "Signs mismatch for angle and vector orientation"

            # Нормализация входных данных. VectorComplex возвращается как VectorComplex.
            rare_list[index] = self.__normaliaztion.normalization([raw_batch[test_id].position,
                                                                   raw_batch[test_id].velocity,
                                                                   raw_batch[test_id].acceleration,
                                                                   orientation_rad,
                                                                   raw_batch[test_id].angular_velocity,
                                                                   raw_batch[test_id].angular_acceleration])

            # Список, который дальше пойдёт в конструктор тензора.
            rare_float_list: List[float] = []

            for i, state_element in enumerate(rare_list[index]):
                # Заполнение итогового списка (будет состоять из float)
                if isinstance(state_element, VectorComplex):
                    # Преобразование объектов VectorComplex в пары нормализованных float.
                    rare_float_list.extend([zo(state_element.x), zo(state_element.y)])
                elif isinstance(state_element, float):
                    # Если нормализованная величина уже float, включаем как float
                    rare_float_list.append(zo(state_element))
                else:
                    raise TypeError('Wrong type object {} in list'.format(type(state_element)))

        # Входной тензор.
        input_tensor: Tensor = tensor([rare_float_list], dtype=TENSOR_DTYPE, requires_grad=True)

        return input_tensor

        # for index, (key, value) in enumerate(raw_batch.items()):
        #     # Из словаря данных для батча извлекаем параметры состояний для каждого испытания.
        #
        #     # Ориентация изделия (угол отклонения в радианах от оси OY в СКЦМ)
        #     orientation_rad: float = 0 if value.orientation.x == 0 else atan2(-value.orientation.x, value.orientation.y)
        #
        #     # Проверка знака угла для правой и левой координатной полуплоскости
        #     # В правой полуплоскости знак угла отрицательный, в левой - положительный (отсчёт от оси OY СКЦМ)
        #     assert (value.orientation.x > 0 and orientation_rad < 0) \
        #            or (value.orientation.x < 0 and orientation_rad > 0) \
        #            or (value.orientation.x == 0 and orientation_rad == 0), \
        #         "Signs mismatch for angle and vector orientation"
        #
        #     rare_list[index] = self.__normaliaztion.normalization([value.position, value.velocity, value.acceleration,
        #                                                      orientation_rad,
        #                                                      value.angular_velocity, value.angular_acceleration])
        #
        #     test_id_list[index] = key
        #
        #     rare_float_list: List[float] = []
        #     for i, state_element in enumerate(rare_list[index]):
        #         if isinstance(state_element, VectorComplex):
        #             rare_float_list.extend([state_element.x, state_element.y])
        #         elif isinstance(state_element, float):
        #             rare_float_list.append(state_element)
        #         else:
        #             raise TypeError('Wrong type object {} in list'.format(type(state_element)))
        #         # rare_float_list
        #
        # # Входной тензор.
        # input: Tensor = tensor([rare_float_list], dtype=TENSOR_DTYPE, requires_grad=True)
        #
        # return input

    def critic_input_preparation(self, actor_input: Tensor, actor_output: Tensor,
                                 environment_batch: Dict[TestId, RealWorldStageStatusN]) -> Tensor:
        action_var: List[List[Bit]] = action_variants(JETS_COUNT)
        result: List[List[ZeroOne]] = []
        for test in environment_batch:
            pass



