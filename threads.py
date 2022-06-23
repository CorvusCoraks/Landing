""" Класс нитей и инструментов работы с ними. """
import physics
import tools
from point import VectorComplex
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import Moving
from queue import Queue
import cmath
from tools import Finish, MetaQueue
from threading import Thread
from training import start_nb
from kill_flags import KillNeuroNetThread, KillRealWorldThread, KillCommandsContainer
from structures import StageControlCommands, RealWorldStageStatusN, ReinforcementValue, CloneInterface, CloneFactory
from stage import Sizes, BigMap
from typing import Optional

# Необходима синхронизация обрабатываемых данных в разных нитях.
# Модель реальности:
# 1. датчики ступени считывают данные в момент времени t.
# 2. По разнице показаний датчиков в t и t-1 вычисляются динамические параметры для момента t
# 3. динамические параметры момента t передаются в нить отображения и в нить нейросети
# 4. Окно отображения отображает ситуацию, нейросеть обрабатывает (обучается).
# 5. Указания нейросети передаются в нить физической модели (сила управляющего воздействия)
# 6. В нити физической модели пересчитывается состояние ОС (показания датчиков) для момента t+1 с учётом того,
# что с момента времени t до момента времени t+1 действуют управляющие воздействия из п. 5.
# 7. Переходим к п. 2

# _Примечание_ В каждый момент считывания показаний датчиков, все управляющие воздействия прекращаются
# (т. е. любое управляющее воздействие действует только до следующего момента считывания показаний датчиков)
# _Примечание_ Промежуток времени между считываниями данных t-1, t, t+1 и т. д. постоянный для определённого диапазона
# высот.
# _Примечание_ В НС необходимо передавать ожидаемое время до следующего считывания данных
# (время действия возможного управляющего воздействия)
# _Примечание_ Так как диапазон скорости изделия колеблется от 0 до 8000 м/с, а высота от 0 до 250000 м, необходимо
# при уменьшении высоты увеличить частоту снятия показаний датчиков
# _Примечание_ Так как очереди для передачи данных между нитями независимые, в каждый объект элемента очереди необходимо
# включить поле момента времени (например, в секундах или их долях),
# по которому будут синхронизироваться действия в разных нитях
# _Допущение_ Считаем, что изменение динамических и статических параметров изделия пренебрежимо мало
# за время отработки данных нейросетью.

# class KillNeuroNetThread:
#     """ Флаг-команда завершения нити. """
#     def __init__(self, kill: bool):
#         self.__value = kill
#
#     @property
#     def kill(self):
#         return self.__value
#
#     @kill.setter
#     def kill(self, value: bool):
#         self.__value = value
#
#
# class KillRealWorldThread:
#     """ Флаг-команда завершения нити. """
#     def __init__(self, kill: bool):
#         self.__value = kill
#
#     @property
#     def kill(self):
#         return self.__value
#
#     @kill.setter
#     def kill(self, value: bool):
#         self.__value = value


# class StageStatus:
#     """
#     Параметры ступени в конкретный момент времени в СКИП. Для передачи данных из нити физического моделирования.
#     """
#     # todo Возможно, класс не нужен
#     # максимально возможное значение ежесекундного счётчика
#     # Должно быть БОЛЬШЕ раза в два-три чем размер батча нейросети, чтобы в батче не оказалось одинаковых временных
#     # меток
#     maxCounterValue: int = 1023
#     # максимальное существующее значение счётчика, которое должно быть меньше или равно максимально возможного
#     currentTimerCounter: int = 1023
#
#     def __init__(self, axisVector2d: VectorComplex, positionVector2d: VectorComplex, text: str):
#         """
#
#         :param axisVector2d: осевой вектор
#         :param positionVector2d: позиция центра масс в СКИП
#         :param text: строка дополнительной информации
#         """
#         self.axisVector2d = axisVector2d
#         self.positionVector2d = positionVector2d
#         self.text = text
#         self.timerCounter: int
#         # timerCounter - счётчик ++1, чтобы не путаться с очерёдностью данных.
#         # первое значение счётчика после инициализации первого элемента очереди из 1023 превратится в 0
#         # по достижению максимального значения, следующим шагом счётчик обнуляется
#         # т. е. счётчик идёт от нуля до максимальной величины, обнуляется и цикл повторяется
#         if StageStatus.currentTimerCounter == StageStatus.maxCounterValue:
#             self.timerCounter = StageStatus.currentTimerCounter = 0
#         else:
#
#             StageStatus.currentTimerCounter += 1
#             self.timerCounter = StageStatus.currentTimerCounter


