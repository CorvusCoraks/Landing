from point import VectorComplex
from math import fabs
from stage import Sizes, BigMap
from structures import RealWorldStageStatusN, StageControlCommands, ReinforcementValue, CloneFactory
from queue import Queue
from typing import TypeVar, Dict, Optional, AnyStr, List, Union, Iterable
from enum import Enum
from math import pi
from abc import ABC,abstractmethod

# Переменная типа (чтобы это не значило): классы объектов данных, которые передаются через очереди
QueueMembers = TypeVar('QueueMembers', RealWorldStageStatusN, StageControlCommands, ReinforcementValue)


class InitialStatusAbstract(ABC, Iterable):
    def __init__(self, max_count):
        self._current_status_index: int = -1
        self._max_status_index: int = max_count - 1
        self._is_empty: bool = False

    @abstractmethod
    def __iter__(self):
        pass

    # def iter(self):

    @abstractmethod
    def __next__(self):
        pass

    @property
    def is_empty(self) -> bool:
        return self._is_empty


class InitialStatus(InitialStatusAbstract):
    def __init__(self, max_count: int):
        InitialStatusAbstract.__init__(self, max_count)

    def __iter__(self):
        self._current_status_index = -1
        self._is_empty = False
        return self

    def __next__(self) -> Optional[RealWorldStageStatusN]:
        self._current_status_index += 1
        if self._is_empty:
            # Когда закончились начальные состояния, метод начинает возвращать *None*
            return None
        else:
            if self._current_status_index == self._max_status_index:
                # Последний элемент, последовательность пуста.
                self._is_empty = True

            return RealWorldStageStatusN(position=BigMap.startPointInPoligonCoordinates,
                                     orientation=VectorComplex.get_instance(0., 1.),
                                     velocity=VectorComplex.get_instance(0., -5.),
                                     angular_velocity=-pi / 36)


class SingleQueue:
    """ Одиночная очередь. Очередь может содеражть только объекты ОДНОГО типа. """
    def __init__(self, name: str, content_type: QueueMembers):
        """

        :param name: имя очереди
        :param content_type: тип элементов, которыми заполняется очередь
        """
        # инкапсулированная очередь
        self.__queue: Queue[QueueMembers] = Queue()
        # тип элементов, содежащихся в очереди
        self.__q_type: type = content_type
        # имя очереди
        self.__name: str = name

    def put(self, value: QueueMembers) -> None:
        """ Поместить объект в очередь """
        if isinstance(value, self.__q_type):
            self.__queue.put(value)
        else:
            raise ValueError('SingleQueue: argument value = {0} is not valid type. Expected: {1}'
                             .format(value, self.__q_type))

    def get(self) -> QueueMembers:
        """ Извлечь объект из очереди """
        return self.__queue.get()

    def empty(self) -> bool:
        """ Если очередь пуста, то True """
        return self.__queue.empty()

    @property
    def q_type(self) -> type:
        """ Возвращает тип элементов, допустимых для данной очереди """
        return self.__q_type


