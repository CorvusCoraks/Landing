""" Реализация файлового хранилища состояния обучения. """
from typing import Dict
from threading import Thread
from queue import Queue
from time import sleep
from basics import SLEEP_TIME
from fl_store.pt_store import TorchFileStorage


class StateStorage(TorchFileStorage, Thread):
    """ Класс записи состояния процесса тренировки в хранилище через дополнительную нить. """
    def __init__(self, research_name: str):
        TorchFileStorage.__init__(self, research_name)
        Thread.__init__(self)
        # Нить-демон (чтобы автоматом завершилась по завершению приложения)
        self.daemon = True
        # Очередь с данными на сохранение
        self.__dict_queue: Queue[Dict] = Queue()
        # Очередь сообщений, подтверждающих, что произведено сохранение данных в хранилище.
        # Необходима для того, чтобы очередная порция данных отправлялась на сохранение только после записи предыдущей.
        self.__report_queue: Queue[bool] = Queue()

    def run(self) -> None:
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
                super().save(for_save)
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

    def save(self, any_dict: Dict):
        # super().save(any_dict)
        if not self.is_alive():
            # Если нить ещё не запущена
            # Запускаем её
            self.start()
            # И отправляем данные на сохранение.
            self.save_queue.put(any_dict)
        else:
            # Если нить уже запущена
            if not self.report_queue.empty():
                # И если есть сообщение, что завершено предыдущее сохранение
                # Забираем элемент из очереди репортов.
                self.report_queue.get()
                # Отправляем список состояния на сохранение.
                self.save_queue.put(any_dict)
            else:
                # А если репорта о завершении предыдущего сохранения ещё нет - ничего не сохраняем.
                # Пропускаем действие, чтобы не создавать очередь в очереди.
                pass
