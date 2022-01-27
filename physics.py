""" Модуль расчёта движения ступени согласно физическим законам реального мира """
from torch import Tensor
import torch
from point import VectorComplex
import stage, cmath
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

# Каждый отсчётный момент времени:
# 1. С датчиков ракеты поступает информация о её координатах в СКИП.
# 2. На основании координат п. 1, и сохранённых координат предыыдущей точки, считается скорость ракеты в текущей точке
# 3. На основании скорости в текущей точке и скорости в прредыдущей точки, считается ускорение.
# 4. Аналогично п. 2 и п. 3 считаются угловые скорости и ускорения.

# Частота считывания/передачи данных с датчиков ступени
# раз в секунду / Герц, если 1000, то это секунда
# Вполне возможно будет переменной: чем ниже скорость, тем меньше частота
# В числителе Герцы, а на итоге - секунды
frequency = 1000 / 1000
# frequency = 1.
# Предыдущее состояние модели
previousStageStatus = None


class HistoricData:
    """ Класс исторических данных, необходимых для расчёта ускорения и скорости """
    # todo Возможно, класс не нужен
    # Так как без знания двух очередных значений положения и времени между ними невозможно посчитать скорость
    # и ускорение объекта
    # Линейные положение, линейная скорость и ускорение - всё это в СКИП
    previousPosition: VectorComplex
    previousVelocity: VectorComplex
    # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
    previousAxeleration: VectorComplex
    # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
    previousOrientation: VectorComplex
    previousAngularVelocity: float
    # Аналогично, зачем мне предыдущее угловое ускорение?
    previousAngularAxeleration: float
    # предыдущее значение времени, необходимо для расчёта времменнОго интервала между двумя отсчётами
    previousTimeStamp: float
    # Длительность действия этих параметров, сек
    timeLength: float
    # todo использовать или previousTimeStamp, или timeLength


class RealWorldStageStatus():
    """ Состояние ступени в конкретный момент времени """
    def __init__(self, position=None,
                 velocity=None,
                 axeleration=None,
                 # Бред. Ориентация с какого-то хрена сама вставится по вектору {0.087; 0.996}
                 orientation=None,
                 angularVelocity=0.,
                 angularAxeleration=0.,
                 timeLength=0.):
        # Линейные положение, линейная скорость и ускорение - всё это в СКИП
        self.position = position if position is not None else VectorComplex.getInstance()
        self.velocity = velocity if velocity is not None else VectorComplex.getInstance()
        # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
        self.axeleration = axeleration if axeleration is not None else VectorComplex.getInstance()
        # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
        # if orientation is None:
        #     self.orientation = VectorComplex.getInstance(0., 0.)
        # else:
        #     self.orientation = orientation
        self.orientation = orientation if orientation is not None else VectorComplex.getInstance()
        self.angularVelocity = angularVelocity
        # Аналогично, зачем мне предыдущее угловое ускорение?
        self.angularAxeleration = angularAxeleration
        # предыдущее значение времени, необходимо для расчёта времменнОго интервала между двумя отсчётами
        self.timeStamp: float = 0.
        # Длительность действия этих параметров, сек
        self.timeLength = timeLength
        # todo использовать или previousTimeStamp, или timeLength. Одновременно, скорее всего излишне.

    def lazyCopy(self):
        newObject = RealWorldStageStatus()
        newObject.position = self.position.lazyCopy()
        newObject.velocity = self.velocity.lazyCopy()
        newObject.axeleration = self.axeleration.lazyCopy()
        newObject.orientation = self.orientation.lazyCopy()
        newObject.angularVelocity = self.angularVelocity
        newObject.angularAxeleration = self.angularAxeleration
        newObject.timeStamp = self.timeStamp
        newObject.timeLength = self.timeLength
        return newObject

    # @classmethod
    # def zero(cls):
    #     return RealWorldStageStatus



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


class BigMap:
    """ Класс испытательного полигона """
    # # Ширина полигона в метрах
    # width = 300000
    # # Высота полигона в метрах
    # height = 100000
    # Временный размер на отладку
    # Ширина полигона в метрах
    width = 100
    # Высота полигона в метрах
    height = 500
    # Координаты начала координат СКИП в системе координат канвы (СКК) в масштабе 1:1
    # todo логически не верно, это же карта полигона. Убрать.
    testPoligonOriginInCCS = VectorComplex.getInstance(width / 2, height * 0.95)
    # Координаты начала координат СКК в СКИП в масштабе 1:1
    canvasOriginInPoligonCoordinates = VectorComplex.getInstance(- width / 2, height * 0.95)
    # Координаты точки приземления в СКИП
    landingPointInPoligonCoordinates = VectorComplex.getInstance()
    # Координаты стартовой точки в СКИП
    startPointInPoligonCoordinates = VectorComplex.getInstance(0., height * 0.9)
    # Координаты центра тяжести ступени (координаты начала координат СКС в СКИП в масштабе 1:1)
    # Движущаяся система координат.
    stageViewOriginInPoligonCoordinates = VectorComplex.getInstance()