class MetaQueue:
    """ Класс инкапсулирющий ВСЕ очереди передачи данных приложения. Синглтон. """
    # Переделал класс в соответствие с sOlid.
    __this_object: Optional['MetaQueue'] = None
    # словарь очередей
    __queues_dict: Dict[str, SingleQueue] = {}
    # ключ синглтона
    __create_key: object = object()
    # Множество допустимых типов
    __types: set = {}

    def __init__(self, names: dict, create_key: object):
        """
        :param names: словарь с элементами вида {'имя_очереди': тип_элемента_очереди}
        :param create_key: ключ синглтона
        """
        assert (create_key is self.__create_key), \
            "MetaQueue object must be created using get_instanse method."

        for key, value in names.items():
            # создание словаря очередей
            self.__queues_dict[key] = SingleQueue(key, value)

        self.__types = set(names.values())

    @classmethod
    def get_instance(cls, queues: Dict[str, QueueMembers]) -> 'MetaQueue':
        """ Если объект не существует, то создаёт его.

        :param queues:  словарь с элементами вида {'имя_очереди': тип_элемента_очереди}
        """
        if cls.__this_object is None:
            cls.__this_object = MetaQueue(queues, cls.__create_key)
        return cls.__this_object

    def put(self, data_block: QueueMembers) -> None:
        """
        Добавить блок данных во ВСЕ очереди, которые готовы принять блок данных данного типа.

        :param data_block: блок данных
        """
        # был ли блок данных отправлен в какую-либо очередь?
        was_sent: bool = False
        # инициация прототипа
        clone_factory: CloneFactory = CloneFactory(data_block)

        # Перебираем очереди, чтобы отправить блок данных
        for name, queue in self.__queues_dict.items():
            if isinstance(data_block, queue.q_type):
                # Если data_block имеет тип, соответствующий данной очереди,
                # то отправляем data_block в эту очередь.
                # Pycharm почему-то считает, что data_block имеет тип type.
                queue.put(clone_factory.clone())
                was_sent = True

        if not was_sent:
            # Если для блока данных не нашлось очереди, значит мы не ждём данных этого типа.
            raise TypeError('Data block type ({0}) is not valid. Expected: {1}'
                            .format(type(data_block), self.__types))

    def put_by_queue_name(self, queue_name: str, data_block: QueueMembers) -> None:
        """ Запись блока данных в конкретную очередь, определяемую именем этой очереди.

        :param queue_name: имя очереди
        :param data_block: блок данных, предназначенный для отправления в очередь.
        """
        # Инициация прототипа
        clone_factory: CloneFactory = CloneFactory(data_block)

        if queue_name in self.__queues_dict.keys():
            # Имя очереди присутствует среди имён очередей
            # Отправляем блок данных в эту очередь.
            self.__queues_dict[queue_name].put(clone_factory.clone())
        else:
            raise ValueError('MetaQueue: queue_name="{0}" argument is not valid key of queues dict'.format(queue_name))


    def get(self, queue_name: str) -> QueueMembers:
        """ Получить блок данных из очереди.

        :param queue_name: имя очереди
        :return: блок данных, полученный из очереди
        """
        if queue_name in self.__queues_dict.keys():
            return self.__queues_dict[queue_name].get()
        else:
            raise ValueError('MetaQueue: queue_name="{0}" argument is not valid key of queues dict'.format(queue_name))

    def empty(self, queue_name: str) -> bool:
        """ Очередь пуста?

        :param queue_name: имя очереди
        :return: очередь пуста? True или False
        """
        if queue_name in self.__queues_dict.keys():
            return self.__queues_dict[queue_name].empty()

        raise ValueError('MetaQueue: name="{0}" argument is not valid key of queues dict'.format(queue_name))


