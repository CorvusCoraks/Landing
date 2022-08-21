""" Композиция двунаправленной очереди из двух разнонаправленных простых очередей """
from queue import Queue
from typing import Optional, Type, Tuple, Any, Union, overload, Dict, List
# from atrolley import StatusData
from copy import deepcopy
from structures import T, ValueCopyInterface, ReinforcementValue, RealWorldStageStatusN, BatchSizeMessage, \
    MessageBase, NumT, NumR, StageControlCommands, TestId, QueueBlock
from carousel.trolleys import AnyTrolley, TrolleyA
# from carousel.atrolley import TestId, TrolleyAbstract
# from abc import ABC, abstractmethod
from kill_flags import KillInterface
from time import sleep
# Время сна между запросами о наличии блока данных в очереди, сек
SLEEP_TIME = 0.001

# QUEUE_ELEMENTS_TYPE: Tuple = (RealWorldStageStatusN, StageControlCommands, ReinforcementValue, MessageBase)

class CarouselB:
    """ Класс инкапсулирует двунаправленную очередь передачи данных в системе (двунаправленное движение вагонеток).
    Исключительно выгрузка вагонеток и погрузка вагонеток. """
    def __init__(self, trolley_quantity: int):
        # количество вагонеток в карусели
        self._trolley_quantity = trolley_quantity
        # очередь загруженных вагонеток в прямом направлении
        self._queue_loaded: Queue = Queue()
        # очередь пустых вагонеток в обратном направлении
        self._queue_unloaded: Queue = Queue()

        for i in range(trolley_quantity):
            self._queue_unloaded.put(TrolleyA())

    def add_trolley(self) -> None:
        """ Добавить в карусель ещё одну вагонетку """
        self._queue_unloaded.put(TrolleyA())
        self._trolley_quantity += 1

    def del_trolley(self) -> None:
        """ Удалить из карусели одну вагонетку """
        self._queue_unloaded.get()
        self._trolley_quantity -= 1

    @property
    def trolleys_quantity(self) -> int:
        """ Количество вагонеток в карусели """
        return self._trolley_quantity

    @property
    def has_new_cargo(self) -> bool:
        """ В очереди имеется полная вагонетка? """
        return not self._queue_loaded.empty()

    @property
    def has_void_trolley(self) -> bool:
        """ В очереди имеется пустая вагонетка? """
        return not self._queue_unloaded.empty()

    def unload(self) -> Any:
        """ Выгрузить вагонетку.

        :return: контейнер (объект-носитель) неизвестного типа """
        trolley: TrolleyA = self._queue_loaded.get()
        unknown_cargo: Any = trolley.unloading()
        self._queue_unloaded.put(trolley)
        return unknown_cargo

    def load(self, unknown_cargo: Any) -> None:
        """ Загрузить вагонетку.

        :param unknown_cargo: контейнер (объект-носитель) неизвестного типа
        """
        void_trolley: TrolleyA = self._queue_unloaded.get()
        void_trolley.loading(unknown_cargo)
        self._queue_loaded.put(void_trolley)


class VoidContaners:
    """ Объект данного класса содержит в себе пустые контейнеры (объекты-носители) для очередей. Объект-склад."""
    def __init__(self, *args):
        """
        :param args: Список объектов-прототипов блоков данных, внутри копий которых будут передаваться данные
        """
        # Словарь {тип прототипа: объект-прототип}
        self._contaners_prototypes: Dict[Type[QueueBlock], QueueBlock] = dict()
        # Словарь {тип прототипа: очередь хранящая пустые контейнеры (объекты-носители)}
        self._contaners_collection: Dict[Type[QueueBlock], Queue] = dict()
        # Количество периодов сна в ожидании пустого контейнера, _sleep_for_void * SLEEP_TYME = полное время сна
        self._sleep_counter: int = 10
        self._SLEEP_MAX = 10
        # self._stop_waiting: KillInterface = stop_waiting

        # Заполняем словари, на основании списка объектов-прототипов
        if len(args) != 0:
            for prototype in args:
                if isinstance(prototype, QueueBlock):
                    self._contaners_prototypes[type(prototype)] = prototype
                    self._contaners_collection[type(prototype)] = Queue()
                else:
                    raise TypeError('Element of "args" argument ({0}) is not a QueueBlock type.'
                                    .format(type(prototype)))
        else:
            raise ValueError('Argument "args" must have at least one element.')

    def get(self, contaner_type: Type[QueueBlock]) -> QueueBlock:
        """ Получить пустой объект-контейнер из хранилища. Цикл ожидания ограничен.

        :param contaner_type: тип желаемого контейнера
        """
        if not contaner_type in self._contaners_prototypes.keys():
            raise ValueError('Argument "contaner_type" ({0}) is not a present in keys of contaner collections.'
                             .format(contaner_type))

        if self._contaners_collection[contaner_type].empty():
            while self._sleep_counter > 0 and self._contaners_collection[contaner_type].empty():
                # ограничение по kill_flags не ставим, так как в любом случае через self._SLEEP_MAX цикл завершится
                sleep(SLEEP_TIME)
                self._sleep_counter -= 1
            else:
                self._sleep_counter = self._SLEEP_MAX
                return deepcopy(self._contaners_prototypes[contaner_type])
        else:
            return self._contaners_collection[contaner_type].get()

    def put(self, contaner: QueueBlock) -> None:
        """ Сдать пустой объект-контейнер на хранение.

        :param contaner: пустой объект-контейнер.
        """
        self._contaners_collection[type(contaner)].put(contaner)