class Action():
    """
    Класс всех сил действующих на ступень. Необходим для компактной их передачи в методах.
    """
    # def __init__(self):
    #     # Силы действия двигателей указываются в СКС.
    #     # Сила левого нижнего рулевого РД
    #     self.FdownLeft: VectorComplex
    #     # Сила правого нижнего рулевого РД
    #     self.FdownRight: VectorComplex
    #     # Сила маршевого РД
    #     self.FdownUp: VectorComplex
    #     # Сила левого верхнего РД
    #     self.FtopLeft: VectorComplex
    #     # Сила правого верхнего РД
    #     self.FtopRight: VectorComplex
    #     # Силы тяжести указываются в СКЦМ
    #     # Силя тяжести нижней массы
    #     self.Gdown: VectorComplex
    #     # Сила тяжести центральной массы
    #     self.Gcenter: VectorComplex
    #     # Силя тяжести верхней массы
    #     self.Gtop: VectorComplex
    #     # Угол отклонения от вертикали. Фактически, это - угол, на который надо повернуть ось абцисс СКЦМ,
    #     # чтобы получить ось абцисс СКС
    #     self.psi: float

    def __init__(self, fdownleft=VectorComplex.getInstance(), fdownright=VectorComplex.getInstance(),
                 fdownup=VectorComplex.getInstance(),
                 ftopleft=VectorComplex.getInstance(), ftopright=VectorComplex.getInstance(),
                 gdown=VectorComplex.getInstance(), gcenter=VectorComplex.getInstance(),
                 gtop=VectorComplex.getInstance(), psi=0.):
        """
        По умолчанию, все силы нулевые.

        :param fdownleft:
        :param fdownright:
        :param fdownup:
        :param ftopleft:
        :param ftopright:
        :param gdown:
        :param gcenter:
        :param gtop:
        :param psi:
        """
        # Силы действия двигателей указываются в СКС.
        # Сила левого нижнего рулевого РД
        self.FdownLeft: VectorComplex = fdownleft
        # Сила правого нижнего рулевого РД
        self.FdownRight: VectorComplex = fdownright
        # Сила маршевого РД
        self.FdownUp: VectorComplex = fdownup
        # Сила левого верхнего РД
        self.FtopLeft: VectorComplex = ftopleft
        # Сила правого верхнего РД
        self.FtopRight: VectorComplex = ftopright
        # Силы тяжести указываются в СКЦМ
        # Силя тяжести нижней массы
        self.Gdown: VectorComplex = gdown
        # Сила тяжести центральной массы
        self.Gcenter: VectorComplex = gcenter
        # Силя тяжести верхней массы
        self.Gtop: VectorComplex = gtop
        # Угол отклонения от вертикали. Фактически, это - угол, на который надо повернуть ось абцисс СКЦМ,
        # чтобы получить ось абцисс СКС
        # todo вынести отсюда, так как не относится к силам
        self.psi: float = psi

    # def setAction(self, FdownLeft: VectorComplex, FdownRight: VectorComplex, FdownUp: VectorComplex,
    #               Gdown: VectorComplex, Gcenter: VectorComplex, Gtop: VectorComplex,
    #               FtopLeft: VectorComplex, FtopRight: VectorComplex,
    #               psi: float):
    #
    #     self.FdownLeft = FdownLeft
    #     self.FdownRight = FdownRight
    #     self.FdownUp = FdownUp
    #     self.FtopLeft = FtopLeft
    #     self.FtopRight = FtopRight
    #     self.Gdown = Gdown
    #     self.Gcenter = Gcenter
    #     self.Gtop = Gtop
    #     self.psi = psi


class Moving():
    """
    Расчёт динамических параметров ступени (смещение, поворот, скорости и ускорения) под действием сил в СКИП
    """
    @classmethod
    def getA(cls, forces: Action):
        """
        Мгновенное линейное ускорение как вектор в СКЦМ

        :return:
        """
        # Если время действия сил равно нулю, то ускорение от этих сил заведомо равно нулю
        # if t == 0.: return 0.

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
    def getE(cls, forces: Action):
        """
        Мгновенное угловое ускорение в системе коодинат ступени.

        :return:
        """
        # Если время действия сил равно нулю, то ускорение от этих сил заведомо равно нулю
        # if t == 0.: return 0.

        # pass
        return 0.

    # @classmethod
    # def getLineVelosity(cls, V0: VectorComplex, t: float, forces: Action):
    #     return V0 + Moving.getA(forces) * t


    @classmethod
    def getDistanseVector(cls, V0: VectorComplex, t: float, forces: Action):
        """
        Измение положения центра масс ступени в системе координат полигона

        :param V0: Начальная скорость центра масс в точке S0
        :param t: Время действия суперпозиции сил
        :param forces: Силы действующие на объект
        :return: перемещение (вектор) из начальной точки с V0 в новую ночку под действием суперпозиции сил
        :rtype: VectorComplex
        """
        # result = VectorComplex.getInstanceC(S0.cardanus + V0.cardanus*t + Axeleration.getA().cardanus*t**2)
        result = V0 * t + Moving.getA(forces) * t ** 2
        return result

    @classmethod
    def getRotationAngle(cls, W0: float, t: float, forces: Action):
        """
        Изменение угла поворота ступени вокруг её центра масс.

        :return:
        """
        result = W0 * t + Moving.getE(forces) * t ** 2
        return result

    @classmethod
    def getNewStatus(cls):
        """ Возвращает новое состояние ступени """

        lineAxeleration = Moving.getA(Action())
        lineVelocity = previousStageStatus.velocity + lineAxeleration * frequency
        linePosition = previousStageStatus.position + lineVelocity * frequency

        # новая ориентация
        # orientation = VectorComplex.getInstance()
        # сложениself.orientation = orientationе двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        cardanus = previousStageStatus.orientation.cardanus * cmath.rect(1., (- cmath.pi / 36))
        # приводим к единичному вектору
        cardanus = cardanus / abs(cardanus)
        # новая ориентация
        orientation = VectorComplex.getInstanceC(cardanus)

        # newPosition = RealWorldStageStatus(position=linePosition, velocity=lineVelocity,
        #                                    axeleration=lineAxeleration, orientation=previousStageStatus.orientation)
        newPosition = RealWorldStageStatus(position=linePosition, velocity=lineVelocity,
                                           axeleration=lineAxeleration, orientation=orientation)
        return newPosition
