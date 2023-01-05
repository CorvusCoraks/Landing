""" Реализации интерфейсов nn_iface.py """
from typing import Union, Dict, Optional, Tuple
from torch.nn import Module, Conv2d
import torch
import torch.nn.functional as F
from thrds_tk.nn_iface import InterfaceStorage, InterfaceNeuronNet, InterfaceACCombo, ProcessStateInterface, DictKey


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class Storage(InterfaceStorage):
    """ *.pt хранилище """
    # Отдельный файл под структуру нейросети (так как она грузится один раз на запуске тренировки,
    # и один раз сохраняется на завершении тренировки). И критик, и актор: словарь с двумя элементами.
    # todo сохранять структуру нейросети на завершении тренировки не целесообразно
    # Отдельный файл под параметры, которые сохраняются после каждого батча (каждой оптимизации):
    # - гиперпараметры нейросети
    # - параметры оптимизатора
    # и т. п.
    def __init__(self, research_name: str):
        # Имя исследования
        self._research_name = research_name
        # Бланк концовки имени файла (будет испльзоваться в функции format)
        self._filename_ending = "{}.pt"
        # Имя файла-хранилища
        self._storage_filename = research_name + self._filename_ending

    def save(self, any_dict: Dict):
        if self._storage_filename.endswith(self._filename_ending):
            # Проверка допустимости имени файла.
            raise Exception("Don`t use class Storage directly.")
        # Словарь данных, которые временно выгружаются из хранилища.
        dict_from: Dict = {}

        try:
            # выгружаем ранее сохранённый словарь
            dict_from = self.load()
        except FileNotFoundError:
            # Если файл для сохранения был не обнаружен, то создаём его, сохраняя пустой словарь
            torch.save({}, self._storage_filename)

        # обновляем словарь (обновляем старые ключи и добавляем новые)
        dict_from.update(any_dict)
        # сохраняем обновлённый словарь
        torch.save(dict_from, self._storage_filename)

    def load(self) -> Dict:
        if self._storage_filename.endswith(self._filename_ending):
            # Проверка допустимости имени файла.
            raise Exception("Don`t use class Storage directly.")
        return torch.load(self._storage_filename)


class ModuleStorage(Storage):
    """ Хранилище структуры нейросетей (и актора, и критика). """
    def __init__(self, research_name: str):
        super().__init__(research_name)
        self._storage_filename = self._storage_filename.format("_nn")


class StateStorage(Storage):
    """ Хранилище состояния процесса обучения. """
    def __init__(self, research_name: str):
        super().__init__(research_name)
        self._storage_filename = self._storage_filename.format("_st")
        print(self._storage_filename)


class NeuronNet(InterfaceNeuronNet):
    def create(self) -> None:
        pass

    @property
    def nn(self) -> Module:
        return TestModel()

    def prepare_input(self) -> None:
        pass

    def proceccing_output(self) -> None:
        pass

    def forward(self) -> None:
        pass

    def backward(self) -> None:
        pass


class ActorAndCritic(InterfaceACCombo):
    @property
    def actor(self) -> Module:
        return TestModel()

    @property
    def critic(self) -> Module:
        return TestModel()

    def save(self, storage: InterfaceStorage) -> bool:
        pass

    def load(self, storage: InterfaceStorage) -> bool:
        pass


class State(ProcessStateInterface):
    def __init__(self):
        self.__batch_size: int = -1
        self.__epoch_start: int = 0
        self.__epoch_current: int = 0
        self.__epoch_stop: int = 0
        self.__prev_q_max: float = 0

    def save(self, storage: InterfaceStorage) -> None:
        dict_for_save = {DictKey.BATCH_SIZE: self.__batch_size,
                         DictKey.EPOCH: [self.__epoch_start, self.__epoch_current, self.__epoch_stop],
                         DictKey.PREV_Q_MAX: self.__prev_q_max}
        storage.save(dict_for_save)

    def load(self, storage: InterfaceStorage) -> None:
        state: Dict = storage.load()
        self.__batch_size = state[DictKey.BATCH_SIZE]
        self.__epoch_start, self.__epoch_current, self.__epoch_stop = state[DictKey.EPOCH]
        self.__prev_q_max = state[DictKey.PREV_Q_MAX]

    @property
    def batch_size(self) -> int:
        return self.__batch_size

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        self.__batch_size = value

    @property
    def epoch_start(self) -> int:
        return self.__epoch_stop

    @epoch_start.setter
    def epoch_start(self, value: int) -> None:
        self.__epoch_stop = value

    @property
    def epoch_current(self) -> int:
        return self.__epoch_current

    @epoch_current.setter
    def epoch_current(self, value: int) -> None:
        self.__epoch_current = value

    @property
    def epoch_stop(self) -> int:
        return self.__epoch_stop

    @epoch_stop.setter
    def epoch_stop(self, value: int) -> None:
        self.__epoch_stop = value


    @property
    def prev_q_max(self) -> float:
        return self.__prev_q_max

    @prev_q_max.setter
    def prev_q_max(self, value) -> None:
        self.__prev_q_max = value
