""" Модуль расчёта движения ступени согласно физическим законам реального мира """
from torch import Tensor
import torch
from point import VectorComplex
import stage, cmath
from decart import complexChangeSystemCoordinatesUniversal
from sructures import StageControlCommands, RealWorldStageStatusN
# from tools import RealWorldStageStatus

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
# frequency = 1000 / 1000
# frequency = 1.

# Предыдущее состояние модели
previousStageStatus = RealWorldStageStatusN()

# Ускорение свободного падения в СКИП и СКЦМ
GravitationalAcceleration = VectorComplex.getInstance(0., -9.8067)

class DataFrequency:
    """
    Частота считывания показаний датчиков в зависимости от дальности до точки приземления и высоты изделия
    """
    # длительность (счётчик) нахождения в верхнем диапазоне после перехода с нижнего
    borderCounter = 0
    # текущая частота считывания показаний
    # большое начальное значение обеспечит при первоначальном запуске программы
    # автоматический "виртуальный" переход вниз из "виртуального" верхнего диапазона в реальный
    currentFrequancy = float("inf")

    # Множитель преобразования в микросекунды
    __multiplier = 0.001

    @classmethod
    def __border(cls, defaultFrequency: float, borderMax=10):
        if DataFrequency.currentFrequancy >= defaultFrequency:
            # если в этот диапазон произошёл переход сверху (по высоте/дистанции)
            # или мы уже были в этом дапазоне в один из прошлых разов
            # или же уже стабильно сидим в этом диапазоне после перехода сверху
            # отмечаем этот факт
            DataFrequency.borderCounter = 0
            # фиксируем новую периодичность считывания
            DataFrequency.currentFrequancy = defaultFrequency
            # переходим на новую периодичность считывания
            return defaultFrequency
        else:
            # Если в этот диапазоне оказались после посещения нижнего
            if DataFrequency.borderCounter > borderMax:
                # Если достигли постоянства нахождения в данном диапазоне после перехода снизу,
                # переходим на его периодичность считывания данных
                DataFrequency.borderCounter = 0
                DataFrequency.currentFrequancy = defaultFrequency
                return defaultFrequency
            # отмечаем длительность нахождения в верхнем диапазоне после нижнего
            DataFrequency.borderCounter += 1
            # но сохраняем периодичность по нижнему диапазону высоты/дистанции)
            return DataFrequency.currentFrequancy

    @classmethod
    def getFrequency(cls, distance: VectorComplex):
        """
        Периодичность считывания показаний датчиков в зависимости от дальности до точки приземления и высоты изделия

        :param distance: вектор расстояния от точки приземления до центра масс изделия
        :return: периодичность считывания показаний датчиков, сек
        :rtype int:
        """

        # todo убрать, при переходе к более-менее реальным процессам
        # временная отладочная установка, чтобы метод отдавал 1 сек.
        DataFrequency.currentFrequancy = 1000
        return 1000

        # дальность до точки приземления, метров
        module = abs(distance) + stage.Sizes.massCenterFromLandingPlaneDistance
        # высота до поверхности, метров
        altitude = distance.y + stage.Sizes.massCenterFromLandingPlaneDistance

        if module < 1 or altitude < 1:
            return DataFrequency.__border(1)
        elif module < 10 or altitude < 5:
            return DataFrequency.__border(10)
        elif module < 100 or altitude < 50:
            return DataFrequency.__border(100)
        elif module < 10000 or altitude < 5000:
            return DataFrequency.__border(1000)
        elif module < 100000 or altitude < 50000:
            return DataFrequency.__border(10000)
        else:
            # один раз в минуту
            return DataFrequency.__border(60000)
    @classmethod
    def toSec(cls, value):
        """
        Преобразование значения периодичности в микросекунды
        """
        return value * DataFrequency.__multiplier