class Porter:
    """ Класс производит выгрузку данных из объекта-носителя (контейнера) неизвестного типа.
    Объект-носитель (контейнер) после этого доступен для повторного использования в очереди. """
    def __init__(self, storage: VoidContaners):
        self._storage: VoidContaners = storage

    def cargo_type(self, unknown_cargo: QueueBlock):
        """ Метод необходим для внешнего модуля, для подготовки подходящего по типу приёмника.
        Только после этого вызывается метод *unloading()* """
        return type(unknown_cargo)

    @overload
    def unpack(self, unknown_cargo: QueueBlock) -> Tuple[TestId, NumT]:
        ...

    @overload
    def unpack(self, unknown_cargo: QueueBlock, to_object: ValueCopyInterface) -> Tuple[TestId, None]:
        ...

    def unpack(self, unknown_cargo: QueueBlock, to_object: Optional[ValueCopyInterface]=None) \
            -> Tuple[TestId, Optional[NumT]]:
        """ Распаковка неизвестного объекта из контейнера.

        :param unknown_cargo: Груз неизвестного типа.
        :param to_object: Если разгрузка производится через объект-аргумент метода.
        :return: Если разгрузка производится возвращаемым значением метода.
        """
        if to_object is not None:
            if isinstance(unknown_cargo, ValueCopyInterface) and isinstance(unknown_cargo, QueueBlock):
                # Если объект, куда нужно разгрузить груз присутствует.
                # if not isinstance(unknown_cargo, ValueCopyInterface):
                #     # У объекта груза нет интерфейса для данного метода разгрузки.
                #     raise TypeError('"{0}" argument do not have ValueCopyInterface.'.format(unknown_cargo))

                # if type(unknown_cargo) == type(to_object):
                if isinstance(unknown_cargo, type(to_object)):
                    # Неизвестный груз является объектом класса (или подкласса) целевого объекта: копируем атрибуты объектов
                    # Опусторшить контейнер.
                    unknown_cargo.data_copy(to_object)
                    # todo Подавить предупреждение, так как на входе в блок мы проверили объект на соответствие классам
                    test_id: TestId = unknown_cargo.test_id
                    # Отправить опустошённый контейнер в хранилище
                    # todo Подавить предупреждение, так как на входе в блок мы проверили объект на соответствие классам
                    self._storage.put(unknown_cargo)
                    return test_id, None
                else:
                    # Не соответствие типов груза и целевого объекта
                    raise TypeError('"{0}" argument and "{1}" argument types mismatch.'.format(unknown_cargo, to_object))
            else:
                # У объекта груза нет интерфейса для данного метода разгрузки.
                raise TypeError('"{0}" argument do not inheriting from ValueCopyInterface or QueueBlock.'.format(unknown_cargo))
        else:
            if isinstance(unknown_cargo, MessageBase):
                # Если груз относится к классу разгружаемых через возвращаемое значение.
                # Опустошить контейнер.
                test_id, value = unknown_cargo.test_id, unknown_cargo.value
                # Отправить опустошённый контейнер на хранение
                self._storage.put(unknown_cargo)
                return test_id, value
            else:
                raise TypeError('"{0}" is not a subclass of MessageBase.'.format(unknown_cargo))

    def pack(self, cargo: Union[ValueCopyInterface, NumT], contaner_type: Type[QueueBlock], test_id:Optional[TestId]) \
            -> Optional[QueueBlock]:
        """ Запаковка груза в контейнер (объект-носитель)

        :param cargo: некий груз
        :param contaner_type: подходящий тип контейнера для данного груза.
        :param test_id: идентификатор испытания
        :return: Объект-контейнер с упакованным в него грузом.
        """
        # Получить пустой контейнер для груза
        contaner = self._storage.get(contaner_type)

        if issubclass(contaner_type, MessageBase) and isinstance(cargo, NumR):
            # Если данные представляют собой простой тип
            contaner.value = cargo
            contaner.test_id = test_id
            return contaner
        elif isinstance(cargo, ValueCopyInterface):
            # Если объект данных сложен, то его загрузка производится через копирование атрибутов
            # if contaner_type == type(cargo):
            if issubclass(contaner_type, type(cargo)):
                # Если класс контейнера является дочерним для класса груза
                cargo.data_copy(contaner)
                contaner.test_id = test_id
                return contaner
        else:
            raise TypeError('Unknown pack method "{0}" class.'.format(contaner_type))

        return None


