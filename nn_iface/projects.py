""" Конкретный проект (комбинация нейросетей). """
from torch import Tensor, cuda, tensor, float32
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from nn_iface.ifaces import ProjectInterface, InterfaceStorage, ProcessStateInterface
from nn_iface.store_nn import ModuleStorage
from nn_iface.store_st import StateStorage, State
from typing import Dict, Optional, List
from net import Net
from tools import Reinforcement, Finish
from basics import TestId, TENSOR_DTYPE, GRAVITY_ACCELERATION_ABS
from structures import RealWorldStageStatusN
from math import atan, atan2
from nn_iface.norm import NormalizationInterface, OneValueNormalisationInterface, MinMaxNormalization, MinMaxVectorComplex, ListMinMaxNormalization, MinMax, MinMaxXY
from math import pi
from point import VectorComplex


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


# class Norm(NormalizationInterface):
#     def __init__(self, distanse: MinMaxXY, velocity: MinMaxXY, acceleration: MinMaxXY,
#                  ang_velocity: MinMax, ang_acceleration: MinMax, time_stamp: MinMax):
#         self.__distanse: OneValueNormalisationInterface = MinMaxVectorComplex(distanse)
#         self.__velocity: OneValueNormalisationInterface = MinMaxVectorComplex(velocity)
#         self.__acceleraton: OneValueNormalisationInterface = MinMaxVectorComplex(acceleration)
#         self.__orientation: OneValueNormalisationInterface = MinMaxNormalization(MinMax(-pi, pi))
#         self.__ang_velocity: OneValueNormalisationInterface = MinMaxNormalization(ang_velocity)
#         self.__ang_acceleration: OneValueNormalisationInterface = MinMaxNormalization(ang_acceleration)
#         self.__timestamp: OneValueNormalisationInterface = MinMaxNormalization(time_stamp)
#
#     def normalization(self, denormalized: List[float]) -> List[float]:
#         normalized: List = [self.__distanse.norm(denormalized[0]), self.__distanse.norm(denormalized[1]),
#                             self.__velocity.norm(denormalized[2]), self.__velocity.norm(denormalized[3]),
#                             self.__acceleraton.norm(denormalized[4]), self.__acceleraton.norm(denormalized[5]),
#                             self.__orientation.norm(denormalized[6]),
#                             self.__ang_velocity.norm(denormalized[7]),
#                             self.__ang_acceleration.norm(denormalized[8]),
#                             self.__timestamp.norm(denormalized[9])]
#         return normalized


class AbstractProject(ProjectInterface):
    """ Абстрактный класс проекта. Объединяет общие атрибуты и реализации методов. """
    def __init__(self):
        self._actor_key = "actor"
        self._critic_key = "critic"

        self._actor: Optional[Module] = None
        self._critic: Optional[Module] = None

        self._training_state: Optional[ProcessStateInterface] = None

        # Хранилища для модуля НС
        self._load_storage_model: Optional[InterfaceStorage] = None
        self._save_storage_model: Optional[InterfaceStorage] = None
        # Хранилище для состояния процесса обучения.
        self._load_storage_training_state: Optional[InterfaceStorage] = None
        self._save_storage_training_state: Optional[InterfaceStorage] = None
        # Хранилище для состояния НС
        self._load_storage_model_state: Optional[InterfaceStorage] = None
        self._save_storage_model_state: Optional[InterfaceStorage] = None

        self._device: str = "cpu"

        # Подкрепление.
        self._reinforcement: Optional[Reinforcement] = None

        # Класс проверки на выход за пределы тестового полигона
        self._finish: Optional[Finish] = None

    @property
    def state(self) -> ProcessStateInterface:
        return self._training_state

    def save_nn(self) -> None:
        self._save_storage_model.save({self._actor_key: self._actor, self._critic_key: self._critic})

    def save_state(self) -> None:
        self._training_state.save(self._save_storage_training_state)

    def load_nn(self) -> None:
        actor_and_critic: Dict = self._load_storage_model.load()
        self._actor = actor_and_critic[self._actor_key]
        self._critic = actor_and_critic[self._critic_key]

    def load_state(self) -> None:
        # загружаем состояние из хранилища
        self._training_state.load(self._load_storage_training_state)

    @property
    def device(self) -> str:
        return self._device

    @property
    def reinforcement(self) -> Reinforcement:
        return self._reinforcement

    @property
    def finish(self) -> Finish:
        return self._finish

    def critic_input_preparation(self, actor_output: Tensor, environment_batch: Dict[TestId, RealWorldStageStatusN]) -> Tensor:
        pass

    def actor_loss(self) -> Tensor:
        pass

    def critic_loss(self) -> Tensor:
        pass

    def actor_optimizer(self) -> None:
        pass

    def critic_optimaizer(self) -> None:
        pass

    def actor_forward(self, actor_input: Tensor) -> Tensor:
        ### Проверка на совпадение количества входных параметров, размерности feaches нейронной сети.
        #
        # Итератор по слоям актора.
        childrens_iter = self._actor.children()
        # Первый слой - слой входных нейронов.
        first_children = childrens_iter.__next__()
        # Второй слой - линейный слой. По нему считаем количество и входных нейронов.
        second_children = childrens_iter.__next__()
        # Итератор по параметрам второго, линейного слоя.
        second_children_parameters_iter = second_children.parameters(recurse=True)
        # Параметры второго, линейного слоя.
        second_children_parameters = second_children_parameters_iter.__next__()
        # Число входных параметров должно соответствовать числу входных нейронов.
        # shape по тензору: [число подтензоров (элементов батча), количество feaches в элементе батча]
        # shape по параметрам: [число нейронов скрытого слоя, число входных нейронов]
        assert second_children_parameters.shape[1] == actor_input.shape[1], \
            "Width of raw_batch element ({}) mismatch of neuron net input feaches count ({})." \
            "May be you change neuron net input width in project, but load old neuron net from storage?".\
                format(second_children_parameters[1], actor_input.shape[1])
        #
        ### Конец проверки.

        return self._actor.forward(actor_input)
        # return actor_input

    def critic_forward(self, critic_input: Tensor) -> Tensor:
        pass


