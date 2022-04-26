""" Тренировка нейросети """
# from physics import Rocket
import tools
from point import VectorComplex
from physics import BigMap
from kill_flags import KillNeuroNetThread
from queue import Queue
from sructures import StageControlCommands, RealWorldStageStatusN


def start_nb(controlQueue: Queue, environmentQueue: Queue, killThisThread: KillNeuroNetThread, savePath='.\\', actorCheckPointFile='actor.pth.tar', criticCheckPointFile='critic.pth.tar'):
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

    # очередное состояние окружающей среды
    environmentStatus = RealWorldStageStatusN()

    startEpoch = 0
    stopEpochNumber = 2
    # Главный цикл (перебор эпох / перебор игр)
    for epoch in range(startEpoch, stopEpochNumber):
        # Одна эпоха - один эксперимент до посадки?
        if killThisThread.kill:
            # если была дана команда на завершение нити
            print("Принудительное завершение поднити обучения по эпохе.\n")
            break

        # Цикл последовательных переходов из одного состояния ОС в другое
        # один проход - один переход
        while not finish.isOneTestFinished(VectorComplex.getInstance(0, 150)):
            # процесс одной попытки посадить изделие
            if killThisThread.kill:
                # если была дана команда на завершение нити
                print("Принудительно завершение поднити обучения внутри испытания.\n")
                break
            pass
            # получить предыдущее (начальное) состояние
            while not killThisThread.kill:
                # ждём очередное состояние окружающей среды
                if not environmentQueue.empty():
                    environmentStatus = environmentQueue.get()
                    # состояние окружающей среды получено, выходим из цикла ожидания в цикл обучения
                    break

            # вывод картинки предыдущего (начального) состояния

            # проход через актора с получением действий актора

            # проход через критика с использованием ВСЕХ возможных действий в данном состоянии ОС
            # с получением ВСЕХ возможных значений функции ценности

            # выбор максимального значения функции ценности

            # Отправка команды, согласно максимального значения функции ценности
            controlQueue.put(StageControlCommands(environmentStatus.timeStamp, duration=1))

            # Целевое значение функции ценности
            targetQtp1 = 0
            # if rf.isLandingFinished(VectorComplex.getInstance(10, 10), 4.):
            #     # На последнем переходе функция ценности стремится к единице (при успешная посадка)
            #     targetQtp1 = rf.getReinforcement(VectorComplex.getInstance(10, 10), 4.)

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
    startState = RealWorldStageStatusN(position=BigMap.startPointInPoligonCoordinates,
                                  orientation=VectorComplex.getInstance(0., 1.))
    startState.timeStamp = 0

    return startState

# вызов при локальном обучении
# start_nb()