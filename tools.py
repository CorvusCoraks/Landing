from point import VectorComplex
from math import fabs
from stage import Sizes, BigMap
from structures import RealWorldStageStatusN, StageControlCommands, ReinforcementValue
from typing import TypeVar, Dict, AnyStr, List, Optional, Callable, overload
from enum import Enum
from basics import ZeroOne, Bit
from random import random
from con_intr.ifaces import Inbound, DataTypeEnum, AppModulesEnum
import time
import threading
import platform


# Переменная типа (чтобы это не значило): классы объектов данных, которые передаются через очереди
QueueMembers = TypeVar('QueueMembers', RealWorldStageStatusN, StageControlCommands, ReinforcementValue)


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
        :param jets: информация о работавших двигателях, приведших к состоянию *stage_status*
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
    # todo Оно надо:?
    ZERO: int = 0
    ONE: int = 1


class KeyPressCheck:
    """ Класс получения из консоли введённых пользователем данных.
    """
    def _press_enter_simulation(self):
        """ Платформозависимая эмуляция нажатия клавиши Enter. """
        if platform.system() == 'Linux':
            # не смог найти простого решения.
            # Под Linux ответ пользователя обязателен.
            pass
        elif platform.system() == 'Windows':
            """https://stackoverflow.com/questions/2791839/
            which-is-the-easiest-way-to-simulate-keyboard-and-mouse-on-python"""
            import ctypes
            # Эмуляция нажатия клавиши Enter
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)

    def __init__(self, prompt: str, default: str, others: list[str]):
        """

        :param prompt: Приглашение.
        :param default: Значение по умолчанию, принимаемое классом, если пользователь ничего не вводит в консоль.
        :param others: Другие допустимые варианты ввода от пользователя.
        """
        self.__prompt = prompt
        # список всех допустимых значений ввода
        self.__valid = ['', default, *others]
        # Время ожидания ввода пользователя.
        self.__WAITING_TIME: int = 5
        # То, что пользователь ввёл.
        self.__answer: Optional[str] = None

    def __check(self) -> None:
        """ Метод, проверяющий факт ввода через определённый промежуток времени. """
        time.sleep(self.__WAITING_TIME)
        if self.__answer is not None:
            return
        print("\nTime is over.")
        self._press_enter_simulation()

    def input(self) -> str:
        """ Аналог стандартного метода input().

        :return: строка, которую ввёл пользователь.
        """
        t = threading.Timer(10, self.__check)
        t.start()

        while True:
            self.__answer = input(self.__prompt)
            if self.__answer in self.__valid:
                t.cancel()
                break

        return self.__answer


def zo(value: float) -> ZeroOne:
    """ Метод контроля величины числа. Входная величина должна быть в диапазоне от 0 до 1. """
    if 0 < value < 1:
        return value
    else:
        raise ValueError("Argument object should be float in 0..1 diapason, but now: {}".format(value))


def action_variants(list_length: int) -> List[List[Bit]]:
    """ Множество всех вариантов действий актора. Метод: растущее бинарное дерево.

    :param list_length: длина вектора возможных действий актора
    :retutn: список вида [[0, 1, 1], [0, 0, 1]]
    """
    def fork(vector: list):
        """ Разветвление узла на две ветки. """
        vector_copy: List = vector.copy()
        vector.append(0)
        vector_copy.append(1)
        return vector, vector_copy

    # корень дерева
    start = [[]]
    # конечные листья дерева на одном проходе по его наращиванию
    temp = []
    result = []

    for i in range(list_length):
        for value in start:
            # Покрытие листьями дерева.
            temp.extend(fork(value))
        # переход к следующему уровню дерева.
        start = temp
        result = temp
        temp = []

    return result


def q_est_init() -> ZeroOne:
    """ Инициализация начального значения функции оценки ценности Q. """
    return zo(random())


class BoolWrapper:
    """ Класс обёртка для *bool* для возвращения значения через аргументы методов. Использование (объект-как-функция):
        \n b = BoolWrapper()
        \n b(True)
        \n bool_value: bool = b()
    """
    def __init__(self, value: bool = False):
        self._value: bool = value


    @overload
    def __call__(self) -> bool:
        """
        :return: возвращает значение сохранённого *bool*
        """
        ...

    @overload
    def __call__(self, arg: bool) -> None:
        """
        :param arg: Сохранить значение *bool*
        """
        ...

    def __call__(self, *args, **kwargs) -> Optional[bool]:
        if len(args) >= 1 and len(kwargs.keys()) > 0:
            # Проверка длины входных аргументов.
            raise ValueError("Input arguments quantity must be zero or one. But now: {}".
                             format(len(args) + len(kwargs.keys())))

        if len(args) == 0:
            # Если нет входных аргументов в методе, то просто возвращаем сохранённое значение.
            return self._value

        if isinstance(args[0], bool):
            # Проверка типа входного аргумента.
            # Если один единственный аргумент метода - *bool*, то сохраняем это значение.
            self._value = args[0]
        else:
            raise TypeError("Input argument have a wrong type: {}. Argument type must be 'bool".
                            format(type(args[0])))


class FinishAppBoolWrapper(BoolWrapper):
    """ Класс-обёртка для команды на завершение приложения.
    По умолчанию - False. Если установлено в True, изменить обратно уже нельзя. """
    def __call__(self, *args) -> Optional[bool]:
        # Если внутренний атрибут уже True, то изменить его на False уже нельзя
        if self._value or len(args) != 1:
            # Если внутренный атрибут уже True или в списке входящих аргументов НЕ ОДИН аргумент,
            # то возвращает значение внутреннего атрибута.
            return self._value
        else:
            return super().__call__(args[0])


def finish_app_checking(inbound: Inbound) -> bool:
    """ Проверка на появление в канале связи команды на завершение приложения. Возбуждает *FinishAppExeption*

    :param inbound: Словарь входных каналов блока приложения.
    """
    for sender in list(AppModulesEnum):
        # Перебор возможных отправителей приложения
        if sender in inbound.keys():
            # Если в словаре входных каналов предусмотрен такой отправитель
            if DataTypeEnum.APP_FINISH in inbound[sender].keys():
                # И у этого отправителя есть канал для передачи сигнала на завершение приложения.
                # И если команда на завершение приложения есть
                if inbound[sender][DataTypeEnum.APP_FINISH].has_incoming():
                    # Получаем эту команду
                    inbound[sender][DataTypeEnum.APP_FINISH].receive()
                    # Возбуждаем исключение завершения приложения.
                    return True
                else:
                    return False


if __name__ == '__main__':
    b = BoolWrapper()
    b(True)
    print(b())