class Reinforcement:
    """
    Класс подкрепления.

    """
    # Предварительно.
    # 1. Разбить пространство на зоны / квадраты.
    # 2. При попадании в квадрат, актор получает подкрепление.
    # 3. Подкрепление тем выше, чем ближе изделие к точке посадки.
    # -. Учитываются только переходы от зоны с низким подкреплением в зону с высоким подкреплением,
    # при обратном переходе, подкрепление - ноль.
    # -. Подкрепление в квадрате делится на время, сколько работали двигатели в предыдущем квадрате, таким образом,
    # чем меньше работали двигатели, тем выше подкрепление.
    # -. При повторном переходе из зоны с низким подкреплением в зону с высоким,
    # 4. При попадании изделия в некую окрестность точки посадки,
    # производится проверка на вписывание в динамические параметры по типу "не больше",
    # и назначется окончательное подкрепление.
    #
    # Вариант 1.
    # - Разбить пространство на концентрические сектора с единым центром в точке посадки.
    # - Концентрические сектора совпадают с границами диапазонов считывания данных.
    # - Максимальное время работы любого двигателя в рамках одного диапазона считывания данных - 10 секунд. Актуально
    # для больших диапазонов.
    # - Подкрепление для данного состояния прямо пропорционально базовому подкреплению и обратно пропорционально
    # времени работы маршевого и рулевых двигателей в предыдущем диапазоне считывания показаний. Т. е., если в данном
    # диапазоне считывания двигатели не работали, то подкрепление за проход этого диапазона будет максимально и равно
    # базовому.
    # - Установить подкрепление за посадку (с оговоренной погрешностью) - 0,3 (выход за пределы оговорённой
    # погрешности по любому параметру на 10% уменьшает данную величину подкрепления на 1%, на 20% - на 5%,
    # на 30% - на 10% и т. д. до нуля), а суммарное базовое подкрепление за весь процесс приземления - 0,7
    #
    # Вариант 2.
    # Логика: приближение к точке посадки должно поощеряться, работа двигателей должна наказываться.
    # - Если при переходе из одного состояния в другое происходит приближение к точке посадки - поощеряем.
    # - Если при переходе из одного состояния в другое радиус-вектор центра масс изделия
    # меньше самого короткого в данном испытании - поощеряем.
    # - Если при переходе из одного состояния в другое работают двигатели - уменьшаем поощерение.
    # Т. е.
    #

    # successLandingBase = 0.3
    # processBase = 1 - successLandingBase
    # минимальный вектор положения центра масс изделия, достигнутый в одном испытании
    min_vector = VectorComplex.get_instance(float("inf"), float("inf"))

    accuracy = 0

    @classmethod
    def get_reinforcement(cls, stage_status: RealWorldStageStatusN, jets: StageControlCommands) -> float:
        """
        Подкрепление

        :param stage_status: состояние ступени
        :param jets: информация о работавших двигателях
        """
        success_reinforcement = 0.
        landing_reinforcement = 0.
        if Finish.is_one_test_failed(stage_status.position):
            cls.min_vector = VectorComplex.get_instance(float("inf"), float("inf"))
            return 0

        # подкрепление за удачную посадку
        if Finish.is_one_test_success(stage_status, cls.accuracy):
            success_reinforcement = 100

        # подкрепление в процесс посадки
        # корректирующий подкрепление множитель
        mult = 0
        if abs(stage_status.position) < abs(cls.min_vector):
            # если достигли позиции ещё ближе, чем была самая близкая, то фиксируем данный радиус-вектор
            cls.min_vector = stage_status.position
            # собираем множитель, в зависимости от включённости двигателей
            mult += 1.25 if jets.top_left else 0
            mult += 1.25 if jets.top_right else 0
            mult += 1.25 if jets.down_left else 0
            mult += 1.25 if jets.down_right else 0
            mult += 5.0 if jets.main else 0
            # все одновременно работающие рулевые двигатели имеют "цену" одного работающего маршевого двигателя
            # считаем, с учётом работавших двигателей, понижая подкрепление
            landing_reinforcement = 1 if mult == 0 else 10 / mult

            if Finish.is_one_test_success(stage_status, cls.accuracy):
                cls.min_vector = VectorComplex.get_instance(float("inf"), float("inf"))

        return success_reinforcement + landing_reinforcement