class DevelopmentTempProject(AbstractProject):
    """ Конкретный проект испытываемой системы управления. Конкретизирующие настроечные параметры тут. """
    def __init__(self):
        super().__init__()
        self.__model_name: str = "first"

        # Хранилища для модуля НС
        self._load_storage_model = ModuleStorage(self.__model_name)
        self._save_storage_model = self._load_storage_model
        # Хранилище для состояния процесса обучения.
        self._load_storage_training_state = StateStorage(self.__model_name)
        self._save_storage_training_state = self._load_storage_training_state
        # Хранилище для состояния НС
        self._load_storage_model_state = self._load_storage_training_state
        self._save_storage_model_state = self._load_storage_training_state

        self._training_state = State()

        # В хранилище состояния процесса сохраняться не будет.
        self._device = "cuda:0" if cuda.is_available() else "cpu"

        self._reinforcement = Reinforcement()

        self._finish = Finish()

        # self.__normaliaztion: NormalizationInterface = Norm([0., 100.], [0., 1000.], [])
        self.__normaliaztion: ListMinMaxNormalization = ListMinMaxNormalization([
            MinMaxXY(MinMax(-100., 100.), MinMax(-10., 500.)),  # дистанция
            MinMaxXY(MinMax(-100., 100.), MinMax(-100., 100.)), # линейная скорость
            MinMaxXY(MinMax(-10 * GRAVITY_ACCELERATION_ABS, 10 * GRAVITY_ACCELERATION_ABS),
                     MinMax(-10 * GRAVITY_ACCELERATION_ABS, 10 * GRAVITY_ACCELERATION_ABS)),    # лин. ускорение
            MinMax(-pi, +pi),   # ориентация (угол от вертикали в СКИП)
            MinMax(-pi/18, +pi/18),   # угловая скорость
            MinMax(-pi/180, +pi/180)])   # угловое ускорение
            # MinMax(0, 6000)])   # time_stamp

    def load_nn(self) -> None:
        try:
            super().load_nn()
        except FileNotFoundError:
            # Создание нейросетей.
            #
            # Актор.
            # количество входов
            ac_input = 9
            # количество нейронов в скрытом слое
            ac_hidden = ac_input
            # количество выходов
            ac_output = 5
            # количество скрытых слоёв
            ac_layers = 1
            self._actor = Net(ac_input, ac_hidden, ac_output, ac_layers, True)
            #
            # Критик.
            # размерность ac_input уже включает в себя размерность входных данных плюс один вход на подкрепление
            # Но в данном случае, на вход критика уже подаётся подкрепление ставшее результатом данного шага,
            # а не предыдущего.
            # вход критика = выход актора + вход актора
            cr_input = ac_output + ac_input
            cr_hidden = cr_input
            cr_output = 1
            cr_layers = 1
            self._critic = Net(cr_input, cr_hidden, cr_output, cr_layers, True)

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

    def actor_input_preparation(self, raw_batch: Dict[TestId, RealWorldStageStatusN]) -> Tensor:
        # Список-заготовка входных данных, список списков, элемент которого является состоянием изделия.
        rare_list: List[List[Optional[float]]] =[[] for a in range(len(raw_batch))]
        # Список-заготовка идентификаторов испытаний (Необходим в будущем для состыковки результатов с идентификаторами)
        test_id_list: List[TestId] = [0 for a in range(len(raw_batch))]

        for index, (key, value) in enumerate(raw_batch.items()):
            # Из словаря данных для батча извлекаем параметры состояний для каждого испытания.

            # Ориентация изделия (угол отклонения в радианах от оси OY в СКЦМ)
            orientation_rad: float = 0 if value.orientation.x == 0 else atan2(-value.orientation.x, value.orientation.y)

            # Проверка знака угла для правой и левой координатной полуплоскости
            # В правой полуплоскости знак угла отрицательный, в левой - положительный (отсчёт от оси OY СКЦМ)
            assert (value.orientation.x > 0 and orientation_rad < 0) \
                   or (value.orientation.x < 0 and orientation_rad > 0) \
                   or (value.orientation.x == 0 and orientation_rad == 0), \
                "Signs mismatch for angle and vector orientation"

            rare_list[index] = self.__normaliaztion.normalization([value.position, value.velocity, value.acceleration,
                                                             orientation_rad,
                                                             value.angular_velocity, value.angular_acceleration])

            test_id_list[index] = key

            rare_float_list: List[float] = []
            for i, state_element in enumerate(rare_list[index]):
                if isinstance(state_element, VectorComplex):
                    rare_float_list.extend([state_element.x, state_element.y])
                elif isinstance(state_element, float):
                    rare_float_list.append(state_element)
                else:
                    raise TypeError('Wrong type object {} in list'.format(type(state_element)))
                # rare_float_list



        # Входной тензор.
        input: Tensor = tensor([rare_float_list], dtype=TENSOR_DTYPE, requires_grad=True)

        return input