# def reality_thread(queues: MetaQueue, kill: KillCommandsContainer):
#     """
#     Функция моделирующая поведение ступени в реальной физической среде
#     :return:
#     """
#     print("Вход в нить окружающей среды.")
#     finishControl = Finish()
#
#     # начальное состояние ступени в СКИП
#     initialStatus = RealWorldStageStatusN(position=BigMap.startPointInPoligonCoordinates,
#                                           orientation=VectorComplex.get_instance(0., 1.),
#                                           velocity=VectorComplex.get_instance(0., -5.), angular_velocity=-cmath.pi / 36)
#     initialStatus.time_stamp = 0
#
#     physics.previousStageStatus = initialStatus
#
#     # Бутафорская команда для первого прохода
#     command = StageControlCommands(0)
#
#     # пока в тестовых целях сделано через счётчик i
#     # в дальнейшем сделать исключительно через флаги kill
#     i = 0
#     while not kill.reality:
#         # КОД
#         # новое состояние в СКИП
#         newStageStatus = Moving.getNewStatus(command)
#
#         # Отправляем величину подкрепления в НС
#         queues.put(ReinforcementValue(newStageStatus.time_stamp,
#                                       tools.Reinforcement.get_reinforcement(
#                                                       newStageStatus, command)
#                                       )
#                                )
#         # добавить в выходную очередь очередную порцию информации о состоянии ступени
#         queues.put(newStageStatus)
#
#         # КОД
#         if finishControl.is_one_test_failed(newStageStatus.position):
#             # завершение единичного испытания по достижению границ полигона
#             # Факт данного события должен передаваться в нить нейросети
#             # Либо перенести эту проверку в нить нейросети
#             kill.reality = True
#         if i == 80:
#             kill.reality = True
#         i += 1
#
#         while not kill.reality:
#             # ждём команду из нейросети на отправленное состояние
#             if not queues.empty("command"):
#                 command = queues.get("command")
#                 # команда получена
#                 break
#
#         physics.previousStageStatus = newStageStatus
#         print("{0}. Time: {1}, Posititon: {2}, Velocyty: {3},\n Axelerantion: {4}, Orientation: {5}\n".
#               format(i, newStageStatus.time_stamp, newStageStatus.position, newStageStatus.velocity,
#                      newStageStatus. acceleration, newStageStatus.orientation))
#     else:
#         kill.neuro = True
#
#     print("Завершение нити реальности.")

def neuronet_thread(queues: MetaQueue, kill: KillCommandsContainer, initial_status: RealWorldStageStatusN):
    """
    Метод, запускаемый в отдельной нитке для обучения нейросети.

    :param queue: очередь, для передачи даннных
    :return:
    """
    print("Вход в нить нейросети.\n")

    # запуск дочерней нити, так как в этой цикла не предусматривается, а вот в дочерней будет цикл обучения
    # todo возможно, следует вызывать из модуля main сразу функцию обучения как нить, без этой промежуточной
    neuroNetTrainingThread = Thread(target=start_nb, name="neuroNetTraningThread", args=(queues, kill, initial_status))
    # запуск метода обучения сети
    neuroNetTrainingThread.start()

    neuroNetTrainingThread.join()

    print("Завершение нити нейросети.\n")


def reality_thread_2(queues: MetaQueue, kill: KillCommandsContainer, max_tests: int, initial_status: RealWorldStageStatusN):
    """
    Функция моделирующая поведение ступени в реальной физической среде

    :param queues: Контейнер очередей передачи данных.
    :param kill: Контейнер команд на завершение нитей.
    :param max_tests: Количество запланированных испытательных посадок.
    """
    print("Вход в нить окружающей среды.")

    finishControl = Finish()

    # провести указанное число испытательных посадок
    for i in range(max_tests):
        # начальное состояние ступени в СКИП
        # initialStatus = initial_status
        # initialStatus.time_stamp = 0

        # physics.previousStageStatus = initialStatus
        # physics.previousStageStatus = initial_status
        # предыдущее состояние изделия
        previous_stage_status: RealWorldStageStatusN = initial_status
        # Информация о начальном положении изделия отправляется в нити
        queues.put(initial_status)
        # Команда управления на двигатели. В начальном состоянии двигатели не включаются
        # command: StageControlCommands = StageControlCommands(0)

        while not kill.reality:
            # ждём команду для двигателей из нейросети на отправленное начальное состояние
            if not queues.empty("command"):
                command = queues.get("command")
                # команда, ведущая к новому состоянию, получена
                break
        else:
            break

        # цикл последовательной генерации состояний в процессе одной тестовой посадки
        # цикл прерывается, только если во время посадки случилась удача / неудача
        # или поступила команда на заврешение работы программы
        while not finishControl.is_one_test_failed(previous_stage_status.position) and not kill.reality:
            # if physics.previousStageStatus.time_stamp == 0:
            #     newStageStatus = physics.previousStageStatus
            #     reinforcement = ReinforcementValue(newStageStatus.time_stamp, 0)
            # else:
            # новое состояние в СКИП
            newStageStatus = Moving.getNewStatus(command, previous_stage_status)
            # Подкрепление действий системы управления, которые привели к новому состоянию
            reinforcement = ReinforcementValue(newStageStatus.time_stamp,
                                               tools.Reinforcement.get_reinforcement(newStageStatus, command)
                                               )

            # Отправляем величину подкрепления в НС
            queues.put(reinforcement)
            # добавить в выходную очередь очередную порцию информации о состоянии ступени
            queues.put(newStageStatus)

            # если удачная посадка
            if finishControl.is_one_test_success(newStageStatus, tools.Reinforcement.accuracy):
                # переходим к следующему испытанию
                break

            while not kill.reality:
                # ждём команду из нейросети на отправленное состояние и подкрепление
                if not queues.empty("command"):
                    command = queues.get("command")
                    # команда, ведущая к новому состоянию, получена
                    break
            else:
                break

            # physics.previousStageStatus = newStageStatus
            previous_stage_status = newStageStatus
            print("{0}. Time: {1}, Posititon: {2}, Velocyty: {3},\n Axelerantion: {4}, Orientation: {5}\n".
                  format(i, newStageStatus.time_stamp, newStageStatus.position, newStageStatus.velocity,
                         newStageStatus.acceleration, newStageStatus.orientation))

        # прекращаем испытания, завершение программы
        if kill.reality:
            break

    print("Завершение нити реальности.")