class PostOffice:
    """ Класс для взаимодействия с очередью передачи данных. """
    # Порядок вызова:
    # parsel_waiting - ждём блок данных из очереди
    # parsel_type - получаем тип блока данных, чтобы подготовить под него внешний пустой объект
    # receive_parsel - получить посылку.
    def __init__(self, carousel: CarouselB, porter: Porter, kill: KillInterface):
        self._carousel: CarouselB = carousel
        self._porter: Porter = porter
        self._temp_parsel: Optional[QueueBlock] = None
        self._stop_waiting: KillInterface = kill

    def parsel_waiting(self) -> bool:
        """ Дождаться посылки. Цикл ожидания ограничен флагом завершения нити.

        :param while_true: Флаг, означающий прерывание процесса ожидания данных из очереди.
        :return: Флаг дал команду прервать процесс ожидания?
        """
        while not self._stop_waiting.kill:
            if self._carousel.has_new_cargo:
                self._temp_parsel = self._carousel.unload()
                # Выход по получению посылки
                return False
            sleep(SLEEP_TIME)
        # Прерывание по флагу
        return True

    # def has_parsel(self) -> bool:
    #     """ В очереди имеются данные? """
    #     return self._carousel.has_new_cargo()

    @property
    def parsel_type(self) -> Optional[Type[QueueBlock]]:
        """ Получить тип посылки.

        :return: тип переданных данных
        """
        if self._temp_parsel:
            return self._porter.cargo_type(self._temp_parsel)
        else:
            # посылка ещё не выгружалась
            return None

    @overload
    def receive_parsel(self) -> Tuple[TestId, NumT]:
        ...

    @overload
    def receive_parsel(self, void_pack: ValueCopyInterface) -> Tuple[TestId, None]:
        ...

    def receive_parsel(self, void_pack: Optional[ValueCopyInterface]=None) -> Tuple[TestId, Optional[NumT]]:
        """ Получить данные из очереди.

        :param void_pack: пустая упаковка для данных из очереди.
        :return: Информация в виде простого значения, если не требуется копирование в *void_pack*
        """
        if self._temp_parsel is None:
            # Если данные из очереди ещё не добывались.
            raise Exception('"self._temp_parsel" is None. Prelimenary, please, wait the parsel using "parsel_waiting" method.')

        if void_pack is None:
            # Если заготовка под данные отсутствует, значит информацию передаём через возвращаемое значение.
            test_id, result = self._porter.unpack(self._temp_parsel)
            # Объект-носитель разгружен, очистить временный объект
            self._temp_parsel = None
            # Выдаём груз во вне.
            return test_id, result
        else:
            # Если заготовка под данные присутствует, информацию передаём во вне через неё.
            test_id, _ = self._porter.unpack(self._temp_parsel, void_pack)
            # Объект-носитель разгружен, очистить временный объект.
            self._temp_parsel = None
            return test_id, None

    def send_parsel(self, any_cargo: Union[ValueCopyInterface, NumT], package_type:Type[QueueBlock],
                    test_id:Optional[TestId]=None) -> None:
        """ Отправить данные в очередь.

        :param any_cargo: данные для отправки в очередь.
        :param test_id: Идентификатор испытания.
        :param package_type: тип упаковки для данных
        """
        # Упаковываем груз в подходящий контейнер
        package = self._porter.pack(any_cargo, package_type, test_id)

        # if package_type is None:
        #     # тип упаковки не указан, значит, контейнер имеет тот же тип, что и груз.
        #     package = self._porter.pack(any_cargo, pe(package_type), test_id)
        # else:
        #     # тип упаковки указан,
        #     package = self._porter.pack(any_cargo, package_type, test_id)

        # отправить упакованный груз в карусель получателю.
        self._carousel.load(package)


