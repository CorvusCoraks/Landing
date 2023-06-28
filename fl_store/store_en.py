""" Реализация хранилища состояния окружающей среды. """

from fl_store.pt_store import TorchFileStorage


class EnvironmentStateStorage(TorchFileStorage):
    """ Хранилище состояния окружающей среды. """
    def __init__(self, file_name: str):
        super().__init__(file_name)
        self._storage_filename = file_name
