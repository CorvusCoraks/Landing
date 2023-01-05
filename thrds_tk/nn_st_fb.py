""" Фабрика выдачи различных хранилищ. """
from thrds_tk.nn_iface import InterfaceStorage
from thrds_tk.nn_class import Storage

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