# class RealWorldStageStatus():
#     """ Состояние ступени в конкретный момент времени """
#     def __init__(self, position=None,
#                  velocity=None,
#                  axeleration=None,
#                  orientation=None,
#                  angularVelocity=0.,
#                  angularAxeleration=0.,
#                  timeStamp=0):
#         """
#
#         :param position: вектор положения издения в СКИП
#         :type position: VectorComplex
#         :param velocity: вектор линейной скорости
#         :type velocity: VectorComplex
#         :param axeleration: вектор линейного ускорения
#         :type axeleration: VectorComplex
#         :param orientation: ориентация (положительно - против часовой стрелки), рад
#         :type orientation: VectorComplex
#         :param angularVelocity: угловая скорость (положительно - против часовой стрелки)
#         :type angularVelocity: float
#         :param angularAxeleration: угловое ускорение (положительно - против часовой стрелки)
#         :type angularAxeleration: float
#         :param timeStamp: метка времени в микросекундах
#         :type timeStamp: int
#         """
#         # Линейные положение, линейная скорость и ускорение - всё это в СКИП
#         self.position = position if position is not None else VectorComplex.getInstance()
#         self.velocity = velocity if velocity is not None else VectorComplex.getInstance()
#         # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
#         self.axeleration = axeleration if axeleration is not None else VectorComplex.getInstance()
#         # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
#         # if orientation is None:
#         #     self.orientation = VectorComplex.getInstance(0., 0.)
#         # else:
#         #     self.orientation = orientation
#         self.orientation = orientation if orientation is not None else VectorComplex.getInstance()
#         self.angularVelocity = angularVelocity
#         # Аналогично, зачем мне предыдущее угловое ускорение?
#         self.angularAxeleration = angularAxeleration
#         # предыдущее значение времени, необходимо для расчёта времменнОго интервала между двумя отсчётами
#         self.timeStamp: int = timeStamp
#         # Длительность действия этих параметров, сек
#         # todo убрать и перейти на timeStamp
#         # self.timeLength = timeLength
#         # todo использовать или previousTimeStamp, или timeLength. Одновременно, скорее всего излишне.
#
#     def lazyCopy(self):
#         newObject = RealWorldStageStatus()
#         newObject.position = self.position.lazyCopy()
#         newObject.velocity = self.velocity.lazyCopy()
#         newObject.axeleration = self.axeleration.lazyCopy()
#         newObject.orientation = self.orientation.lazyCopy()
#         newObject.angularVelocity = self.angularVelocity
#         newObject.angularAxeleration = self.angularAxeleration
#         newObject.timeStamp = self.timeStamp
#         # newObject.timeLength = self.timeLength
#         return newObject


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

    def __init__(self, fdownleft=None, fdownright=None,
                 fdownup=None,
                 ftopleft=None, ftopright=None,
                 gdown=None, gcenter=None,
                 gtop=None, psi=0.):
        """
        По умолчанию, все силы нулевые.

        :param fdownleft: Сила (ньютоны) нижнего левого двигателя
        :param fdownright:Сила (ньютоны) нижнего правого двигателя
        :param fdownup:Сила (ньютоны) маршевого (центрального) двигателя
        :param ftopleft:Сила (ньютоны) верхнего левого двигателя
        :param ftopright:Сила (ньютоны) верхнего правого двигателя
        :param gdown:Сила тяжести (ньютоны) нижней массы
        :param gcenter:Сила тяжести (ньютоны) средней массы в центре масс
        :param gtop:Сила тяжести (ньютоны) верхней массы
        :param psi: угол отклонения вектора ориентации от вертикали
        """
        # Силы действия двигателей указываются в СКС.
        # Сила левого нижнего рулевого РД
        # self.FdownLeft: VectorComplex = fdownleft
        self.FdownLeft = VectorComplex.getInstance() if fdownleft is None else fdownleft
        # Сила правого нижнего рулевого РД
        # self.FdownRight: VectorComplex = fdownright
        self.FdownRight = VectorComplex.getInstance() if fdownright is None else fdownright
        # Сила маршевого РД
        # self.FdownUp: VectorComplex = fdownup
        self.FdownUp = VectorComplex.getInstance() if fdownup is None else fdownup
        # Сила левого верхнего РД
        # self.FtopLeft: VectorComplex = ftopleft
        self.FtopLeft = VectorComplex.getInstance() if ftopleft is None else ftopleft
        # Сила правого верхнего РД
        # self.FtopRight: VectorComplex = ftopright
        self.FtopRight = VectorComplex.getInstance() if ftopright is None else ftopright
        # Силы тяжести указываются в СКЦМ
        # Силя тяжести нижней массы
        # self.Gdown: VectorComplex = gdown
        self.Gdown = VectorComplex.getInstance() if gdown is None else gdown
        # Сила тяжести центральной массы
        # self.Gcenter: VectorComplex = gcenter
        self.Gcenter = VectorComplex.getInstance() if gcenter is None else gcenter
        # Силя тяжести верхней массы
        # self.Gtop: VectorComplex = gtop
        self.Gtop = VectorComplex.getInstance() if gtop is None else gtop
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
        # todo сделать private?
        # Если время действия сил равно нулю, то ускорение от этих сил заведомо равно нулю
        # if t == 0.: return 0.

        # Складываем силы двигателей, получая суперпозицию в СКС
        f = forces.FdownLeft + forces.FdownRight + forces.FdownUp + forces.FtopLeft + forces.FtopRight
        # Переводим суперпозицию сил двигателей в СКЦМ
        f = complexChangeSystemCoordinatesUniversal(f, VectorComplex.getInstance(0., 0.), -forces.psi)
        # Складываем силы тяжести в их суперпозицию в СКЦМ
        # g = forces.Gdown + forces.Gcenter + forces.Gtop
        g = (stage.Stage.topMass + stage.Stage.centerMass + stage.Stage.downMass) * GravitationalAcceleration
        # Векторно складываем суперпозицию сил двигателей и суперпозицию сил тяжести от масс
        sum = f + g
        # Получаем вектор линейного ускорения центра масс под действием суммы всех сил (Второй закон Ньютона)
        a = sum / (stage.Stage.topMass + stage.Stage.centerMass + stage.Stage.downMass)
        return a

    @classmethod
    def getE(cls, forces: Action):
        """
        Мгновенное угловое ускорение в системе коодинат ступени (СКС).

        :return:
        """
        # todo сделать private?
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
        # todo сделать private или вообще убрать?
        # result = VectorComplex.getInstanceC(S0.cardanus + V0.cardanus*t + Axeleration.getA().cardanus*t**2)
        result = V0 * t + Moving.getA(forces) * t ** 2
        return result

    @classmethod
    def getRotationAngle(cls, W0: float, t: float, forces: Action):
        """
        Изменение угла поворота ступени вокруг её центра масс.

        :return:
        """
        # todo сделать private или вообще убрать?
        result = W0 * t + Moving.getE(forces) * t ** 2
        return result

    @classmethod
    def getNewStatus(cls, controlCommands: StageControlCommands):
        """ Возвращает новое состояние ступени """
        duration = DataFrequency.toSec(DataFrequency.getFrequency(previousStageStatus.position))

        lineAxeleration = Moving.getA(Action(fdownup=VectorComplex.getInstance(0.,stage.Engine.mainEngineForce)))
        # lineAxeleration = Moving.getA(Action())
        # lineAxeleration = VectorComplex.getInstance(-3., 0.)
        lineVelocity = previousStageStatus.velocity + lineAxeleration * duration
        linePosition = previousStageStatus.position + lineVelocity * duration

        # новая ориентация
        # угловое ускорение
        angularAxeleration = 0.
        # угловая скорость, рад/сек
        angularVelocity = previousStageStatus.angularVelocity + angularAxeleration * duration
        # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        # cardanus = previousStageStatus.orientation.cardanus * cmath.rect(1., (- cmath.pi / 36))
        # поворот на угол, рад.
        angle = angularVelocity * duration
        # переводим угол из радианов в форму комплексного числа
        complexAngle = cmath.rect(1., angle)
        # поворот вектора ориентации через перемножение комплексных чисел
        cardanus = previousStageStatus.orientation.cardanus * complexAngle
        # приводим к единичному вектору
        cardanus = cardanus / abs(cardanus)
        # новая ориентация
        orientation = VectorComplex.getInstanceC(cardanus)

        # # новая ориентация
        # # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        # cardanus = previousStageStatus.orientation.cardanus * cmath.rect(1., (- cmath.pi / 36))
        # # приводим к единичному вектору
        # cardanus = cardanus / abs(cardanus)
        # # новая ориентация
        # orientation = VectorComplex.getInstanceC(cardanus)

        newPosition = RealWorldStageStatusN(position=linePosition, velocity=lineVelocity, axeleration=lineAxeleration,
                                           angularVelocity=angularVelocity, angularAxeleration=angularAxeleration,
                                           orientation=orientation)
        newPosition.timeStamp = previousStageStatus.timeStamp + DataFrequency.getFrequency(previousStageStatus.position)

        return newPosition
