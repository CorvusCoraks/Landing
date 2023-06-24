""" Модуль конкретного проекта. """
from types import ModuleType
import importlib
from torch import Tensor, cuda, tensor, zeros, repeat_interleave, tile, split, max, int64, sum, matmul, transpose
from torch.nn import Module, Sequential
import torch.optim
from fl_store.store_nn import ModuleStorage
from state import State
from fl_store.store_st import StateStorage
from typing import Dict, Optional, List, Tuple
from net import NetSeq
from tools import Reinforcement, Finish, action_variants, zo
from basics import TestId, TENSOR_DTYPE, TENSOR_INDEX_DTYPE, CUDA0, CPU, ZeroOne, Bit
from structures import RealWorldStageStatusN
from math import atan2
from nn_iface.norm import ListMinMaxNormalization
from nn_iface.ifaces import LossCriticInterface, LossActorInterface
from point import VectorComplex
from nn_iface.projects import AbstractProject
from app_cfg import PROJECT_DIRECTORY_PATH, PROJECT_DIRECTORY_NAME, PROJECT_CONFIG_NAME
from DevTmpPr.cfg import ACTOR_INPUT, ACTOR_HIDDEN, ACTOR_OUTPUT, ACTOR_OPTIONS
from DevTmpPr.cfg import CRITIC_INPUT, CRITIC_HIDDEN, CRITIC_OUTPUT, CRITIC_OPTIONS
from DevTmpPr.cfg import POSITION_MINMAX, LINE_VELOCITY_MINMAX, LINE_ACCELERATION_MINMAX
from DevTmpPr.cfg import ORIENTATION_MINMAX, ANGULAR_VELOCITY_MINMAX, ANGULAR_ACCELERATION_MINMAX
from DevTmpPr.cfg import NN_STORAGE_FILENAME, STATE_STORAGE_FILENAME
from DevTmpPr.cfg import JETS_COUNT
from DevTmpPr.cfg import CRITIC_LOSS, ACTOR_LOSS
from DevTmpPr.cfg import ACTOR_OPTIMIZER, ACTOR_OPTIMIZER_LR, ACTOR_OPTIMIZER_MOMENTUM
from DevTmpPr.cfg import CRITIC_OPTIMIZER, CRITIC_OPTIMIZER_LR, CRITIC_OPTIMIZER_MOMENTUM
from DevTmpPr.cfg import START_VALUES


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

        # Модуль конфигурации проекта.
        # self.__cfg: ModuleType = importlib.import_module('{}.{}'.format(PROJECT_DIRECTORY_NAME, PROJECT_CONFIG_NAME))

        # Список возможных действий актора.
        self.__action_var: List[List[Bit]] = action_variants(JETS_COUNT)

    def _create_optimizers(self, actor: Module, critic:Module) -> tuple[torch.optim.Optimizer, torch.optim.Optimizer]:
        """ Подпрограмма создания оптимизаторов. """
        actor_optimizer = ACTOR_OPTIMIZER(actor.parameters(), lr=ACTOR_OPTIMIZER_LR,
                                          momentum=ACTOR_OPTIMIZER_MOMENTUM)
        critic_optimizer = CRITIC_OPTIMIZER(critic.parameters(), lr=CRITIC_OPTIMIZER_LR,
                                            momentum=CRITIC_OPTIMIZER_MOMENTUM)

        return actor_optimizer, critic_optimizer

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
        # Если актор или критик ещё None, то создать оптимизаторы не получится.
        foo = None
        if self._actor is None or self._critic is None:
            raise ValueError("{} Could`t create optimizers. ".format(
                "Actor is None." if self._actor is None else "Critic is None." if self._critic is None else foo
            ))

        # Создание оптимизаторов
        self._actor_optimizer, self._critic_optimizer = self._create_optimizers(self._actor, self._critic)

        try:
            # # загружаем состояние из хранилища
            super().load_state()
        except FileNotFoundError:
            # Задание начальных состояний для параметров испытаний.
            self._training_state.batch_size = START_VALUES['batch_size']
            self._training_state.epoch_start = START_VALUES['epoch_start']
            self._training_state.epoch_current = START_VALUES['epoch_current']
            self._training_state.epoch_stop = START_VALUES['epoch_stop']
            # self._training_state.prev_q_max = 0

    def actor_input_preparation(self, raw_batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:

        # Список-заготовка (rare steak, стейк с кровью) входных данных, список списков,
        # элемент которого является состоянием изделия.
        rare_list: List[List[Optional[ZeroOne]]] = [[] for _ in range(len(raw_batch))]

        # Список, который пойдёт в конструктор тензора.
        rare_float_list: List[List[float]] = []

        for index, test_id in enumerate(s_order):
            # Из списка идентификаторов тестов по очерёдно извлекаем индексы и идентификаторы.

            # Ориентация изделия (угол отклонения в радианах от оси OY в СКЦМ)
            orientation_rad: float = 0 if raw_batch[test_id].orientation.x == 0 \
                else atan2(-raw_batch[test_id].orientation.x, raw_batch[test_id].orientation.y)

            # Проверка знака угла для правой и левой координатной полуплоскости
            # В правой полуплоскости знак угла отрицательный, в левой - положительный (отсчёт от оси OY СКЦМ)
            assert (raw_batch[test_id].orientation.x > 0 and orientation_rad < 0) \
                   or (raw_batch[test_id].orientation.x < 0 and orientation_rad > 0) \
                   or (raw_batch[test_id].orientation.x == 0 and orientation_rad == 0),\
                "Signs mismatch for angle and vector orientation"

            # Нормализация входных данных. VectorComplex возвращается как VectorComplex.
            rare_list[index] = self.__normaliaztion.normalization([raw_batch[test_id].position,
                                                                   raw_batch[test_id].velocity,
                                                                   raw_batch[test_id].acceleration,
                                                                   orientation_rad,
                                                                   raw_batch[test_id].angular_velocity,
                                                                   raw_batch[test_id].angular_acceleration])

            # Заполнение итогового списка (будет состоять из float)
            # Одно состояние
            state: list = []
            for i, state_element in enumerate(rare_list[index]):
                if isinstance(state_element, VectorComplex):
                    # Преобразование объектов VectorComplex в пары нормализованных float.
                    # rare_float_list.extend([zo(state_element.x), zo(state_element.y)])
                    state.extend([zo(state_element.x), zo(state_element.y)])
                elif isinstance(state_element, float):
                    # Если нормализованная величина уже float, включаем как float
                    # rare_float_list.append(zo(state_element))
                    state.append(zo(state_element))
                else:
                    raise TypeError('Wrong type object {} in list'.format(type(state_element)))
            # Добавка одного состояния в двумерный список будущего батча
            rare_float_list.append(state)

        # Входной тензор.
        input_tensor: Tensor = tensor(rare_float_list, dtype=TENSOR_DTYPE, requires_grad=True)

        return input_tensor

    def critic_input_preparation(self, actor_input: Tensor, actor_output: Tensor,
                                 environment_batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:

        # Подготовка целевого тезнора.
        # Клонируем вход актора,
        critic_in = actor_input.clone()
        # затем расширяем первое измерение клона на размер первого измерения списка возможных действий актора
        # Список повторений каждого элемента по горизонтали.
        # Все элементы повторяются 1 раз, ...
        rep = [1 for _ in critic_in[0]]
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

    def max_in_q_est(self, q_est_next: Tensor, s_order: List[TestId]) -> Dict[TestId, int]:
        # Клонирование тензора (используемый метод ``tensor.max()`` [источник?] поиска максимального значения
        # не поддерживает автоматическое дифференцирование и отказывается работать
        # если градиент у одного из тензоров активирован)
        tensors: Tensor = q_est_next.clone().detach()
        # Преобразование общего тензора оценок ф-ции ценности (выход критика) в список тензоров.
        # Каждый тензор соответствует набору оценок функции ценности по одному испытанию из батча.
        tensors: List[Tensor] = split(tensors, len(self.__action_var), dim=0)

        # Результирующий список максимальных оценок фунции ценности.
        result: Dict[TestId, int] = {}
        # Выходной кортеж для функции поиска максимума в тензоре.
        max_from: Tuple[Tensor, Tensor] = (zeros(0), zeros(0, dtype=int64))
        # Обход списка тензоров
        for i, one_tensor in enumerate(tensors):
            # Нахождение максимума в тензоре.
            max(one_tensor, dim=0, out=max_from)
            # Пополнение словаря результатов.
            result[s_order[i]] = max_from[1].item()

        return result

    def critic_output_transformation(self, all_q_est: Tensor, s_order: List[TestId],
                                     max_q_est_index: Dict[TestId, int]) -> Tensor:

        # По ключевым точкам проверено: grad_fn - present, requires_grad == True

        # Преобразуем двумерную матрицу выхода критика в двумерную матрицу,
        # где одна строка содержит оценки функции ценности всех вариантов действий в данном состоянии данного испытания.
        matrix_view = all_q_est.view((len(s_order), len(self.__action_var)))
        # grad_fn - present, requires_grad == True

        # Создание аналогичного по размеру тензора, где все элементы - нули.
        # + транспонирование его в вертикальный "вектор/матрицу" (подготовка к процедуре умножения)
        ones: Tensor = transpose(zeros(matrix_view.size(), requires_grad=False), dim0=0, dim1=1)
        # В позициях максимальных оценок устанавливаются единицы.
        for test_id in s_order:
            ones[max_q_est_index[test_id]][0] = 1

        # Перемножение двух матриц, в результате, все элементы обнуляются,
        # кроме элементов содержащих максимальные оценки функции ценности для данного испытания
        matrix_view = matmul(matrix_view, ones)
        # grad_fn - present, requires_grad == True

        # Сложить элементы в каждой строке. Получится тензор, где размер измерения 0 - количество испытаний в батче,
        # а измерение 1 содержит МАКСИМАЛЬНУЮ оценку функции ценности для данного конкретного испытания в батче.
        matrix_view = sum(matrix_view, 1, keepdim=True)
        # grad_fn - present, requires_grad == True

        return matrix_view

    def choose_max_q_action(self, s_order: List[TestId], max_q_index: Dict[TestId, int]) -> \
            Dict[TestId, Tensor]:

        result: Dict[TestId, Tensor] = {}

        for test_id in s_order:
            result[test_id] = tensor([self.__action_var[max_q_index[test_id]]], dtype=TENSOR_DTYPE)

        return result

    @property
    def actor_loss(self) -> LossActorInterface:
        return ACTOR_LOSS()

    @property
    def critic_loss(self) -> LossCriticInterface:
        return CRITIC_LOSS()


if __name__ == '__main__':
    pass
    # ProjectMainClass.transform(tensor([[0], [1], [2], [3], [4], [5], [6], [7], [8], [9]]), {0: 1})
