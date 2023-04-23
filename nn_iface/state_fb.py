""" Фабрика выдачи различных хранилищ. """
# todo модуль-заготовка
from nn_iface.if_state import InterfaceStorage
from fl_store.store_nn import TorchFileStorage


def storage_fabrica(fabrica_type: str, name: str) -> InterfaceStorage:
    if fabrica_type == "sql_db":
        pass
    elif fabrica_type == "yaml":
        pass
    elif fabrica_type == "shelve":
        pass
    else:
        # Стандартное хранилище pytorch в *.pth-файл.
        # fabrica_type == "pth"
        return TorchFileStorage(name)