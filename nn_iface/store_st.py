""" Реализация состояния и его хранилища. """
from typing import Dict, Optional

# from torch import device as torch_device

from nn_iface.ifaces import InterfaceStorage, ProcessStateInterface, DictKey
from threading import Thread
from queue import Queue
from time import sleep
from basics import SLEEP_TIME
from nn_iface.storage import Storage


class StateStorage(Storage, Thread):
    # Класс записи состояния процесса тренировки в хранилище через дополнительную нить.
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
        """

        :return: Очередь для передачи сохраняемого словаря.
        """
        return self.__dict_queue

    @property
    def report_queue(self) -> Queue:
        """

        :return: Очередь для передачи подтверждения, что сохранение произведено.
        """
        return self.__report_queue


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

    # @property
    # def device(self) -> Optional[str]:
    #     return self.__proxy_dict[DictKey.DEVICE]
    #
    # @device.setter
    # def device(self, value: Optional[str]) -> None:
    #     self.__proxy_dict[DictKey.DEVICE]


