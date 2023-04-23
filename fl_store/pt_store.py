""" Модуль с общим классом хранилища через стандартные методы torch: save(), load(). """
from nn_iface.if_state import InterfaceStorage
from typing import Dict
import torch


class TorchFileStorage(InterfaceStorage):
    """ *.pt хранилище """
    # Размышлизмы.
    # Отдельный файл под структуру нейросети (так как она грузится один раз на запуске тренировки,
    # и один раз сохраняется на завершении тренировки). И критик, и актор: словарь с двумя элементами.
    # todo сохранять структуру нейросети на завершении тренировки не целесообразно
    # Отдельный файл под параметры, которые сохраняются после каждого батча (каждой оптимизации):
    # - гиперпараметры нейросети
    # - параметры оптимизатора
    # и т. п.

    def __init__(self, file_name: str):
        # Имя файла-хранилища
        self._storage_filename = file_name

    def save(self, any_dict: Dict):
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
        return torch.load(self._storage_filename)
