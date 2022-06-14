""" Модуль расчёта движения ступени согласно физическим законам реального мира """
from torch import Tensor
import torch
from point import VectorComplex
import stage, cmath
from decart import complexChangeSystemCoordinatesUniversal
from structures import StageControlCommands, RealWorldStageStatusN
from tools import math_int
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
# 2. На основании координат п. 1, и сохранённых координат предыдущей точки, считается скорость ракеты в текущей точке
# 3. На основании скорости в текущей точке и скорости в предыдущей точки, считается ускорение.
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

class CheckPeriod:
    """
    Интервал считывания показаний датчиков в зависимости от дальности до точки приземления и высоты изделия
    """
    # длительность (счётчик) нахождения в верхнем диапазоне после перехода с нижнего
    borderCounter: int = 0
    # текущий интервал между считываниями показаний
    # большое начальное значение обеспечит при первоначальном запуске программы
    # автоматический "виртуальный" переход вниз из "виртуального" верхнего диапазона в реальный
    # к сожалению только float, потому в процессе работы, контролируемо переведём её в int
    currentFrequancy = float("inf")

    # Множитель преобразования в секунды
    __multiplier: float = 0.001

    @classmethod
    def __border(cls, defaultFrequency: int, borderMax=10) -> int:
        """
        Метод определяет, пересечение границ между диапазонами и устойчивость нахождения в диапазоне

        :param defaultFrequency: длительность интервала между считываниями показаний по умолчанию
        :param borderMax: порог нахождения в диапазоне, после которого считается, что нахождение в нём устойчиво
        :return: подтверждённая длительность между интервалами считывания
        """
        if CheckPeriod.currentFrequancy >= defaultFrequency:
            # если в этот диапазон произошёл переход сверху (по высоте/дистанции)
            # или мы уже были в этом дапазоне в один из прошлых разов
            # или же уже стабильно сидим в этом диапазоне после перехода сверху
            # отмечаем этот факт
            CheckPeriod.borderCounter = 0
            # фиксируем новую периодичность считывания и, автоматически, превращаем левую величину из float в int
            CheckPeriod.currentFrequancy = defaultFrequency
            # переходим на новую периодичность считывания
            return defaultFrequency
        else:
            # Если в этот диапазоне оказались после посещения нижнего
            if CheckPeriod.borderCounter > borderMax:
                # Если достигли постоянства нахождения в данном диапазоне после перехода снизу,
                # переходим на его периодичность считывания данных
                CheckPeriod.borderCounter = 0
                # фиксируем новую периодичность считывания и, автоматически, превращаем левую величину из float в int
                CheckPeriod.currentFrequancy = defaultFrequency
                return defaultFrequency
            # отмечаем длительность нахождения в верхнем диапазоне после нижнего
            CheckPeriod.borderCounter += 1
            # но сохраняем периодичность по нижнему диапазону высоты/дистанции)
            # CheckPeriod.currentFrequancy = int(CheckPeriod.currentFrequancy)
            if CheckPeriod.currentFrequancy is float:
                # для успокоения интерпретатора, превращаем выходную величину из float в int
                CheckPeriod.currentFrequancy = int(CheckPeriod.currentFrequancy)
            return CheckPeriod.currentFrequancy

    @classmethod
    def setDuration(cls, distance: VectorComplex):
        """
        Периодичность считывания показаний датчиков. Вызывать только при установке нового состояния изделия.

        :param distance: вектор расстояния от точки приземления до центра масс изделия
        :return: периодичность считывания показаний датчиков, миллисекунды
        :rtype int:
        """

        # # todo убрать, при переходе к более-менее реальным процессам
        # # временная отладочная установка, чтобы метод отдавал 1 сек.
        # CheckPeriod.currentFrequancy = 1000
        # return 1000

        # дальность до точки приземления, метров
        module = abs(distance) + stage.Sizes.massCenterFromLandingPlaneDistance
        # высота до поверхности, метров
        altitude = distance.y + stage.Sizes.massCenterFromLandingPlaneDistance

        if module < 1 or altitude < 1:
            return CheckPeriod.__border(1)
        elif module < 10 or altitude < 5:
            return CheckPeriod.__border(10)
        elif module < 100 or altitude < 50:
            return CheckPeriod.__border(100)
        elif module < 10000 or altitude < 5000:
            return CheckPeriod.__border(1000)
        elif module < 100000 or altitude < 50000:
            return CheckPeriod.__border(10000)
        else:
            # один раз в минуту
            return CheckPeriod.__border(60000)

    @classmethod
    def to_Sec(cls, value: int)->float:
        """
        Преобразование значения интервала в секунды
        """
        return value * CheckPeriod.__multiplier

    @classmethod
    def to_mSec(cls, value: int)->int:
        """ Преобразование значения интервала в миллисекунды """
        return math_int(CheckPeriod.to_Sec(value) * 1000)


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
        if controlCommands.allOff():
            # Если все двигатели выключены, все силы от двигателей сделать нулевыми
            pass

        duration = CheckPeriod.setDuration(previousStageStatus.position)
        secDuration = CheckPeriod.to_Sec(duration)

        lineAxeleration = Moving.getA(Action(fdownup=VectorComplex.getInstance(0.,stage.Engine.mainEngineForce)))
        # lineAxeleration = Moving.getA(Action())
        # lineAxeleration = VectorComplex.getInstance(-3., 0.)
        lineVelocity = previousStageStatus.velocity + lineAxeleration * secDuration
        linePosition = previousStageStatus.position + lineVelocity * secDuration

        # новая ориентация
        # угловое ускорение
        angularAxeleration = 0.
        # угловая скорость, рад/сек
        angularVelocity = previousStageStatus.angular_velocity + angularAxeleration * secDuration
        # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        # cardanus = previousStageStatus.orientation.cardanus * cmath.rect(1., (- cmath.pi / 36))
        # поворот на угол, рад.
        angle = angularVelocity * secDuration
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

        newPosition = RealWorldStageStatusN(position=linePosition, velocity=lineVelocity, acceleration=lineAxeleration,
                                            angular_velocity=angularVelocity, angular_acceleration=angularAxeleration,
                                            orientation=orientation)
        newPosition.time_stamp = previousStageStatus.time_stamp + duration
        # newPosition.secDuration = CheckPeriod.setDuration(linePosition)

        return newPosition
