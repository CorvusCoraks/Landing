from logging import getLogger
from basics import logger_name, TestId, FinishAppException, SLEEP_TIME
from ifc_flow.i_flow import INeuronet
from thrds_tk.threads import AYarn
import random
# import shelve
import structures
from tools import Finish
from structures import StageControlCommands, RealWorldStageStatusN
from torch import device, cuda, tensor, float
from net import Net
from typing import Dict, Any, Optional, Callable
from time import sleep
from con_intr.ifaces import ISocket, ISender, IReceiver, AppModulesEnum, DataTypeEnum
from con_simp.contain import Container, BioContainer
from con_simp.wire import ReportWire
from nn_iface.ifaces import InterfaceStorage, InterfaceNeuronNet, ProcessStateInterface, InterfaceACCombo
from nn_iface.store_nn import ModuleStorage, ActorAndCritic
from nn_iface.store_st import StateStorage, State

logger = getLogger(logger_name+'.neuronet')
Inbound = Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]]
Outbound = Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]]

class NeuronetThread(INeuronet, AYarn):
    """ Нить нейросети. """
    def __init__(self, name: str, data_socket: ISocket, max_tests: int, batch_size: int, savePath='.\\', actorCheckPointFile='actor.pth.tar', criticCheckPointFile='critic.pth.tar'):
        AYarn.__init__(self, name)

        logger.info('Конструктор класса нити нейросети. {}.__init__'.format(self.__class__.__name__))

        self.__inbound: Inbound = data_socket.get_in_dict()
        self.__outbound: Outbound = data_socket.get_out_dict()

        self.__max_tests = max_tests

        # Объекты для работы по новой структуре вычислительного блока
        # Имя испытания нейросети
        self.__model_name = "first"
        # Хранилища для модуля НС
        self.__load_storage_model: InterfaceStorage = ModuleStorage(self.__model_name)
        self.__save_storage_model: InterfaceStorage = self.__load_storage_model
        # Хранилище для состояния процесса обучения.
        self.__load_storage_training_state: InterfaceStorage = StateStorage(self.__model_name)
        self.__save_storage_training_state: InterfaceStorage = self.__load_storage_training_state
        # Хранилище для состояния НС
        self.__load_storage_model_state: InterfaceStorage = self.__load_storage_training_state
        self.__save_storage_model_state: InterfaceStorage = self.__load_storage_training_state

        self.__training_state: ProcessStateInterface = State()
        self.__two_nn: InterfaceACCombo = ActorAndCritic()

        # Загрузка
        try:
            self.__training_state.load(self.__load_storage_training_state)
        except FileNotFoundError:
            # Задание начальных состояний для параметров испытаний.
            self.__training_state.batch_size = 1
            self.__training_state.epoch_start = 0
            self.__training_state.epoch_current = 0
            self.__training_state.epoch_stop = 2
            self.__training_state.prev_q_max = 0

        try:
            self.__two_nn.load(self.__load_storage_model)
        except FileNotFoundError:
            # Создание нейросетей.
            pass

        # используемое для обучения устройство
        self.__calc_device = device("cuda:0" if cuda.is_available() else "cpu")
        logger.debug('{}'.format(self.__calc_device))

        self.__previous_state_time_stamp = 0

        # logger.debug('{} || {}'.format(self.__actorCheckPointFile, self.__criticCheckPointFile))

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
        # self.__environmentStatus: RealWorldStageStatusN = RealWorldStageStatusN()
        # environmentStatusA: List[RealWorldStageStatusN]
        # подкрепление для предыдущего состояния ОС
        # prevReinforcement = 0.

        # Информация о подкреплении каждого шага для передачи через очередь
        self.__reinf: structures.ReinforcementValue = structures.ReinforcementValue(0, 0.)

    def initialization(self) -> None:
        pass

    def run(self) -> None:
        pass

    def __finish_app_checking(self, inbound: Inbound) -> None:
        """ Метод проверяет на появление в канале связи команды на заврешение приложения. """
        # Если команда на завершение приложения есть
        if inbound[AppModulesEnum.VIEW][DataTypeEnum.APP_FINISH].has_incoming():
            # Получаем эту команду
            inbound[AppModulesEnum.VIEW][DataTypeEnum.APP_FINISH].receive()
            # Возбуждаем исключение завершения приложения.
            raise FinishAppException
        # return False

    def __get_remaining_tests(self, inbound: Inbound, sleep_time: float, finish_app_checking: Callable[[Inbound], None]) -> int:
        """ Получить оставшееся количество запланированных испытаний. """
        while not inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].has_incoming():
            # Пока в канале нет сообщений, крутимся в цикле ожидания.
            sleep(sleep_time)
            finish_app_checking(inbound)

        # Дождались сообщения
        container = inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].receive()
        remaining_tests: int = container.unpack()
        return remaining_tests

    def __collect_batch(self, inbound: Inbound, sleep_time: float,
                        finish_app_checking: Callable[[Inbound], None], batch_size: int) \
            -> Dict[TestId, RealWorldStageStatusN]:
        """ Собрать словарь-контейнер-накопитель для состояний изделия в разных испытаниях для создания батча. """
        # Результирующий словарь
        batch_dict: Dict[TestId, RealWorldStageStatusN] = {}
        for i in range(batch_size):
            # Отсчитываем количество, в зависимости от планируемого размера батча
            while not inbound[AppModulesEnum.PHYSICS][DataTypeEnum.STAGE_STATUS].has_incoming():
                # Крутимся в цикле в ожидании данных в канале.
                sleep(sleep_time)
                finish_app_checking(inbound)

            # Есть порция данных
            container = inbound[AppModulesEnum.PHYSICS][DataTypeEnum.STAGE_STATUS].receive()
            assert isinstance(container, BioContainer), \
                "Container class should be a BioContainer. But now is {}".format(container.__class__)
            test_id, _ = container.get()
            stage_status = container.unpack()
            # test_id, stage_status = container.get(), container.unpack()
            # Пополняем словарь
            batch_dict[test_id] = stage_status

        return batch_dict

    def _yarn_run(self, *args, **kwargs) -> None:
        # Вечный цикл. Выход из него по команде на завершение приложения.
        while True:
            try:
                # Оставшееся количество запланированных испытаний.
                remaining_tests: int = self.__get_remaining_tests(self.__inbound, SLEEP_TIME, self.__finish_app_checking)
                # Если размер планируемого батча больше полного планируемого количества испытаний, то будем формировать
                # батч размером в полное планируемое количество испытаний.
                self.__training_state.batch_size = self.__training_state.batch_size if self.__training_state.batch_size <= remaining_tests else remaining_tests

                # Отправляем в модуль физической модели число испытаний, которое хочет получить данный модуль.
                report_wire = self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].get_report_sender()
                assert isinstance(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS], ReportWire), \
                    'Data wire for remaining tests info should be a ReportWire class. But now is {}'.\
                        format(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].__class__)
                report_wire.send(Container(cargo=self.__training_state.batch_size))

                # Сформировать словарь состояний изделия в различных испытаниях.
                batch_dict: Dict[TestId, RealWorldStageStatusN] = \
                    self.__collect_batch(self.__inbound, SLEEP_TIME,
                                         self.__finish_app_checking, self.__training_state.batch_size)

                # сформировать батч-тензор для ввода в актора из состояний N испытаний

                # получить тензор выхода (действий/команд) актора для каждого из N испытаний

                # сформировать батч-тензор для ввода в критика из NхV вариантов, где N-количество испытаний
                # на входе в актора, V - количество вариантов действий актора (количество вариантов включений двигателей)
                # Если батч-тензор на входе в актора состоит из 10 испытаний, количество вариантов
                # включения двигателей - 20, то на вход в критика пойдёт тензор размером 10 х 20, т. е. 200 векторов

                # Получить тензор значений функции ценности на выходе из критика размерностью NхV

                # Для каждого из N испытаний выбрать максимальное значение функции ценности из соответствующих V вариантов.

                # Варианты действий актора, которые соответствуют выбранным максимальным N значениям функции ценности,
                # принять к исполнению и получить подкрепление на выбранные действия.

                # # Отправка команды, согласно максимального значения функции ценности
                # # Пока случайным образом в тестовых целях, чтобы работало.
                for key in batch_dict:
                    # Проходимся по словарю/массиву/тензору комманд
                    # И отправляем их поочерёдно в модуль физической модели.
                    #
                    # Пока вот выбрано случайным образом в тестовых целях, чтобы работало.
                    # И вместо реальных команд нолик и единица.
                    random.seed()
                    if random.choice([0, 1]):
                        # Нейросеть не дала определённого вывода. Команды нет. Двигатели не включать, пропуск такта
                        self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(Container(key, StageControlCommands(0)))
                    else:
                        # Нейросеть актора даёт команду
                        self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(Container(key, StageControlCommands(1)))

                # Рассчитать ошибку на основании выбранных N максимальных значений функции ценности
                # и N полученных подкреплений.

                # Произвести корректировку гиперпараметров нейросети методом обратного распространения ошибки.

                # self.__state_storage.save_training({
                #     'start_epoch': 0,
                #     'current_epoch': 0,
                #     'stop_epoch': 2,
                #     'previous_q_max': 0
                # })

                # Сохранение по новым интерфейсам.
                self.__training_state.save(self.__save_storage_training_state)
                self.__two_nn.save(self.__save_storage_model_state)

            except FinishAppException:
                # Поступила команда на завершение приложения.
                #
                self.__training_state.save(self.__save_storage_training_state)
                self.__two_nn.save(self.__save_storage_model)
                logger.info('Нейросеть. Поступила команда на завершение приложения. Завершаем нить.')
                break

        # while not self.__kill.neuro:
        #
        #     logger.info('Нейросеть: Перед входом в цикл прямого прохода по нейросети.')
        #     # Цикл последовательных переходов из одного состояния ОС в другое
        #     # один проход - один переход
        #     # while not self.__finish.is_one_test_failed(self.__environmentStatus.position) and not self.__kill.neuro:
        #     while not self.__kill.neuro:
        #         # if kill.neuro:
        #         #     # если была дана команда на завершение нити
        #         #     print("Принудительно завершение поднити обучения внутри испытания.\n")
        #         #     break
        #
        #         # получить предыдущее (начальное) состояние
        #
        #         # environmentStatus = wait_data_from_queue(kill.neuro, queues, 'neuro')
        #         # if environmentStatus is None: break
        #
        #         if not is_initial_forward:
        #
        #         # # Подготовка входного вектора для актора
        #         # inputActor = actorInputTensor(self.__environmentStatus)
        #         #
        #         # # проход через актора с получением действий актора
        #         # actorAction = self.__netActor(inputActor)
        #         #
        #         # # Подготовка входного вектора для критика
        #         # inputCritic = criticInputTensor(self.__environmentStatus, actorAction)
        #         # # проход через критика с использованием ВСЕХ возможных действий в данном состоянии ОС
        #         # # с получением ВСЕХ возможных значений функции ценности
        #         # aLotOfQTensor = self.__netCritic(inputCritic)
        #         # # выбор максимального значения функции ценности
        #         # Qmax = tensor([[1]], dtype=float, requires_grad=True)
        #         # # Отправка команды, согласно максимального значения функции ценности
        #         # # Пока случайным образом в тестовых целях, чтобы работало.
        #         for key in batch_dict:
        #             # Проходимся по словарю/массиву/тензору комманд
        #             # И отправляем их поочерёдно в модуль физической модели.
        #             # Пока вот выбранно случайным образом в тестовых целях, чтобы работало.
        #             # И вместо реальных команд нолик и единица.
        #             random.seed()
        #             if random.choice([0, 1]):
        #                 # Нейросеть не дала определённого вывода. Команды нет. Двигатели не включать, пропуск такта
        #                 # self.__queues.command_to_real.load(test_id, StageControlCommands(self.__environmentStatus.time_stamp))
        #                 self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(Container(test_id, 0))
        #             else:
        #                 # Нейросеть актора даёт команду
        #                 # self.__queues.command_to_real.load(test_id, StageControlCommands(self.__environmentStatus.time_stamp, main=True))
        #                 self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(Container(test_id, 1))
        #
        #         # if is_initial_forward:
        #         #     # Получили максимальное значение функции ценности для нулевого состояния.
        #         #     # Отправили в физ. модель команды для двигателей для нулевого состояния.
        #         #     # Больше ничего мы для него сделать не можем, переходим сразу к ожиданию следующего состояния ОС.
        #         #     self.__previousQmax = Qmax.item()
        #         #     # continue
        #         #
        #         # # Ждём появления подкрепления в очереди
        #         # while not self.__kill.neuro:
        #         #     if self.__queues.reinf_to_neuronet.has_new_cargo():
        #         #         self.__queues.reinf_to_neuronet.unload(self.__reinf)
        #         #         break
        #         # else:
        #         #     # если была дана команда на завершение нити
        #         #     logger.info("Принудительно завершение поднити обучения внутри испытания.")
        #         #     break
        #
        #         #
        #         # # while not kill.neuro:
        #         # #     if not queues.empty("reinf"):
        #         # #         reinf = queues.get("reinf")
        #         # #         break
        #         # # else:
        #         # #     # если была дана команда на завершение нити
        #         # #     print("Принудительно завершение поднити обучения внутри испытания.\n")
        #         # #     break
        #         #
        #         # # while not reinforcementQueue.empty():
        #         # #     reinf = reinforcementQueue.get()
        #         # #     # Проверка на совпадение отметки времени
        #         # #     # if environmentStatus.time_stamp
        #         # #     if killThisThread.kill:
        #         # #         # если была дана команда на завершение нити
        #         # #         print("Принудительно завершение поднити обучения внутри испытания.\n")
        #         # #         break
        #         #
        #         # # if environmentStatus.time_stamp > 0:
        #         # #     # для нулевого состояния окружающей среды корректировку функции ценности не производим
        #         #
        #         # # Ошибка критика
        #         # # criticLoss = previousQmax + 0.001*(reinf + 0.01*Qmax - previousQmax)
        #         # criticLoss = add(previousQmax, mul(sub(add(mul(Qmax, 0.01), reinf.reinforcement), previousQmax), 0.001))
        #         # # обратный проход последовательно по критику, а затем по актору
        #         # criticLoss.backward()
        #         # actorAction.backward(actorGradsFromCritic())
        #         #
        #         # # Оптимизация гиперпараметров нейросетей
        #         #
        #         # # Функцию ценности превращаем в скаляр, чтобы на следующем проходе, по этой величине не было backward
        #         # previousQmax = Qmax.item()
        #
        #         #
        #         #
        #         is_initial_forward = False
        #         # # Каждые несколько проходов
        #         # #     Сохранение состояния окружающей среды
        #         # #     Сохранение состояния ступени
        #         # #     Сохранение состояния процесса обучения
        #         # #     Сохранение состяния нейросетей
        #
        #     self.__state_storage.save_training({
        #         'start_epoch': 0,
        #         'current_epoch': 0,
        #         'stop_epoch': 2,
        #         'previous_q_max': 0
        #     })


def load_nn(nn: InterfaceNeuronNet, storage: InterfaceStorage):
    pass

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
    # todo убрать за ненадобностью
    default_dict: Optional[Dict[str, Any]] = {}
    default_dict['start_epoch'] = 0
    default_dict['current_epoch'] = 0
    default_dict['stop_epoch'] = 2
    default_dict['previous_q_max'] = 0
    return default_dict


