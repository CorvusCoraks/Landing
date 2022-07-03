""" Модуль расчёта движения ступени согласно физическим законам реального мира """
from point import VectorComplex
import stage
import cmath
from decart import complexChangeSystemCoordinatesUniversal
from structures import StageControlCommands, RealWorldStageStatusN
from tools import math_int

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

# Ускорение свободного падения в СКИП и СКЦМ
GravitationalAcceleration = VectorComplex.get_instance(0., -9.8067)


class CheckPeriod:
    """
    Интервал считывания показаний датчиков в зависимости от дальности до точки приземления и высоты изделия
    """
    # длительность (счётчик) нахождения в верхнем диапазоне после перехода с нижнего
    border_counter: int = 0
    # текущий интервал между считываниями показаний
    # большое начальное значение обеспечит при первоначальном запуске программы
    # автоматический "виртуальный" переход вниз из "виртуального" верхнего диапазона в реальный
    # к сожалению только float, потому в процессе работы, контролируемо переведём её в int
    current_frequancy = float("inf")

    # Множитель преобразования в секунды
    __multiplier: float = 0.001

    @classmethod
    def __border(cls, default_frequency: int, border_max=10) -> int:
        """
        Метод определяет, пересечение границ между диапазонами и устойчивость нахождения в диапазоне

        :param default_frequency: длительность интервала между считываниями показаний по умолчанию
        :param border_max: порог нахождения в диапазоне, после которого считается, что нахождение в нём устойчиво
        :return: подтверждённая длительность между интервалами считывания
        """
        if CheckPeriod.current_frequancy >= default_frequency:
            # если в этот диапазон произошёл переход сверху (по высоте/дистанции)
            # или мы уже были в этом дапазоне в один из прошлых разов
            # или же уже стабильно сидим в этом диапазоне после перехода сверху
            # отмечаем этот факт
            CheckPeriod.border_counter = 0
            # фиксируем новую периодичность считывания и, автоматически, превращаем левую величину из float в int
            CheckPeriod.current_frequancy = default_frequency
            # переходим на новую периодичность считывания
            return default_frequency
        else:
            # Если в этот диапазоне оказались после посещения нижнего
            if CheckPeriod.border_counter > border_max:
                # Если достигли постоянства нахождения в данном диапазоне после перехода снизу,
                # переходим на его периодичность считывания данных
                CheckPeriod.border_counter = 0
                # фиксируем новую периодичность считывания и, автоматически, превращаем левую величину из float в int
                CheckPeriod.current_frequancy = default_frequency
                return default_frequency
            # отмечаем длительность нахождения в верхнем диапазоне после нижнего
            CheckPeriod.border_counter += 1
            # но сохраняем периодичность по нижнему диапазону высоты/дистанции)
            # CheckPeriod.current_frequancy = int(CheckPeriod.current_frequancy)
            if CheckPeriod.current_frequancy is float:
                # для успокоения интерпретатора, превращаем выходную величину из float в int
                CheckPeriod.current_frequancy = int(CheckPeriod.current_frequancy)
            return CheckPeriod.current_frequancy

    @classmethod
    def set_duration(cls, distance: VectorComplex) -> int:
        """
        Периодичность считывания показаний датчиков. Вызывать только при установке нового состояния изделия.

        :param distance: вектор расстояния от точки приземления до центра масс изделия
        :return: периодичность считывания показаний датчиков, миллисекунды
        """

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
    def to_sec(cls, value: int) -> float:
        """
        Преобразование значения интервала в секунды
        """
        return value * CheckPeriod.__multiplier

    @classmethod
    def to_mu_sec(cls, value: int) -> int:
        """ Преобразование значения интервала в миллисекунды """
        return math_int(CheckPeriod.to_sec(value) * 1000)


