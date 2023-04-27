""" Модуль с общим классом хранилища через стандартные методы torch: save(), load(). """
from nn_iface.if_state import InterfaceStorage
from typing import Dict
import torch
from basics import FinishAppException


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
        # Возможно несоответствие сериализованных в хранилище объектов и объектов в программе.
        # Может выпадать ошибка вида "not valid key". Такое возможно, если программист изменил структуру данных
        # в программе, а при очередном запуске попытался загрузить старую структуру их хранилища.
        # todo В будущем предусмотреть легальное прекращение работы приложения с выдачей ясного пояснения по ошибке
        # То есть, нужна генерация FinishAppException и перехват его где-то в вызывающих методах, с передачей
        # команды DataTypeEnum.APP_FINISH на легитимное завершение всех потоков приложения.
        #
        result: dict = {}
        try:
            result: dict = torch.load(self._storage_filename)
        except ValueError as e:
            print("Attention! Возможно класс данных изменён в приложении, "
                  "но совершается попытка загрузки из хранилища устарелого объекта.")
            # raise FinishAppException
            raise
        else:
            return result
        # return torch.load(self._storage_filename)
