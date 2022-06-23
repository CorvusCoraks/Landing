""" Модуль загрузки и сохранения. """
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import shelve

class INeuroNetStorage(ABC):
    @abstractmethod
    def save_neuro_net(self, state: Dict[str, Any]):
        pass

    @abstractmethod
    def load_neuro_net(self) -> Dict[str, Any]:
        pass


class ITrainingStateStorage(ABC):
    @abstractmethod
    def save_training(self, state: Dict[str, Any]):
        pass

    @abstractmethod
    def load_training(self, default: Dict[str, Any]) -> Dict[str, Any]:
        pass


class NeuroNetShelve(INeuroNetStorage):
    """ Сохранение и загрузка состояния нейросети в процессе обучения через shelve. """
    def __init__(self):
        self.__shelve_file_name = 'shelve_nn'

    def save_neuro_net(self, state: Dict[str, Any]):
        with shelve.open(self.__shelve_file_name) as sh_file:
            keys = state.keys()
            for some_key in keys:
                sh_file[some_key] = state[some_key]

    def load_neuro_net(self) -> Dict[str, Any]:
        with shelve.open(self.__shelve_file_name) as sh_file:
            keys = sh_file.keys()
            result: dict

            for some_key in keys:
                result[some_key] = sh_file[some_key]

        return result

    def default(self):
        default_dict: Optional[Dict[str, Any]] = None
        return default_dict


class TrainingStateShelve(ITrainingStateStorage):
    """ Сохранение и загрузка состояния нейросети в процессе обучения через shelve. """
    def __init__(self):
        self.__shelve_file_name = 'sh_state'

    def save_training(self, state: Dict[str, Any]):
        with shelve.open(self.__shelve_file_name) as sh_file:
            keys = state.keys()
            for some_key in keys:
                sh_file[some_key] = state[some_key]

    def load_training(self, default: Dict[str, Any]) -> Dict[str, Any]:
        result: dict = {}
        with shelve.open(self.__shelve_file_name) as sh_file:
            keys = sh_file.keys()

            if len(keys) == 0:
                return default

            for some_key in keys:
                result[some_key] = sh_file[some_key]

        return result
