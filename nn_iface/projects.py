""" Конкретный проект (комбинация нейросетей). """
from torch import Tensor, cuda, tensor, float32
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from nn_iface.ifaces import ProjectInterface, InterfaceStorage, ProcessStateInterface
from nn_iface.store_nn import ModuleStorage
from nn_iface.store_st import StateStorage, State
from typing import Dict, Optional
from net import Net
from tools import Reinforcement, Finish
from basics import TestId, TENSOR_DTYPE
from structures import RealWorldStageStatusN


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


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

    def actor_input_preparation(self, batch: Dict[TestId, RealWorldStageStatusN]) -> Tensor:


        # childrens = self._actor.children()
        # children_0 = childrens.__next__()
        # children_0 = childrens.__next__()
        # params = children_0.parameters(recurse=True)
        # for param in params:
        #     print(param)
        # params_0 = params.__next__()
        # Список-заготовка входных данных
        input_list: list =[a for a in range(len(batch))]
        # Список-заготовка идентификаторов испытаний (Необходим в будущем для состыковки результатов с идентификаторами)
        test_id_list: list = [a for a in range(len(batch))]


        for index, (key, value) in enumerate(batch.items()):
            # Из словаря данных для батча извлекаем параметры состояний для каждого испытания.
            input_list[index] = [value.position.x, value.position.y,
                                 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
            test_id_list[index] = key

        # Входной тензор.
        input: Tensor = tensor(input_list, dtype=TENSOR_DTYPE, requires_grad=True)

        return input

    def critic_input_preparation(self) -> None:
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
            "Width of batch element mismatch of neuron net input feaches count."
        #
        ### Конец проверки.

        return self._actor.forward(actor_input)

    def critic_forward(self) -> Tensor:
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

    def load_nn(self) -> None:
        try:
            super().load_nn()
        except FileNotFoundError:
            # Создание нейросетей.
            #
            # Актор.
            # количество входов
            ac_input = 13
            # количество нейронов в скрытом слое
            ac_hidden = ac_input-5
            # количество выходов
            ac_output = 5
            # количество скрытых слоёв
            ac_layers = 1
            self._actor = Net(ac_input, ac_hidden, ac_output, ac_layers, True)
            #
            # Критик.
            # размерность ac_input уже включает в себя размерность входных данных плюс один вход на подкрепление
            # Но в данном случае, на вход критика уже подаётся подкрепление ставшее результатом данного шага, а не предыдущего.
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



