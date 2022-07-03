""" Тренировка нейросети """
# from physics import Rocket
import random
import shelve
# from builtins import function

import structures
from tools import Finish, ones_and_zeros_variants_f, MetaQueue
from point import VectorComplex
# from physics import BigMap
from kill_flags import KillNeuroNetThread, KillCommandsContainer
# from queue import Queue
from structures import StageControlCommands, RealWorldStageStatusN, QueueContent
from torch import device, cuda, tensor, float, mul, add, sub
# from torch.nn.functional import mse_loss
from net import Net
# from shelve import open, Shelf
# from stage import BigMap
from status import ITrainingStateStorage, TrainingStateShelve
from typing import Dict, Any, Optional, Union, Tuple
from copy import deepcopy


def start_nb(queues: MetaQueue, kill: KillCommandsContainer, initial_status: RealWorldStageStatusN, savePath='.\\', actorCheckPointFile='actor.pth.tar', criticCheckPointFile='critic.pth.tar'):
    """ Входная функция для тренировки
        - при локальной тренировке, вызов функции идёт с параметрами по умолчанию.
        - при тренировке через ноутбук, производится установка параметров вызова функции.
    """
    print("Вход в поднить обучения.\n")

    state_storage: ITrainingStateStorage = TrainingStateShelve()

    state_dict: Dict[str, Any] = state_storage.load_training(default())

    # shelveFilename = "shelve"
    # with shelve.open(shelveFilename) as sh:
    #     shKeys = sh.keys()
    #     if "9_50_v" in shKeys:
    #         # Ключ найден, прочесть значение.
    #         criticBlank = sh["9_50_v"]
    #     else:
    #         # Ключ не найден. Создать значение.
    #         sh["9_50_v"] = ones_and_zeros_variants_f(8, 3)
    #         criticBlank = sh["9_50_v"]


    # используемое для обучения устройство
    calc_device = device("cuda:0" if cuda.is_available() else "cpu")
    print(calc_device)

    # предыдущее значение функции ценности выданное нейросетью криктика
    previousQmax = state_dict['previous_q_max']

    previous_state_time_stamp = 0

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
    finish = Finish()

    # очередное состояние окружающей среды
    environmentStatus: RealWorldStageStatusN
    # подкрепление для предыдущего состояния ОС
    # prevReinforcement = 0.

    # Информация о подкреплении каждого шага для передачи через очередь
    reinf: structures.ReinforcementValue

    startEpoch = 0
    stopEpochNumber = 2
    # Главный цикл (перебор эпох / перебор игр)
    # for epoch in range(startEpoch, stopEpochNumber):
    while not kill.neuro:
        # if kill.neuro:
        #     # если была дана команда на завершение нити
        #     print("Принудительное завершение поднити обучения по эпохе.\n")
        #     break

        # фиктивное значение начального состояния изделия, необходимое только для того,
        # чтобы запустился цикл прохода по процессу одной посадки
        # environmentStatus = RealWorldStageStatusN(position=VectorComplex.get_instance(0, 450))
        # environmentStatus = initial_status_obj
        # Получить из очереди начальное положение изделия
        # environmentStatus = wait_data_from_queue(kill.neuro, queues, 'neuro')
        # if environmentStatus is None: break

        # Получить из очереди начальное положение изделия
        while not kill.neuro:
            # ждём появления начального состояния окружающей среды в очереди
            if not queues.empty("neuro"):
                environmentStatus = queues.get("neuro")
                # состояние окружающей среды получено, выходим из цикла ожидания в цикл обучения
                break
        else:
            print("Принудительное завершение поднити нейросети во время ожидания начального состояния.\n")
            break

        # Цикл последовательных переходов из одного состояния ОС в другое
        # один проход - один переход
        while not finish.is_one_test_failed(environmentStatus.position) and not kill.neuro:
            # if kill.neuro:
            #     # если была дана команда на завершение нити
            #     print("Принудительно завершение поднити обучения внутри испытания.\n")
            #     break

            # получить предыдущее (начальное) состояние

            # environmentStatus = wait_data_from_queue(kill.neuro, queues, 'neuro')
            # if environmentStatus is None: break

            if environmentStatus.time_stamp != 0:
                # Для нулевого состояния повторный вход в данный цикл - лишнее.
                # Данный цикл актуален только для ненулевых состояний.
                while not kill.neuro:
                    # ждём очередное состояние окружающей среды
                    if not queues.empty("neuro"):
                        environmentStatus = queues.get("neuro")
                        # состояние окружающей среды получено, выходим из цикла ожидания в цикл обучения
                        break
                else:
                    # Если в цикле ожидания очередного состояния ОС появился приказ на завершение нити обучения
                    print("Принудительно завершение поднити обучения внутри испытания.\n")
                    break

            # if environmentStatus.time_stamp < previous_state_time_stamp:
            #     # Новая отметка времени вдруг стала РАНЬШЕ, чем отметка времени предыдущего состояния.
            #     # Это означает, что предыдущая попытка посадки изделия завершилась и началась новая.
            #     previousQmax = 0.
            #     pass

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
            # Пока случайным образом в тестовых целях, чтобы работало.
            random.seed()
            if random.choice([0, 1]):
                # Нейросеть не дала определённого вывода. Команды нет. Двигатели не включать, пропуск такта
                queues.put(StageControlCommands(environmentStatus.time_stamp))
            else:
                # Нейросеть актора даёт команду
                queues.put(StageControlCommands(environmentStatus.time_stamp, main=True))

            if environmentStatus.time_stamp == 0:
                # Получили максимальное значение функции ценности для нулевого состояния.
                # Отправили в физ. модель команды для двигателей для нулевого состояния.
                # Больше ничего мы для него сделать не можем, переходим сразу к ожиданию следующего состояния ОС.
                previousQmax = Qmax.item()
                continue

            # # Ждём появления подкрепления в очереди
            # while reinforcementQueue.empty():
            #     if killThisThread.kill:
            #         # если была дана команда на завершение нити
            #         print("Принудительно завершение поднити обучения внутри испытания.\n")
            #         break
            # else:
            #     reinf = reinforcementQueue.get()
            #     # Проверка на совпадение отметки времени
            #     # if environmentStatus.time_stamp
            #     pass

            # Ждём появления подкрепления в очереди
            while not kill.neuro:
                if not queues.empty("reinf"):
                    reinf = queues.get("reinf")
                    break
            else:
                # если была дана команда на завершение нити
                print("Принудительно завершение поднити обучения внутри испытания.\n")
                break

            # while not reinforcementQueue.empty():
            #     reinf = reinforcementQueue.get()
            #     # Проверка на совпадение отметки времени
            #     # if environmentStatus.time_stamp
            #     if killThisThread.kill:
            #         # если была дана команда на завершение нити
            #         print("Принудительно завершение поднити обучения внутри испытания.\n")
            #         break

            # if environmentStatus.time_stamp > 0:
            #     # для нулевого состояния окружающей среды корректировку функции ценности не производим

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

        state_storage.save_training({
            'start_epoch': 0,
            'current_epoch': 0,
            'stop_epoch': 2,
            'previous_q_max': 0
        })
    print("Выход из поднити обучения.\n")

# def generateStartState():
#     """
#     Генерация начального положения изделия
#
#     :return:
#     :rtype RealWorldStageStatus:
#     """
#     startState = RealWorldStageStatusN(position=BigMap.startPointInPoligonCoordinates,
#                                   orientation=VectorComplex.get_instance(0., 1.))
#     startState.time_stamp = 0
#
#     return startState

# def wait_data_from_queue(flag: function, queues: MetaQueue, queue_name: str, commment='') -> Optional[QueueContent]:
#     while not flag:
#         if not queues.empty(queue_name):
#             return queues.get(queue_name)
#     else:
#         if len(commment) != 0:
#             print(commment)
#         return None

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

def default() -> Dict[str, Any]:
    """ Значения по умолчанию. """
    default_dict: Optional[Dict[str, Any]] = {}
    default_dict['start_epoch'] = 0
    default_dict['current_epoch'] = 0
    default_dict['stop_epoch'] = 2
    default_dict['previous_q_max'] = 0
    return default_dict

# вызов при локальном обучении
# start_nb()