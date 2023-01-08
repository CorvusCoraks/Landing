""" Фабрика выдачи различных хранилищ. """
from nn_iface.ifaces import InterfaceStorage
from nn_iface.store_nn import Storage

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
        return Storage(name)