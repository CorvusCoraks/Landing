""" Модуль с общим классом хранилища через стандартные методы torch: save(), load(). """
from nn_iface.ifaces import InterfaceStorage
from typing import Dict
from torch import save, load


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
