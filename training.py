""" Тренировка нейросети """
# from physics import Rocket
import tools
from point import VectorComplex
from physics import RealWorldStageStatus, BigMap
from kill_flags import KillNeuroNetThread
from queue import Queue


def start_nb(controkQueue: Queue, environmentQueue: Queue, killThisThread: KillNeuroNetThread, savePath='.\\', actorCheckPointFile='actor.pth.tar', criticCheckPointFile='critic.pth.tar'):
    """ Входная функция для тренировки
        - при локальной тренировке, вызов функции идёт с параметрами по умолчанию.
        - при тренировке через ноутбук, производится установка параметров вызова функции.
    """
    print("Вход в поднить обучения.\n")
    rf = tools.Reinforcement()
    # rocket = Rocket()
    # генерация начального состояния игры (состояния ступени)
    # startState = generateStartState()

    # Загрузка сохранённой НС или сосздание новой

    # Загрузка сохранённых параметров НС

    # инициализация класса проверки на выход за пределы тестового полигона
    finish = tools.Finish()

    startEpoch = 0
    stopEpochNumber = 2
    # Главный цикл (перебор эпох / перебор игр)
    for epoch in range(startEpoch, stopEpochNumber):
        if killThisThread.kill:
            # если была дана команда на завершение нити
            print("Принудительное завершение поднити обучения по эпохе.\n")
            break

        # Цикл последовательных переходов из одного состояния ОС в другое
        # один проход - один переход
        # while not rf.isLandingFinished(Point(10, 10), 4.):
        # while (not finish.isOneTestFinished(Point(10, 10))) or (not rf.isLandingFinished(Point(10, 10), 4.)):
        while not finish.isOneTestFinished(VectorComplex.getInstance(10, 10)):
            if killThisThread.kill:
                # если была дана команда на завершение нити
                print("Принудительно завершение поднити обучения внутри испытания.\n")
                break
            pass
            # получить предыдущее (начальное) состояние

            # вывод картинки предыдущего (начального) состояния

            # проход через актора с получением действий актора

            # проход через критика с использованием ВСЕХ возможных действий в данном состоянии ОС
            # с получением ВСЕХ возможных значений функции ценности

            # выбор максимального значения функции ценности

            # Целевое значение функции ценности
            targetQtp1 = 0
            if rf.isLandingFinished(VectorComplex.getInstance(10, 10), 4.):
                # На последнем переходе функция ценности стремится к единице (при успешная посадка)
                targetQtp1 = rf.getReinforcement(VectorComplex.getInstance(10, 10), 4.)

            # обратный проход последовательно по критику, а затем по актору
            # Функция потерь считается для варианта выбора максимального значения функции ценности
            # и подкрепления полученного для этого выбора


            # Каждые несколько проходов
            #     Сохранение состояния окружающей среды
            #     Сохранение состояния ступени
            #     Сохранение состояния процесса обучения
            #     Сохранение состяния нейросетей
    print("Выход из поднити обучения.\n")

def generateStartState():
    """
    Генерация начального положения изделия

    :return:
    :rtype RealWorldStageStatus:
    """
    startState = RealWorldStageStatus(position=BigMap.startPointInPoligonCoordinates,
                                  orientation=VectorComplex.getInstance(0., 1.))
    startState.timeStamp = 0.

    return startState

# вызов при локальном обучении
# start_nb()