class Finish:
    """
    Класс завершения единичного испытания

    """
    # Допустимое отклонение при выявлении факта посадки (метров)
    __yEpsilon = 0.01
    # Высота выключения двигателей (по высоте центра масс)
    __leg_relative_y = Sizes.massCenterFromLandingPlaneDistance

    # Необходим для того, чтобы единичное испытание не длилось чрезмерное неразумное время
    def __init__(self):
        pass

    @classmethod
    def is_one_test_failed(cls, coord: VectorComplex) -> bool:
        """ Проверка на неблагополучное завершение очередной тренировки

        :param coord: центр масс ракеты в СКИП
        """
        # Очередная тренировка заканчивается либо удачной посадкой, либо ударом о землю,
        # либо выходом за пределы зоны испытаний
        # Метод необходим исключительно для того, чтобы одно испытание не длилось вечно
        if fabs(coord.x) * 2 > BigMap.width \
            or coord.y > BigMap.height \
            or coord.y < cls.__leg_relative_y - cls.__yEpsilon:
            # Если ступень вылетела за пределы испытательного полигона:
            # - ступень вылетела за левую/правую границу полигона
            # - вылетела за верхнюю границу полигона
            # - вылетела за нижнюю границу полигона
            # испытание завершено
            return True
        return False

    @classmethod
    def is_one_test_success(cls, state: RealWorldStageStatusN, accuracy: int, close=True)->bool:
        """
        Посадка завершена успешно. Уррраааа!

        :param state: состояние изделия
        :param accuracy: параметр выбранной точности, 0, 1, 2, ..., 9
        :param close: выбрать диапазон расчёта параметров: дальний (не очень точный) или ближний (точный)
        :type close: bool
        """

        def within(accuracy: dict, value: float)->bool:
            """ Проверка на нахождение внутри диапазона """
            if accuracy["min"] < value < accuracy["max"]:
                return True
            else:
                return False

        accuracy_dict = Finish.landing_scope(accuracy, close)

        # Последовательная проверка по всем параметрам на успешность попадания в их диапазоны.
        if within(accuracy_dict["dy"], state.position.y) and within(accuracy_dict["dx"], state.position.x):
            if within(accuracy_dict["dVy"], state.velocity.y) and within(accuracy_dict["dVx"], state.velocity.x):
                if within(accuracy_dict["dAy"], state.acceleration.y) and within(accuracy_dict["dAx"], state.acceleration.x):
                    if within(accuracy_dict["dPhi"], state.orientation):
                        if within(accuracy_dict["dW"], state.angular_velocity):
                            if within(accuracy_dict["dE"], state.angular_acceleration):
                                return True
        return False

    @classmethod
    def landing_scope(cls, step: int, close=True)->Dict[AnyStr, Dict[AnyStr, float]]:
        """
        Диапазоны параметров, в которые должно попасть изделие при штатной посадке

        :param step: одно из десяти значений: 0, 1, ..., 9, где 0 - максимальная точность, 9 - минимальная точность
        :param close: если True, выдаём значения высокой точности при нахождении у поверхности, если False - низкой.
        :type close: bool
        :return: Словарь, содержащий границы допустимости вида {'parameter_name': {'min': min_value, 'max': max_value}}
        """
        def so_far(x: int)->tuple:
            """ Линейная функция падающая от (9: 100) до (0; 1)

            :return: min - (-1, +1)
            """
            value = ((100 - 1) / 9) * x + 1
            return -value, +value


        def so_close(x: int)->tuple:
            """ Линейная функция, падающая от (9; 1) до (0; 0.01)

             :return: min - (-0.01, +0.01)
             """
            value = ((1 - 0.01) / 9) * x + 0.01
            return -value, +value

        result = so_close(step) if close else so_far(step)
        # Точность по X в максимуме будет (-5, +5), в минимуме - (-50000. +50000)
        result_x = (result[0] * 500, result[1] * 500)
        # Кооректировка к точности в максимуме будет +0,01, в минимуме +45000
        result_y = result[1] if close else result[1] * 50 * step

        return {
                # допустимый диапазон положения по оси Y
                "dy": {"min": cls.__leg_relative_y, "max": cls.__leg_relative_y + result_y},
                # допустимый диапазон положения по оси Х
                "dx": {"min": result_x[0], "max": result_x[1]},
                # допустимый диапазон линейной скорости по оси Y
                "dVy": {"min": result[0], "max": result[1]},
                # допустимый диапазон линейной скорости по оси X
                "dVx": {"min": result[0], "max": result[1]},
                # допустимый диапазон линейного ускорения по оси Y
                "dAy": {"min": result[0], "max": result[1]},
                # допустимый диапазон линейного ускорения по оси Х
                "dAx": {"min": result[0], "max": result[1]},
                # допустимый диапазон угла ориентации
                "dPhi": {"min": result[0], "max": result[1]},
                # допустимый диапазон угловой скорости
                "dW": {"min": result[0], "max": result[1]},
                # допустимый диапазон уголового ускорения
                "dE": {"min": result[0], "max": result[1]}
                }