class Carousel:
    """ Класс инкапсулирует двунаправленную очередь передачи данных в системе (двунаправленное движение вагонеток)"""
    def __init__(self, cargo_prototype: T, trolley_quantity: int):
        """

        :param cargo_prototype: Объект-прототип груза
        :param trolley_quantity: Количество 'вагонеток' в карусели
        """
        # Объект-прототип груза
        self._cargo_prototype: T = cargo_prototype
        # очередь загруженных вагонеток в прямом направлении
        self._queue_loaded: Queue = Queue()
        # очередь пустых вагонеток в обратном направлении
        self._queue_unloaded: Queue = Queue()
        # объект-прототип вагонетки
        self._trolley_prototype: AnyTrolley = AnyTrolley(self._cargo_prototype)
        # количество вагонеток в Carousel
        self._trolley_quantity: int = 0
        # тип груза
        # self.__cargo_class: Type = type(trolley_prototype._cargo)

        for value in range(trolley_quantity):
            self.add_trolley()

    def add_trolley(self) -> None:
        """ Добавить в карусель ещё одну вагонетку """
        self._queue_unloaded.put(deepcopy(self._trolley_prototype))
        self._trolley_quantity += 1

    def del_trolley(self) -> None:
        """ Удалить из карусели одну вагонетку """
        self._queue_unloaded.get()
        self._trolley_quantity -= 1

    @property
    def trolleys_quantity(self) -> int:
        """ Количество вагонеток в карусели """
        return self._trolley_quantity

    def has_new_cargo(self) -> bool:
        """ В очереди имеется полная вагонетка? """
        return not self._queue_loaded.empty()

    def has_void_trolley(self) -> bool:
        """ В очереди имеется пустая вагонетка? """
        return not self._queue_unloaded.empty()

    def unload(self, to_object: T) -> Tuple[TestId, bool]:
        """ Разгрузить вагонетку

        :param to_object: Копировать состояние атрибутов в объект *to_object*
        :return: test_id, is_initial - идентификатор испытания, состояние начальное для нового теста? """
        if type(to_object) is not type(self._cargo_prototype):
            # Если тип целевого объекта не соответствует типу груза в вагонетке
            raise TypeError('Method argument type mismatch: expected {0}, but {1}'.
                            format(type(self._cargo_prototype), type(to_object)))

        trolley: AnyTrolley = self._queue_loaded.get()
        test_id, is_initial = trolley.unload(to_object)
        self._queue_unloaded.put(trolley)
        return test_id, is_initial

    def load(self, test_id: TestId, from_object: T, initial=False) -> None:
        """ Загрузить вагонетку

        :param test_id: Идентификатор теста
        :param from_object: копировать состояние артибутов из объекта *from_object*
        :param initial: это начальное состояние нового испытания?
        """
        if type(from_object) is not type(self._cargo_prototype):
            # Если тип объекта-источника не соответствует типу груза в вагонетке
            raise TypeError('Method argument type mismatch: expected {0}, but {1}'.
                            format(type(self._cargo_prototype), type(from_object)))

        trolley: AnyTrolley = self._queue_unloaded.get()
        trolley.load(test_id, from_object, initial)
        self._queue_loaded.put(trolley)


if __name__ == '__main__':
    channal = CarouselB(3)
    store = VoidContaners(RealWorldStageStatusN, StageControlCommands, BatchSizeMessage)
    porter = Porter(store)
    post_office = PostOffice(channal, porter)
    # channal = CarouselB(3, porter)