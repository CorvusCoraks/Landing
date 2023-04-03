""" Модуль конкретного проекта. """
from torch import Tensor, cuda, tensor, zeros, repeat_interleave, tile, scatter, split, max, int64
from torch.nn import Module, Sequential
from fl_store.store_nn import ModuleStorage
from state import State
from fl_store.store_st import StateStorage
from typing import Dict, Optional, List, Tuple, Union
from net import NetSeq
from tools import Reinforcement, Finish, action_variants, Bit, zo
from basics import TestId, TENSOR_DTYPE, TENSOR_INDEX_DTYPE, EVAL, GRAVITY_ACCELERATION_ABS, CUDA0, CPU, ZeroOne, Bit, Q_EST_NEXT, INDEX_IN_TEST
from basics import Q_est_value, Index_value, Dict_key
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
from DevTmpPr.cfg import JETS_COUNT, ALPHA, GAMMA


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

        # Список возможных действий актора.
        self.__action_var: List[List[Bit]] = action_variants(JETS_COUNT)

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

    def critic_input_preparation(self, actor_input: Tensor, actor_output: Tensor,
                                 environment_batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:

        # Список возможных действий актора.
        # action_var: List[List[Bit]] = action_variants(JETS_COUNT)

        # Подготовка целевого тезнора.
        # Клонируем вход актора,
        critic_in = actor_input.clone()
        # затем расширяем первое измерение клона на размер первого измерения списка возможных действий актора
        # Список повторений каждого элемента по горизонтали.
        # Все элементы повторяются 1 раз, ...
        rep = [1 for a in critic_in[0]]
        # ... кроме последнего элемента, который повторяясь задаёт место под будущие варианты действий актора.
        rep[len(rep)-1] = len(self.__action_var[0]) + 1
        rep = tensor(rep)
        # Повтороение элементов линейного тензора, согласно ранее созданного тензора повторений.
        # Задаётся место под будущее размещение действий актора (пока тензор-вектор)
        critic_in = repeat_interleave(critic_in, rep, dim=1)
        # Увеличиваем нулевое измерение, дублируя каждую строку столько раз, сколько вариантов действий есть у актора
        # (разворачиваем тензор-вектор в тензор-матрицу).
        critic_in = repeat_interleave(critic_in, len(self.__action_var), dim=0)

        # Подготовка тензора индексов.
        # Стартовая позиция (по dim=1) действий актора во входном тензоре критика.
        st = actor_input.size(dim=1)
        # Индексный вектор
        action_index: List = [[st + i for i in range(len(self.__action_var[0]))]]
        index_tensor: Tensor = tensor(action_index, dtype=TENSOR_INDEX_DTYPE)
        # Превращение индексного вектора в индексную матрицу, путём копирования нулевой строки тензора.
        index_tensor = index_tensor.repeat(critic_in.size(dim=0), 1)

        # Подготовка тензора действий актора.
        # Создание заготовки тензора-вектора вариантов действий актора
        action_tensor: Tensor = tensor(self.__action_var, dtype=TENSOR_DTYPE)
        # Создание большого тензора вариантов действий путём размножения заготовки
        # (разворачивание тензора-вектора в тензор-матрицу путём копирования одной строки)
        action_tensor = tile(action_tensor, (actor_input.size(dim=0), 1))

        # Слияние целевого тензора и тензора действий.
        result: Tensor = critic_in.scatter_(1, index_tensor, action_tensor)

        return result

    # def action_variants(self) -> int:
    #     return len(self.__action_var)

    # def max_in_q_est(self, q_est_next: Tensor, s_order: List[TestId]) -> List[List[ZeroOne | int]]:
    # def max_in_q_est(self, q_est_next: Tensor, s_order: List[TestId]) -> Dict[TestId, List[ZeroOne | int]]:
    def max_in_q_est(self, q_est_next: Tensor, s_order: List[TestId]) -> Dict[TestId, Dict[Dict_key, Q_est_value | Index_value]]:
        """
        Элементами возвращаемого словаря являются словари из двух пар ключ-значение:
        значение максимальной оценки функции ценности,
        индекс данного максимального значения в списке ВСЕХ значений оценки функции ценности по данному испытанию.
        """
        # Клонирование тензора (используемый метод поиска максимального значения
        # не поддерживает автоматическое дифференцирование и отказывается работать
        # если градиент у одного из тензоров активирован)
        tensors: Tensor = q_est_next.clone().detach()
        # Преобразование общего тензора оценок ф-ции ценности (выход критика) в список тензоров.
        # Каждый тензор соответствует набору оценок функции ценности по одному испытанию из батча.
        tensors: List[Tensor] = split(tensors, len(self.__action_var), dim=0)

        # Результирующий список максимальных оценок фунции ценности.
        # max_q_est: List[List[ZeroOne | int]] = []
        # by_test_id: Dict[TestId, List[ZeroOne | int]] = {}
        by_test_id: Dict[TestId, Dict[Dict_key, Q_est_value | Index_value]] = {}
        # Выходной кортеж для функции поиска максимума в тензоре.
        max_from: Tuple[Tensor, Tensor] = (zeros(0), zeros(0, dtype=int64))
        # Обход списка тензоров
        for i, one_tensor in enumerate(tensors):
            # Нахождение максимума в тензоре.
            max(one_tensor, dim=0, out=max_from)
            # Пополнение списка результатов.
            # max_q_est.append([max_from[0].item(), max_from[1].item()])
            # Индекс испытания в списке тензоров и индекс испытания в списке идентификаторов испытаний совпадают
            # by_test_id[s_order[i]] = [max_from[0].item(), max_from[1].item()]
            by_test_id[s_order[i]] = {Q_EST_NEXT: max_from[0].item(), INDEX_IN_TEST: max_from[1].item()}

        # return max_q_est
        return by_test_id

    # def max_q_est(self, ):

    # todo добавить сигнатуру метода в родительский интерфейс.
    def choose_max_q_action(self, max_q_est: Dict[TestId, Dict[Dict_key, Q_est_value | Index_value]]) -> Dict[TestId, Tensor]:
        """ Выбор действия актора, отвечающего максимальной оценке функции ценности.

        :param max_q_est: словарь максимальных оценок функции ценности для всех испытаний.
        :return: Словарь вида: идентификатор испытания - тензор действия актора, максимальная оценка функции ценности.
        """

        # if len(max_q_est) != len(s_order):
        #     # Проверка на совпадение длин двух списков.
        #     raise ValueError("Length of first argument not equal length of second argument: {} != {}".
        #                      format(len(max_q_est), len(s_order)))

        result: Dict[TestId, Tensor] = {}
        # for i, test_id in enumerate(s_order):
        #     action_index = max_q_est[i][1]
        #     result[test_id] = tensor([self.__action_var[action_index]], dtype=TENSOR_DTYPE)

        for test_id, value in max_q_est.items():
            # action_index = value[1]
            action_index = value[INDEX_IN_TEST]
            # result[test_id] = tensor([self.__action_var[action_index]], dtype=TENSOR_DTYPE)
            result[test_id] = tensor([self.__action_var[action_index]], dtype=TENSOR_DTYPE)

        return result

    def correction(self, reinf: Dict[TestId, ZeroOne],
                   max_q_est: Dict[TestId, ZeroOne],
                   max_q_est_next: Dict[TestId, ZeroOne]) -> Dict[TestId, ZeroOne]:
        q_err: Dict[TestId, float] = {}
        for test_id, rf in reinf.items():
            # q_err[test_id] = ALPHA * (rf + GAMMA * max_q_est_next[test_id] - max_q_est[test_id])
            q_err[test_id] = rf + GAMMA * max_q_est_next[test_id][0] - max_q_est[test_id]

        return q_err