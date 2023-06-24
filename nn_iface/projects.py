""" Конкретный проект (комбинация нейросетей). """
from torch import Tensor, tensor, add, mul
import torch.nn
import torch.nn.functional as F
import torch.optim
from nn_iface.ifaces import ProjectInterface, LossCriticInterface, LossActorInterface
from nn_iface.if_state import InterfaceStorage, ProcessStateInterface
from typing import Dict, Optional, List
from tools import Reinforcement, Finish
from basics import TestId, ACTOR_CHAPTER, CRITIC_CHAPTER, ZeroOne
from abc import ABC


class TestModel(torch.nn.Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = torch.nn.Conv2d(1, 20, 5)
        self.conv2 = torch.nn.Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class MSE_RLLoss(LossCriticInterface, torch.nn.MSELoss):
    """ Класс функции потерь среднего квадратичного отклонения. """
    def __init__(self, gamma: float = 0.001, reduction: str = 'mean'):
        torch.nn.MSELoss.__init__(self, reduction)
        self._gamma = gamma

    def __call__(self, s_order: List[TestId], reinf: Dict[TestId, ZeroOne],
                 max_q_est: Dict[TestId, ZeroOne], max_q_est_next: Tensor) -> Tensor:

        # Список предыдущих максимальных оценок функции ценности
        q_est_input: List[List[ZeroOne]] = [[max_q_est[test_id]] for test_id in s_order]
        # Тензор предыдущих максимальных оценок функции ценности
        q_est_input: Tensor = tensor(q_est_input, requires_grad=False)

        # Список подкреплений
        rf: List[List[ZeroOne]] = [[reinf[test_id]] for test_id in s_order]
        # Тензор подкреплений
        rf: Tensor = tensor(rf, requires_grad=False)

        # Целевая оценка функции ценности.
        q_est_target: Tensor = add(rf, mul(max_q_est_next, self._gamma))

        return torch.nn.MSELoss.__call__(self, q_est_input, q_est_target)


class MSELoss(LossActorInterface, torch.nn.MSELoss):
    """ Просто MSE."""
    def __init__(self, reduction: str = 'mean'):
        torch.nn.MSELoss.__init__(self, reduction)

    def __call__(self, output: Tensor, target: Tensor):
        return torch.nn.MSELoss.__call__(self, output, target)


class AbstractProject(ProjectInterface, ABC):
    """ Абстрактный класс проекта. Объединяет общие атрибуты и реализации методов. """
    def __init__(self):
        self._actor_key = ACTOR_CHAPTER
        self._critic_key = CRITIC_CHAPTER

        self._actor: Optional[torch.nn.Module] = None
        self._critic: Optional[torch.nn.Module] = None

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

        # Оптимайзер актора
        self._actor_optimizer: Optional[torch.optim.Optimizer] = None
        # Оптимайзер критика
        self._critic_optimizer: Optional[torch.optim.Optimizer] = None

    @property
    def state(self) -> ProcessStateInterface:
        return self._training_state

    def save_nn(self) -> None:
        self._save_storage_model.save({self._actor_key: self._actor, self._critic_key: self._critic})

    def save_state(self) -> None:
        # фиксируем состояние оптимизатора актора в прокси-словаре
        self._training_state.actor_optim_state = self._actor_optimizer.state_dict()
        # фиксируем состояние оптимизатора критика в прокси-словаре
        self._training_state.critic_optim_state = self._critic_optimizer.state_dict()
        # сохраняем промежуточное состояние процесса обучения.
        self._training_state.save(self._save_storage_training_state)

    def del_previous_saved(self):
        self._save_storage_model.delete()
        self._save_storage_training_state.delete()
        self._save_storage_model_state.delete()

    def load_nn(self) -> None:
        actor_and_critic: Dict = self._load_storage_model.load()
        self._actor = actor_and_critic[self._actor_key]
        self._critic = actor_and_critic[self._critic_key]

    def load_state(self) -> None:
        # загружаем состояние из хранилища
        self._training_state.load(self._load_storage_training_state)
        # Восстанавливаем состояние оптимизатора актора
        self._actor_optimizer.load_state_dict(self._training_state.actor_optim_state)
        # Восстанавливаем состояние оптимизатора критика
        self._critic_optimizer.load_state_dict(self._training_state.critic_optim_state)

    @property
    def device(self) -> str:
        return self._device

    @property
    def reinforcement(self) -> Reinforcement:
        return self._reinforcement

    @property
    def finish(self) -> Finish:
        return self._finish

    def actor_target(self, s_order: List[TestId], commands: Dict[TestId, Tensor]) -> Tensor:
        list_for_tensor: List = [commands[test_id][0].tolist() for test_id in s_order]

        return tensor(list_for_tensor, requires_grad=False)

    def _features_examine(self, net_name: str, net_input: Tensor, net: torch.nn.Module) -> None:
        """ Проверка на совпадение количества входных параметров и размерности features нейронной сети.

        :param net_name: Имя (идентификатор проверяемой нейросети)
        :param net_input: Проверяемый входной тензор.
        :param net: Объект проверяемой нейросети.
        """
        # У входного тензора должно быть два измерения.
        if len(net_input.size()) != 2:
            raise ValueError("Input tensor dimensions count is wrong. Current count is {}, but should be 2."
                             .format(len(net_input.size())))
        ### Проверка на совпадение количества входных параметров, размерности features нейронной сети.
        #
        # Итератор по слоям актора.
        childrens_iter = net.children()
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
        assert second_children_parameters.shape[1] == net_input.shape[1], \
            "Width of raw_batch element ({}) mismatch of neuron net input features count ({})." \
            "May be you change neuron net input width in project, but load old neuron net from storage?".\
            format(second_children_parameters[1], net_input.shape[1])

        if second_children_parameters.shape[1] != net_input.shape[1]:
            raise ValueError("Width of raw_batch element ({}) mismatch of neuron net ({}) input features count ({}). "
                             "May be you change neuron net input width in project, "
                             "but load old neuron net from storage?".
                             format(second_children_parameters[1], net_name, net.net_input.shape[1]))

    def actor_forward(self, actor_input: Tensor) -> Tensor:
        self._features_examine('actor', actor_input, self._actor)
        return self._actor.forward(actor_input)

    def critic_forward(self, critic_input: Tensor) -> Tensor:
        self._features_examine('critic', critic_input, self._critic)
        return self._critic.forward(critic_input)

    @property
    def actor_optimizer(self) -> torch.optim.Optimizer:
        return self._actor_optimizer

    @property
    def critic_optimizer(self) -> torch.optim.Optimizer:
        return self._critic_optimizer
