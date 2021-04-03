""" Модуль расчёта движения ступени согласно физическим законам реального мира """
from torch import Tensor
import torch
from point import VectorComplex
import stage
from decart import complexChangeSystemCoordinatesUniversal

# Физическая модель ступени представляет из себя три жёстко связанные точки (лежат на оси ступени)
# массой m1 (центр дна ракеты), m2 (средняя точка, центр масс), m3 (верх ступени)
# Вышеуказанные массы и расстояния между ними подбираются вручную изначально (как исходные данные),
# с тем условием, чтобы центр масс приходился на точку m2
# Эти массы с течением времени не меняются.
# Движение ступени в рамках глобальных координат (система полигона) моделируется движением центра масс (точка m2)
# Ориентация ступени задаётся углом отклонения вертикального осевого вектора относительно вертикали глобальной
# системы координат.
# положение центра масс ступени и направляющий вектор передаются в модуль визуализации
# На остновании этих данных происходит отрисовка ступени на новом положении.

# Используемые системы координат:
# - Собственная система координат ступени (СКС): ось ординат совпадает с продольной овсью ступени, начало координат
# находится в центре масс ступени.
# - Система координат центра масс ступени (СКЦМ): начало координат совпадает с центром масс ступени,
# оси ординат и абцисс коллинеарны с соответствующими осями системы координат испытательного полигона.
# - Система координат испытательного полигона (СКИП): начало координат находится в точке желаемой посадки, ось ординат
# направлена вертикально вверх (против силы тяжести), ось абцисс направлено вправо.
# - Система координат канвы (СКК): ось абцисс напралвена вправо, ось ординат направлена вниз, начало координат находится
# "где-то высоко в небе"

class Rocket():
    """ Класс ракеты / ступени. Динамические параметры. """
    def __init__(self):
        # self.__baseVector: tensor = torch.zeros([1, 4])
        # координаты центра масс ракеты относительно точки посадки
        self.__coord: VectorComplex
        # угол отклонения оси ступени от вертикали
        self.__psi = 0.

        # вектор скорости ракеты
        self.__v: VectorComplex
        # вектор ускорения ракеты
        self.__a: VectorComplex

        # угловая скорость ступени
        self.__w: float
        # угловое ускорение ступени
        self.__e: float

    def ganerateState(self):
        """ Генерация начального положения ракеты / состояния всей системы """
        pass


class BigMap():
    """ Класс испытательного полигона """
    # # Ширина полигона в метрах
    # width = 300000
    # # Высота полигона в метрах
    # height = 100000
    # Временный размер на отладку
    # Ширина полигона в метрах
    width = 50
    # Высота полигона в метрах
    height = 100


class Action():
    def __init__(self):
        # Силы действия двигателей указываются в СКС.
        # Сила левого нижнего рулевого РД
        self.FdownLeft: VectorComplex
        # Сила правого нижнего рулевого РД
        self.FdownRight: VectorComplex
        # Сила маршевого РД
        self.FdownUp: VectorComplex
        # Сила левого верхнего РД
        self.FtopLeft: VectorComplex
        # Сила правого верхнего РД
        self.FtopRight: VectorComplex
        # Силы тяжести указываются в СКЦМ
        # Силя тяжести нижней массы
        self.Gdown: VectorComplex
        # Сила тяжести центральной массы
        self.Gcenter: VectorComplex
        # Силя тяжести верхней массы
        self.Gtop: VectorComplex
        # Угол отклонения от вертикали. Фактически, это - угол, на который надо повернуть ось абцисс СКЦМ,
        # чтобы получить ось абцисс СКС
        self.psi: float

    def setAction(self, FdownLeft: VectorComplex, FdownRight: VectorComplex, FdownUp: VectorComplex,
                  Gdown: VectorComplex, Gcenter: VectorComplex, Gtop: VectorComplex,
                  FtopLeft: VectorComplex, FtopRight: VectorComplex,
                  psi: float):

        self.FdownLeft = FdownLeft
        self.FdownRight = FdownRight
        self.FdownUp = FdownUp
        self.FtopLeft = FtopLeft
        self.FtopRight = FtopRight
        self.Gdown = Gdown
        self.Gcenter = Gcenter
        self.Gtop = Gtop
        self.psi = psi


class Axeleration():
    """
    Расчёт динамических параметров ступени (смещение, поворот, скорости и ускорения) под действием сил в СКИП
    """
    @classmethod
    def getA(cls, forces: Action):
        """
        Мгновенное линейное ускорение как вектор в СКЦМ

        :return:
        """
        # Складываем силы двигателей, получая суперпозицию в СКС
        f = forces.FdownLeft + forces.FdownRight + forces.FdownUp + forces.FtopLeft + forces.FtopRight
        # Переводим суперпозицию сил двигателей в СКЦМ
        f = complexChangeSystemCoordinatesUniversal(f, VectorComplex.getInstance(0., 0.), -forces.psi)
        # Складываем силы тяжести в их суперпозицию
        g = forces.Gdown + forces.Gcenter + forces.Gtop
        # Векторно складываем суперпозицию сил двигателей и суперпозицию сил тяжести от масс
        sum = f + g
        # Получаем вектор линейного ускорения центра масс под действием суммы всех сил (Второй закон Ньютона)
        a = sum / (stage.Stage.topMass + stage.Stage.centerMass + stage.Stage.downMass)
        return a

    @classmethod
    def getE(cls, FdowLeft: float, FdownRight: float, FdownUp: float, Gdown: float,
             Gcenter: float,
             FtopLeft: float, FtopRight: float, Gtop: float,
             psi: float):
        """
        Мгновенное угловое ускорение в системе коодинат ступени.

        :return:
        """
        return 0.

    @classmethod
    def getDistanseVector(cls, V0: VectorComplex, t: float):
        """
        Измение положения центра масс ступени в системе координат полигона

        :param V0: Начальная скорость центра масс в точке S0
        :param t: Время действия суперпозиции сил
        :return: перемещение (вектор) из начальной точки с V0 в новую ночку под действием суперпозиции сил
        :rtype: VectorComplex
        """
        # result = VectorComplex.getInstanceC(S0.cardanus + V0.cardanus*t + Axeleration.getA().cardanus*t**2)
        result = V0 * t + Axeleration.getA() * t ** 2
        return result

    @classmethod
    def getRotationAngle(cls, W0: float, t: float):
        """
        Изменение угла поворота ступени вокруг её центра масс.

        :return:
        """
        result = W0 * t + Axeleration.getE() * t ** 2
        return result
