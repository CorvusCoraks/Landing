""" Реализации интерфейсов nn_iface.py """
from typing import Union, Dict, Optional, Tuple
from torch.nn import Module, Conv2d
from torch import device, save, load, cuda
import torch.nn.functional as F
from thrds_tk.nn_iface import InterfaceStorage, InterfaceNeuronNet, InterfaceACCombo, ProcessStateInterface, DictKey
from threading import Thread
from queue import Queue
from time import sleep
from basics import SLEEP_TIME


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
            save({}, self._storage_filename)

        # обновляем словарь (обновляем старые ключи и добавляем новые)
        dict_from.update(any_dict)
        # сохраняем обновлённый словарь
        save(dict_from, self._storage_filename)

    def load(self) -> Dict:
        if self._storage_filename.endswith(self._filename_ending):
            # Проверка допустимости имени файла.
            raise Exception("Don`t use class Storage directly.")
        return load(self._storage_filename)


class ModuleStorage(Storage):
    """ Хранилище структуры нейросетей (и актора, и критика). """
    def __init__(self, research_name: str):
        super().__init__(research_name)
        self._storage_filename = self._storage_filename.format("_nn")


class StateStorage(Storage, Thread):
    # Класс записи состояния в хранилище через дополнительную нить.
    def __init__(self, research_name: str):
        Storage.__init__(self, research_name)
        Thread.__init__(self)
        # Нить-демон (чтобы автоматом завершилась по завершению приложения)
        self.daemon = True
        # имя файла-хранилища
        self._storage_filename = self._storage_filename.format("_st")
        # print(self._storage_filename)
        # Очередь с данными на сохранение
        self.__dict_queue: Queue[Dict] = Queue()
        # Очередь сообщений, подтверждающих, что произведено сохранение данных в хранилище.
        # Необходима для того, чтобы очередная порция данных отправлялась на сохранение только после записи предыдущей.
        self.__report_queue: Queue[bool] = Queue()
        # self.__was_running: bool = False

    def run(self) -> None:
        # self.__was_running = True
        while True:
            if not self.__dict_queue.empty():
                # Если очередь с данными на сохранение не пуста.
                # То получаем данные.
                for_save: Dict = self.__dict_queue.get()
                if not isinstance(for_save, Dict):
                    # Проверка типа данных полученных из очереди.
                    raise TypeError(
                        "From queue received wrong type object: {0}. Queue only for Dict type objects."
                        .format(for_save.__class__))
                # Отправляем данные на сохранение.
                self.save(for_save)
                # Подтверждаем сохранение данных
                self.__report_queue.put(True)
            else:
                # Если данных на сохранение нет, засыпаем.
                sleep(SLEEP_TIME)

    @property
    def save_queue(self) -> Queue:
        return self.__dict_queue

    @property
    def report_queue(self) -> Queue:
        return self.__report_queue



# class SaveCommand:
#     def __init__(self, save_dict: Dict, storage: StateStorage):
#         self.dict: Dict = save_dict
#         self.storage: StateStorage = storage


# class SaveThread(Thread):
#     def __init__(self, queue: Queue):
#         # Демон, так как демон завершается (исполнение прерывается) с завершением породившей его нити.
#         super().__init__(daemon=True)
#         self.__queue: Queue = queue
#
#     def run(self) -> None:
#         while True:
#             if not self.__queue.empty():
#                 for_save: SaveCommand = self.__queue.get()
#                 if not isinstance(for_save, SaveCommand):
#                     raise TypeError("From queue received wrong type object: {0}. Queue only for SaveCommand type objects."
#                                     .format(for_save.__class__))
#                 for_save.storage.save(for_save.dict)
#             else:
#                 sleep(SLEEP_TIME)


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
        # Словарь с данными.
        self.__proxy_dict: Dict = {DictKey.BATCH_SIZE: -1,
                                   DictKey.EPOCH: [0, 0, 0],
                                   DictKey.PREV_Q_MAX: 0.,
                                   DictKey.TEMP_FOR_TEST: 0}

    def save(self, storage: InterfaceStorage) -> None:
        self.__proxy_dict[DictKey.TEMP_FOR_TEST] += 1
        # Полученный объект должен быть потомком класса-нити
        if not isinstance(storage, StateStorage):
            raise TypeError("Input argument is wrong class: {}. It should be a object of StateStorage class".
                            format(storage.__class__))

        if not storage.is_alive():
            # Если нить ещё не запущена
            # Запускаем её
            storage.start()
            # И отправляем данные на сохранение.
            storage.save_queue.put(self.__proxy_dict)
        else:
            # Если нить уже запущена
            if not storage.report_queue.empty():
                # И если есть сообщение, что завершено предыдущее сохранение
                # Забираем элемент из очереди репортов.
                storage.report_queue.get()
                # Отправляем список состояния на сохранение.
                storage.save_queue.put(self.__proxy_dict)
            else:
                # А если репорта о завершении предыдущего сохранения ещё нет - ничего не сохраняем.
                # Пропускаем действие, чтобы не создавать очередь в очереди.
                pass

    def load(self, storage: InterfaceStorage) -> None:
        # self.__dict_loaded = True
        self.__proxy_dict: Dict = storage.load()

    @property
    def batch_size(self) -> int:
        return self.__proxy_dict[DictKey.BATCH_SIZE]

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        self.__proxy_dict[DictKey.BATCH_SIZE] = value

    @property
    def epoch_start(self) -> int:
        return self.__proxy_dict[DictKey.EPOCH][0]

    @epoch_start.setter
    def epoch_start(self, value: int) -> None:
        self.__proxy_dict[DictKey.EPOCH][0] = value

    @property
    def epoch_current(self) -> int:
        return self.__proxy_dict[DictKey.EPOCH][1]

    @epoch_current.setter
    def epoch_current(self, value: int) -> None:
        self.__proxy_dict[DictKey.EPOCH][1] = value

    @property
    def epoch_stop(self) -> int:
        return self.__proxy_dict[DictKey.EPOCH][2]

    @epoch_stop.setter
    def epoch_stop(self, value: int) -> None:
        self.__proxy_dict[DictKey.EPOCH][2] = value


    @property
    def prev_q_max(self) -> float:
        return self.__proxy_dict[DictKey.PREV_Q_MAX]

    @prev_q_max.setter
    def prev_q_max(self, value) -> None:
        self.__proxy_dict[DictKey.PREV_Q_MAX] = value
