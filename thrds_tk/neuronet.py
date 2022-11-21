from ifc_flow.i_flow import INeuronet
from thrds_tk.threads import AYarn
import random
# import shelve
import structures
from tools import Finish
from carousel.metaque import MetaQueueN
# from point import VectorComplex
from kill_flags import KillCommandsContainer
from structures import StageControlCommands, RealWorldStageStatusN
from torch import device, cuda, tensor, float
from net import Net
from status import ITrainingStateStorage, TrainingStateShelve
from typing import Dict, Any, Optional
# from copy import deepcopy
from time import sleep
from carousel.atrolley import TestId
from con_intr.ifaces import ISocket


class NeuronetThread(INeuronet, AYarn):
    """ Нить нейросети. """
    def __init__(self, name: str, data_socket: ISocket, queues: MetaQueueN, kill: KillCommandsContainer, batch_size: int, savePath='.\\', actorCheckPointFile='actor.pth.tar', criticCheckPointFile='critic.pth.tar'):
        AYarn.__init__(self, name)

        print('Конструктор класса нити нейросети.')

        self.__data_soket = data_socket
        self.__queues = queues
        self.__kill = kill
        self.__batch_size = batch_size

        # файлы сохранений
        self.__actorCheckPointFile = savePath + actorCheckPointFile
        self.__criticCheckPointFile = savePath + criticCheckPointFile

        self.__sleep_time = 0.001

        self.__state_storage: ITrainingStateStorage = TrainingStateShelve()

        self.__state_dict: Dict[str, Any] = self.__state_storage.load_training(default())

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
        self.__calc_device = device("cuda:0" if cuda.is_available() else "cpu")
        print(self.__calc_device)

        # предыдущее значение функции ценности выданное нейросетью криктика
        self.__previousQmax = self.__state_dict['previous_q_max']

        self.__previous_state_time_stamp = 0

        # размер батча
        # batch_size = 1

        print(self.__actorCheckPointFile, ' || ', self.__criticCheckPointFile)

        # Актор
        # количество входов
        self.__ac_input = 13
        # количество нейронов в скрытом слое
        self.__ac_hidden = self.__ac_input
        # количество выходов
        self.__ac_output = 5
        # количество скрытых слоёв
        self.__ac_layers = 1
        self.__netActor = Net(self.__ac_input, self.__ac_hidden, self.__ac_output, self.__ac_layers, True)

        # размерность ac_input уже включает в себя размерность входных данных плюс один вход на подкрепление
        # Но в данном случае, на вход критика уже подаётся подкрепление ставшее результатом данного шага, а не предыдущего.
        # вход критика = выход актора + вход актора
        self.__cr_input = self.__ac_output + self.__ac_input
        self.__cr_hidden = self.__cr_input
        self.__cr_output = 1
        self.__cr_layers = 1
        self.__netCritic = Net(self.__cr_input, self.__cr_hidden, self.__cr_output, self.__cr_layers, True)

        # объект подкрепления
        # rf = tools.Reinforcement()

        # Загрузка сохранённой НС или сосздание новой

        # Загрузка сохранённых параметров НС

        # инициализация класса проверки на выход за пределы тестового полигона
        self.__finish = Finish()

        # очередное состояние окружающей среды
        self.__environmentStatus: RealWorldStageStatusN = RealWorldStageStatusN()
        # environmentStatusA: List[RealWorldStageStatusN]
        # подкрепление для предыдущего состояния ОС
        # prevReinforcement = 0.

        # Информация о подкреплении каждого шага для передачи через очередь
        self.__reinf: structures.ReinforcementValue = structures.ReinforcementValue(0, 0.)

        self.__startEpoch = 0
        self.__stopEpochNumber = 2

    def initialization(self) -> None:
        pass

    def run(self) -> None:
        pass

    def _yarn_run(self, *args, **kwargs) -> None:
        while not self.__kill.neuro:
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

            test_id: TestId = 0

            is_initial_forward = False

            for i in range(self.__batch_size):
                # Получить из очереди начальное положение изделия
                while not self.__kill.neuro:
                    # ждём появления начального состояния окружающей среды в очереди
                    if self.__queues.state_to_neuronet.has_new_cargo():
                        test_id, _ = self.__queues.state_to_neuronet.unload(self.__environmentStatus)
                        is_initial_forward = True
                        # состояние окружающей среды получено, выходим из цикла ожидания в цикл обучения
                        break
                    sleep(self.__sleep_time)
                else:
                    print("Принудительное завершение поднити нейросети во время ожидания начального состояния.\n")
                    break

                # todo состостояния из окружающей среды из очереди выходят - проверено!
                print(test_id, self.__environmentStatus.position)

            # Цикл последовательных переходов из одного состояния ОС в другое
            # один проход - один переход
            while not self.__finish.is_one_test_failed(self.__environmentStatus.position) and not self.__kill.neuro:
                # if kill.neuro:
                #     # если была дана команда на завершение нити
                #     print("Принудительно завершение поднити обучения внутри испытания.\n")
                #     break

                # получить предыдущее (начальное) состояние

                # environmentStatus = wait_data_from_queue(kill.neuro, queues, 'neuro')
                # if environmentStatus is None: break

                print('Нейросеть: вход в цикл прямого прохода по нейросети.')

                if not is_initial_forward:
                    # Для нулевого состояния повторный вход в данный цикл - лишнее.
                    # Данный цикл актуален только для ненулевых состояний.
                    while not self.__kill.neuro:
                        # ждём очередное состояние окружающей среды
                        if self.__queues.state_to_neuronet.has_new_cargo():
                            test_id, _ = self.__queues.state_to_neuronet.unload(self.__environmentStatus)
                            # состояние окружающей среды получено, выходим из цикла ожидания в цикл обучения
                            break
                        sleep(self.__sleep_time)
                    else:
                        # Если в цикле ожидания очередного состояния ОС появился приказ на завершение нити обучения
                        print("Принудительно завершение поднити обучения внутри испытания.\n")
                        break

                # Подготовка входного вектора для актора
                inputActor = actorInputTensor(self.__environmentStatus)

                # проход через актора с получением действий актора
                actorAction = self.__netActor(inputActor)

                # Подготовка входного вектора для критика
                inputCritic = criticInputTensor(self.__environmentStatus, actorAction)
                # проход через критика с использованием ВСЕХ возможных действий в данном состоянии ОС
                # с получением ВСЕХ возможных значений функции ценности
                aLotOfQTensor = self.__netCritic(inputCritic)
                # выбор максимального значения функции ценности
                Qmax = tensor([[1]], dtype=float, requires_grad=True)
                # Отправка команды, согласно максимального значения функции ценности
                # Пока случайным образом в тестовых целях, чтобы работало.
                random.seed()
                if random.choice([0, 1]):
                    # Нейросеть не дала определённого вывода. Команды нет. Двигатели не включать, пропуск такта
                    # queues.put(StageControlCommands(environmentStatus.time_stamp))
                    self.__queues.command_to_real.load(test_id, StageControlCommands(self.__environmentStatus.time_stamp))
                else:
                    # Нейросеть актора даёт команду
                    # queues.put(StageControlCommands(environmentStatus.time_stamp, main=True))
                    self.__queues.command_to_real.load(test_id, StageControlCommands(self.__environmentStatus.time_stamp, main=True))

                if is_initial_forward:
                    # Получили максимальное значение функции ценности для нулевого состояния.
                    # Отправили в физ. модель команды для двигателей для нулевого состояния.
                    # Больше ничего мы для него сделать не можем, переходим сразу к ожиданию следующего состояния ОС.
                    self.__previousQmax = Qmax.item()
                    # continue

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
                while not self.__kill.neuro:
                    if self.__queues.reinf_to_neuronet.has_new_cargo():
                        self.__queues.reinf_to_neuronet.unload(self.__reinf)
                        break
                else:
                    # если была дана команда на завершение нити
                    print("Принудительно завершение поднити обучения внутри испытания.\n")
                    break
                #
                # # while not kill.neuro:
                # #     if not queues.empty("reinf"):
                # #         reinf = queues.get("reinf")
                # #         break
                # # else:
                # #     # если была дана команда на завершение нити
                # #     print("Принудительно завершение поднити обучения внутри испытания.\n")
                # #     break
                #
                # # while not reinforcementQueue.empty():
                # #     reinf = reinforcementQueue.get()
                # #     # Проверка на совпадение отметки времени
                # #     # if environmentStatus.time_stamp
                # #     if killThisThread.kill:
                # #         # если была дана команда на завершение нити
                # #         print("Принудительно завершение поднити обучения внутри испытания.\n")
                # #         break
                #
                # # if environmentStatus.time_stamp > 0:
                # #     # для нулевого состояния окружающей среды корректировку функции ценности не производим
                #
                # # Ошибка критика
                # # criticLoss = previousQmax + 0.001*(reinf + 0.01*Qmax - previousQmax)
                # criticLoss = add(previousQmax, mul(sub(add(mul(Qmax, 0.01), reinf.reinforcement), previousQmax), 0.001))
                # # обратный проход последовательно по критику, а затем по актору
                # criticLoss.backward()
                # actorAction.backward(actorGradsFromCritic())
                #
                # # Оптимизация гиперпараметров нейросетей
                #
                # # Функцию ценности превращаем в скаляр, чтобы на следующем проходе, по этой величине не было backward
                # previousQmax = Qmax.item()
                #
                #
                is_initial_forward = False
                # # Каждые несколько проходов
                # #     Сохранение состояния окружающей среды
                # #     Сохранение состояния ступени
                # #     Сохранение состояния процесса обучения
                # #     Сохранение состяния нейросетей

            self.__state_storage.save_training({
                'start_epoch': 0,
                'current_epoch': 0,
                'stop_epoch': 2,
                'previous_q_max': 0
            })


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