class Action:
    """
    Класс всех сил действующих на ступень. Необходим для компактной их передачи в методах.
    """
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
        self.FdownLeft: VectorComplex = VectorComplex.get_instance() if fdownleft is None else fdownleft
        # Сила правого нижнего рулевого РД
        self.FdownRight: VectorComplex = VectorComplex.get_instance() if fdownright is None else fdownright
        # Сила маршевого РД
        self.FdownUp: VectorComplex = VectorComplex.get_instance() if fdownup is None else fdownup
        # Сила левого верхнего РД
        self.FtopLeft: VectorComplex = VectorComplex.get_instance() if ftopleft is None else ftopleft
        # Сила правого верхнего РД
        self.FtopRight: VectorComplex = VectorComplex.get_instance() if ftopright is None else ftopright
        # Силы тяжести указываются в СКЦМ
        # Силя тяжести нижней массы
        self.Gdown: VectorComplex = VectorComplex.get_instance() if gdown is None else gdown
        # Сила тяжести центральной массы
        self.Gcenter: VectorComplex = VectorComplex.get_instance() if gcenter is None else gcenter
        # Силa тяжести верхней массы
        self.Gtop: VectorComplex = VectorComplex.get_instance() if gtop is None else gtop
        # Угол отклонения от вертикали. Фактически, это - угол, на который надо повернуть ось абцисс СКЦМ,
        # чтобы получить ось абцисс СКС
        # todo вынести отсюда, так как не относится к силам
        self.psi: float = psi


class Moving:
    """
    Расчёт динамических параметров ступени (смещение, поворот, скорости и ускорения) под действием сил в СКИП
    """
    @classmethod
    def get_a(cls, forces: Action) -> VectorComplex:
        """
        Мгновенное линейное ускорение как вектор в СКЦМ под действием сил *forces*
        """
        # todo сделать private?
        # Если время действия сил равно нулю, то ускорение от этих сил заведомо равно нулю
        # if t == 0.: return 0.

        # Складываем силы двигателей, получая суперпозицию в СКС
        f = forces.FdownLeft + forces.FdownRight + forces.FdownUp + forces.FtopLeft + forces.FtopRight
        # Переводим суперпозицию сил двигателей в СКЦМ
        f = complexChangeSystemCoordinatesUniversal(f, VectorComplex.get_instance(0., 0.), -forces.psi)
        # Складываем силы тяжести в их суперпозицию в СКЦМ
        g = (stage.Stage.topMass + stage.Stage.centerMass + stage.Stage.downMass) * GravitationalAcceleration
        # Векторно складываем суперпозицию сил двигателей и суперпозицию сил тяжести от масс
        sum_forces = f + g
        # Получаем вектор линейного ускорения центра масс под действием суммы всех сил (Второй закон Ньютона)
        a = sum_forces / (stage.Stage.topMass + stage.Stage.centerMass + stage.Stage.downMass)
        return a

    @classmethod
    def get_e(cls, forces: Action) -> float:
        """
        Мгновенное угловое ускорение в системе коодинат ступени (СКС) под действием сил *forces*.
        """
        # todo сделать private?
        # Если время действия сил равно нулю, то ускорение от этих сил заведомо равно нулю
        # if t == 0.: return 0.

        # pass
        return 0.

    @classmethod
    def get_new_status(cls, control_commands: StageControlCommands,
                       previous_status: RealWorldStageStatusN) -> RealWorldStageStatusN:
        """ Возвращает новое состояние ступени

        :param control_commands: управляющие команды на двигатели изделия
        :param previous_status: предыдущее состояние изделия
        :return: Новое состояние изделия - результат действия двигателей
        """
        if control_commands.all_off():
            # Если все двигатели выключены, все силы от двигателей сделать нулевыми
            pass

        duration = CheckPeriod.set_duration(previous_status.position)
        sec_duration = CheckPeriod.to_sec(duration)

        line_axeleration = Moving.get_a(Action(fdownup=VectorComplex.get_instance(0., stage.Engine.mainEngineForce)))
        line_velocity = previous_status.velocity + line_axeleration * sec_duration
        line_position = previous_status.position + line_velocity * sec_duration

        # угловое ускорение
        angular_axeleration = 0.
        # угловая скорость, рад/сек
        angular_velocity = previous_status.angular_velocity + angular_axeleration * sec_duration
        # поворот на угол, рад.
        angle = angular_velocity * sec_duration
        # переводим угол из радианов в форму комплексного числа
        complex_angle = cmath.rect(1., angle)
        # поворот вектора ориентации через перемножение комплексных чисел
        cardanus = previous_status.orientation.cardanus * complex_angle
        # приводим к единичному вектору
        cardanus = cardanus / abs(cardanus)
        # новая ориентация
        orientation = VectorComplex.get_instance_c(cardanus)

        new_position = RealWorldStageStatusN(position=line_position, velocity=line_velocity,
                                             acceleration=line_axeleration, angular_velocity=angular_velocity,
                                             angular_acceleration=angular_axeleration, orientation=orientation)
        new_position.time_stamp = previous_status.time_stamp + duration

        return new_position
