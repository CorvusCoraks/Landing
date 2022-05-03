""" Тренировка нейросети """
# from physics import Rocket
import random

import structures
import tools
from point import VectorComplex
from physics import BigMap
from kill_flags import KillNeuroNetThread
from queue import Queue
from structures import StageControlCommands, RealWorldStageStatusN
from torch import device, cuda, tensor, float, mul, add, sub
from torch.nn.functional import mse_loss
from net import Net


def start_nb(controlQueue: Queue, environmentQueue: Queue, reinforcementQueue: Queue, killThisThread: KillNeuroNetThread, savePath='.\\', actorCheckPointFile='actor.pth.tar', criticCheckPointFile='critic.pth.tar'):
    """ Входная функция для тренировки
        - при локальной тренировке, вызов функции идёт с параметрами по умолчанию.
        - при тренировке через ноутбук, производится установка параметров вызова функции.
    """
    print("Вход в поднить обучения.\n")

    # используемое для обучения устройство
    calc_device = device("cuda:0" if cuda.is_available() else "cpu")
    print(calc_device)

    # предыдущее значение функции ценности выданное нейросетью криктика
    previousQmax = 0.

    # размер батча
    batch_size = 1

    # файлы сохранений
    actorCheckPointFile = savePath + actorCheckPointFile
    criticCheckPointFile = savePath + criticCheckPointFile

    print(actorCheckPointFile, ' || ', criticCheckPointFile)

    # Актор
    # количество входов
    ac_input = 13
    # количество нейронов в скрытом слое
    ac_hidden = ac_input
    # количество выходов
    ac_output = 5
    # количество скрытых слоёв
    ac_layers = 1
    netActor = Net(ac_input, ac_hidden, ac_output, ac_layers, True)

    # размерность ac_input уже включает в себя размерность входных данных плюс один вход на подкрепление
    # Но в данном случае, на вход критика уже подаётся подкрепление ставшее результатом данного шага, а не предыдущего.
    # вход критика = выход актора + вход актора
    cr_input = ac_output + ac_input
    cr_hidden = cr_input
    cr_output = 1
    cr_layers = 1
    netCritic = Net(cr_input, cr_hidden, cr_output, cr_layers, True)


    # объект подкрепления
    # rf = tools.Reinforcement()

    # Загрузка сохранённой НС или сосздание новой

    # Загрузка сохранённых параметров НС

    # инициализация класса проверки на выход за пределы тестового полигона
    finish = tools.Finish()

    # очередное состояние окружающей среды
    environmentStatus = RealWorldStageStatusN()
    # подкрепление для предыдущего состояния ОС
    # prevReinforcement = 0.

    # Подкрепление каждого шага
    reinf = structures.ReinforcementValue(0, 0)

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
            # процесс одной попытки посадить изделие, т. е. перебор состояний в процессе одной посадки
            if killThisThread.kill:
                # если была дана команда на завершение нити
                print("Принудительно завершение поднити обучения внутри испытания.\n")
                break
            # получить предыдущее (начальное) состояние
            while not killThisThread.kill:
                # ждём очередное состояние окружающей среды
                if not environmentQueue.empty():
                    environmentStatus = environmentQueue.get()
                    # состояние окружающей среды получено, выходим из цикла ожидания в цикл обучения
                    break

            # Подготовка входного вектора для актора
            inputActor = actorInputTensor(environmentStatus)

            # проход через актора с получением действий актора
            actorAction = netActor(inputActor)

            # Подготовка входного вектора для критика
            inputCritic = criticInputTensor(environmentStatus, actorAction)
            # проход через критика с использованием ВСЕХ возможных действий в данном состоянии ОС
            # с получением ВСЕХ возможных значений функции ценности
            aLotOfQTensor = netCritic(inputCritic)
            # выбор максимального значения функции ценности
            Qmax = tensor([[1]], dtype=float, requires_grad=True)
            # Отправка команды, согласно максимального значения функции ценности
            random.seed()
            if random.choice([0, 1]):
                # Нейросеть не дала определённого вывода. Команды нет. Двигатели не включать, пропуск такта
                controlQueue.put(StageControlCommands(environmentStatus.timeStamp, duration=0))
            else:
                # Нейросеть актора даёт команду
                controlQueue.put(StageControlCommands(environmentStatus.timeStamp, duration=1000))

            # Ждём появления подкрепления в очереди
            while reinforcementQueue.empty():
                if killThisThread.kill:
                    # если была дана команда на завершение нити
                    print("Принудительно завершение поднити обучения внутри испытания.\n")
                    break
            else:
                reinf = reinforcementQueue.get()
                # Проверка на совпадение отметки времени
                # if environmentStatus.timeStamp
                pass

            if environmentStatus.timeStamp > 0:
                # для нулевого состояния окружающей среды корректировку функции ценности не производим
                # Ошибка критика
                # criticLoss = previousQmax + 0.001*(reinf + 0.01*Qmax - previousQmax)
                criticLoss = add(previousQmax, mul(sub(add(mul(Qmax, 0.01), reinf.reinforcement), previousQmax), 0.001))
                # обратный проход последовательно по критику, а затем по актору
                criticLoss.backward()
                actorAction.backward(actorGradsFromCritic())

                # Оптимизация гиперпараметров нейросетей

                # Функцию ценности превращаем в скаляр, чтобы на следующем проходе, по этой величине не было backward
                previousQmax = Qmax.item()


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

def actorInputTensor(environment: RealWorldStageStatusN):
    """
    Формирует тензор входных параметров актора

    :param environment:
    :return:
    """
    return tensor([[0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0.]], dtype=float)

def criticInputTensor(environment: RealWorldStageStatusN, actorAction: tensor):
    """
    Формирует тензор входныx параметров критика.

    :param environment:
    :param actorOutputVariants:
    :return: [[Состояние ОС, Вариант действия 1],[Состояние ОС, Вариант действия 2],[Состояние ОС, Вариант действия 3]]
    """
    return tensor([[0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 1., 0., 1., 0., 1., 0.,],
                   [0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 1., 0., 1., 0., 1., 0.,]],
                  dtype=float)

def actorGradsFromCritic():
    """
    Метод выделяет градиенты актора с входных параметров критика (после обратного прохода по критику)

    :return:
    """
    return tensor([[0., 1., 0., 1., 0.]], dtype=float)

# вызов при локальном обучении
# start_nb()