def math_int(value: float)->int:
    """
    Округление до целого по правилу математики.

    :param value: входное число с плавающей точкой
    :return: округлённое до целого
    """
    return int(value + (0.5 if value > 0 else -0.5))


class ZeroOrOne(Enum):
    ZERO: int = 0
    ONE: int = 1

def ones_and_zeros_variants_f(vector_length: int, start_position: int)->List[List[ZeroOrOne]]:
    """ Функция возвращает ВСЕ варианты размещения (все комбинации) из множества [0; 1] в векторе длиной *vectorLength*


    Варианты расположения нулей и единиц в векторе начинаются с позиции *start_position* включительно.
    До позиции *startPositon* в векторе находятся нули.

    :param vector_length: длинна списка, варианты расположения нулей и единиц в котором мы ищем
    :param start_position: позиция, до которой в векторе всегда находятся нули, с неё начинается присутствие нулей и ед.
    :return: список вида [[0, 0, 0, 0], [0, 0, 1, 0], ..., [0, 1, 1, 1]]
    """

    # Суть работы функции.
    # Везде нули - один вариант
    # Единица ставится на первую позицию - второй вариант
    # Единица смещается на вторую позицию - третий вариант.
    # ...
    # После прохода единицы до конца.
    # Единица ставится на первую и вторую позиции - ещё вариант
    # Вторая единица смещается на одну позицию вправо - ещё вариант
    # ... и т. д. до упора вправо.
    # Первая единица смещается вправо на одну позицию - ещё вариант
    # ... и т. д. пока она не упрётся в единицу, достигшую правого края.
    # Далее, слева ставятся три единицы и так же поочерёдно сдвигаются вправо, образуя новые варианты.
    # ...
    # И, последний вариант - все единицы

    def one_trip(start: int, stop: int, start_str: list, start_point: int, mother_list: list) -> None:
        """ Подпрограмма, выдающая ВСЕ варианты для конечного набора единиц, смещая их поочерёдно вправо

        :param start: позиция, в которой стоит единица, которую мы будем двигать вправо
        :param stop: позиция до которой мы будем двигать единицу (но не занимая эту позицию)
        :param start_str: исходный список, в котором слева есть единицы, которые мы и должны поочерёдно сместить вправо
        :param mother_list: результирующий список, к которому мы последовательно добавляем получающиеся варианты
        """

        temp_list = start_str.copy()
        for i in range(start, stop):
            temp_list = temp_list.copy()
            if i + 1 == stop:
                # если единица достигла правого края
                if start != start_point:
                    # и если слева от той позиции откуда эта единица стартовала ещё есть позиции с единицами
                    # начинаем двигать её сестру, которая стояла слева от неё
                    one_trip(start - 1, stop - 1, temp_list, start_point, mother_list)
                return
            else:
                # а если единица ещё не достигла правого свободного края
                # присваиваем её позиции ноль
                temp_list[i] = 0.
                # а следующей позиции справа единицу, как бы сдвигая эту самую единицу на одну позицию вправо
                temp_list[i + 1] = 1.
                # пристыковываем полученный набор к результирующему списку
                mother_list.append(temp_list)

    # список-заготовка из нулевых элементов
    zero_list: list = [x * 0 for x in range(vector_length)]

    # результат, собственно
    result: list = []
    # первый элемент результата - список из нулевых элементов
    result.append(zero_list.copy())

    for j in range(start_position, vector_length):
        start_str = zero_list.copy()
        for m in range(start_position, j + 1):
            # заполняем ведущими единицами
            start_str[m] = 1.

        # ^^^^ цикл, выдающий последовательно списки вида [1., 0., ..., 0.], [1., 1., ..., 0.], ..., [1., 1., ..., 1.]

        start = j
        stop = vector_length

        result.append(start_str)
        one_trip(start, stop, start_str, start_position, result)
    return result


