import importlib
from logging import getLogger
from basics import logger_name, TestId, FinishAppException, SLEEP_TIME, ZeroOne, QUEUE_OBJECT_TYPE_ERROR
from basics import Dict_key, Q_est_value, Index_value
from ifc_flow.i_flow import INeuronet
from thrds_tk.threads import AYarn
import random
# import shelve
import structures
from structures import StageControlCommands, RealWorldStageStatusN, ReinforcementValue
from torch import device, tensor, float, Tensor
from typing import Dict, Any, Optional, Callable, List
from time import sleep
from con_intr.ifaces import ISocket, ISender, IReceiver, AppModulesEnum, DataTypeEnum
from con_simp.contain import Container, BioContainer
from con_simp.wire import ReportWire
from nn_iface.ifaces import InterfaceStorage, InterfaceNeuronNet, ProjectInterface
# from DevTmpPr.project import ProjectMainClass
from tools import q_est_init
from app_cfg import PROJECT_DIRECTORY_NAME, PROJECT_PY_NAME, PROJECT_MAIN_CLASS

# project_module = importlib.import_module('{}.{}'.format(PROJECT_DIRECTORY_NAME, PROJECT_PY_NAME))
# project_class = eval('module.{}'.format(PROJECT_MAIN_CLASS))

# eval('from {}.{} import {}'.format(PROJECT_DIRECTORY_NAME, PROJECT_PY_NAME, PROJECT_MAIN_CLASS))

logger = getLogger(logger_name + '.neuronet')
Inbound = Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]]
Outbound = Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]]


class NeuronetThread(INeuronet, AYarn):
    """ Нить нейросети. """

    def __init__(self, name: str, data_socket: ISocket, max_tests: int,
                 batch_size: int, savePath='.\\', actorCheckPointFile='actor.pth.tar',
                 criticCheckPointFile='critic.pth.tar'):
        AYarn.__init__(self, name)

        logger.info('Конструктор класса нити нейросети. {}.__init__'.format(self.__class__.__name__))

        self.__inbound: Inbound = data_socket.get_in_dict()
        self.__outbound: Outbound = data_socket.get_out_dict()
        # self.__type_match: Callable[]

        self.__max_tests = max_tests

        # тестируемый проект
        # self.__project: ProjectInterface = ProjectMainClass()
        # RunTime импортирование модуля с проектом.
        project_module = importlib.import_module('{}.{}'.format(PROJECT_DIRECTORY_NAME, PROJECT_PY_NAME))
        # Создание объекта на основании класса проекта.
        self.__project: ProjectInterface = eval('project_module.{}()'.format(PROJECT_MAIN_CLASS))

        self.__project.load_nn()

        self.__project.load_state()

        self.__calc_device = device(self.__project.device)
        logger.debug('{}'.format(self.__calc_device))

        self.__previous_state_time_stamp = 0

        # Q_estimate - предыдущая оценка ф-ции ценности действия
        self.__q_est: Dict[TestId, ZeroOne] = {}

        # Список, порядок которого соответствует порядку векторов во входном тензоре актора.
        # (Так как порядок элементов в словарях непредсказуем)
        # self.__s_order: List[TestId] = []

        # logger.debug('{} || {}'.format(self.__actorCheckPointFile, self.__criticCheckPointFile))

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

    def __get_remaining_tests(self, inbound: Inbound, sleep_time: float,
                              finish_app_checking: Callable[[Inbound], None]) -> int:
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

            # Пополняем словарь
            batch_dict[test_id] = stage_status

        return batch_dict

    def _q_est_actual(self, s: Dict[TestId, RealWorldStageStatusN], q_est: Dict[TestId, ZeroOne]) \
            -> Dict[TestId, ZeroOne]:
        """ Метод актуализации словаря предыдущих оценок ф-ции ценности действий Q.

        :param s: Словарь состояний
        :param q_est: Словарь оценок функции ценности действий.
        :return: Словарь оценок функции ценности, согласованный со словарём состояний (вх. данные актора)
        """
        """
            Если в словаре оценок нет оценки для какого либо испытания, то считаем, что это испытание только начинается,
            и, значит, просто генерируем начальную оценку функции ценности.
            Если в словаре состояний нет испытания, для которого присутствует оценка в словаре оценок, то считаем это
            испытание завершившимся, а оценку не нужно. Значит удаляем её из словаря оценок.
            Внимание! Если испытание пошло в обработку, то нужно его довести до конца без перерывов и пауз, 
            так как в момент паузы прошлые значнния оценки функции ценности будут удалены как ненужные этим методом.
        """

        # Копируем исходный словарь оценок
        q = q_est.copy()
        # Проверка словаря оценок на наличие в нём оценок ценности действий испытаний из словаря состояний.
        for key in s.keys():
            # Обходим по ключу словарь состояний.
            if key not in q.keys():
                # Если в словаре оценок нет элемента с данным ключом, то инициализируем и добавляем его в словарь
                q[key] = q_est_init()

        # Проверка словаря состояний на наличие в нём испытаний, оценки действий которых хранятся в словаре оценок.
        # Список оценок функции ценности подлежащих удалению.
        should_be_deleted: List[TestId] = []
        for key in q.keys():
            # Обходим по ключу словарь оценок ценности
            if key not in s.keys():
                # Если в словаре состояний нет такого ключа, то заносим его в список на удаление.
                should_be_deleted.append(key)

        # Удаляем поочерёдно ключи из основного словаря оценок функции ценности.
        for key in should_be_deleted:
            q.pop(key)

        # Возвращаем словарь очищенный от ненужных оценок.
        return q

    def __get_reinforcement(self, inbound: Inbound, waiting_count: int, sleep_time: float,
                              finish_app_checking: Callable[[Inbound], None]) -> Dict[TestId, ZeroOne]:
        """ Получить подкрепления.

        :param waiting_count: количество ожидаемых подкреплений.
        """
        result: Dict[TestId, ZeroOne] = {}
        for i in range(waiting_count):
            while not inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REINFORCEMENT].has_incoming():
                # Пока в канале нет сообщений, крутимся в цикле ожидания.
                sleep(sleep_time)
                finish_app_checking(inbound)

            # Дождались сообщения
            container = inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REINFORCEMENT].receive()
            # buffer_value = container.unpack()
            # if not isinstance(buffer_value, ReinforcementValue)
            reinforcement: ReinforcementValue = container.unpack()
            # test_id: TestId = container.get()
            _, reinf = reinforcement.get_reinforcement()
            result[container.get()] = reinf

        return result

    # def q_est_by_test(self, q_est: List[List[ZeroOne, int]], s_order: List[TestId]):


    def _yarn_run(self, *args, **kwargs) -> None:
        # Вечный цикл. Выход из него по команде на завершение приложения.
        while True:
            try:
                # Оставшееся количество запланированных испытаний.
                remaining_tests: int = self.__get_remaining_tests(self.__inbound, SLEEP_TIME,
                                                                  self.__finish_app_checking)
                # Если размер планируемого батча на входе актора больше полного планируемого количества испытаний,
                # то будем формировать
                # батч размером в полное планируемое количество испытаний.
                self.__project.state.batch_size = self.__project.state.batch_size \
                    if self.__project.state.batch_size <= remaining_tests else remaining_tests

                # Q_estimate
                # q_est: Dict[TestId, float] = ...

                assert isinstance(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS], ReportWire), \
                    'Data wire for remaining tests info should be a ReportWire class. But now is {}'. \
                        format(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].__class__)
                # Отправляем в модуль физической модели число испытаний, которое хочет получить данный модуль.
                report_wire: ISender = self.__inbound[AppModulesEnum.PHYSICS][
                    DataTypeEnum.REMANING_TESTS].get_report_sender()
                report_wire.send(Container(cargo=self.__project.state.batch_size))

                # Сформировать словарь состояний изделия в различных испытаниях.
                batch_dict: Dict[TestId, RealWorldStageStatusN] = \
                    self.__collect_batch(self.__inbound, SLEEP_TIME,
                                         self.__finish_app_checking, self.__project.state.batch_size)

                # Фиксируем порядок испытаний.
                s_order: List[TestId] = []
                for key in batch_dict:
                    s_order.append(key)

                # Актуализировать словарь предыдущих оценок функции ценности действий.
                self.__q_est = self._q_est_actual(batch_dict, self.__q_est)

                # debug = self._q_est_actual({0: RealWorldStageStatusN(), 1: RealWorldStageStatusN()},
                #                             {0: 12.0, 2: 13.0, 3: 14.0})

                # сформировать батч-тензор для ввода в актора состояний N испытаний
                # стейк слабой прожарки (предыдущая прожарка производится в вызываемом методе)
                medium_rare: Tensor = self.__project.actor_input_preparation(batch_dict, s_order)

                # получить тензор выхода (действий/команд) актора для каждого из N испытаний
                # стейк средней прожарки
                medium: Tensor = self.__project.actor_forward(medium_rare)

                # сформировать батч-тензор для ввода в критика из NхV вариантов, где N-количество испытаний/состояний
                # на входе в актора, V - количество вариантов действий актора (количество вариантов включений двигателей)
                # Если батч-тензор на входе в актора состоит из 10 испытаний, количество вариантов
                # включения двигателей - 32 (2^5), то на вход в критика пойдёт тензор размером 10 х 32, т. е. 320 векторов

                medium_in_critic: Tensor = self.__project.critic_input_preparation(medium_rare, medium, batch_dict, s_order)

                # debug = self.__project.critic_input_preparation(
                #     tensor([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]),
                #     tensor([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]),
                #     {0: RealWorldStageStatusN(), 1: RealWorldStageStatusN()},
                #     [1, 0])

                # Получить тензор значений функции ценности на выходе из критика размерностью NхV
                q_est_next: Tensor = self.__project.critic_forward(medium_in_critic)

                # Для каждого из N испытаний выбрать максимальное значение функции ценности из соответствующих V вариантов.
                # max_q_est_next: List[List[ZeroOne | int]] = self.__project.max_in_q_est(q_est_next, s_order)
                max_q_est_next: Dict[TestId, Dict[Dict_key, Q_est_value | Index_value]] = self.__project.max_in_q_est(q_est_next, s_order)

                # Выбрать варианты действий актора,
                # которые соответствуют выбранным максимальным N значениям функции ценности.
                commands: Dict[TestId, Tensor] = self.__project.choose_max_q_action(max_q_est_next)

                # Отправка команд (планируемых действий), согласно максимального значения функции ценности
                for test_id, command_t in commands.items():
                    # Проходимся по словарю команд

                    # Преобразование данных тензора в список
                    command: List = command_t.tolist()[0]

                    # Отправка желаемых действий для каждого испытания в модуль физической модели.
                    self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(
                        Container(test_id, StageControlCommands(0, 0, *command))
                    )

                # Для каждого из N испытаний получить подкрепления, соответствующие выбранным вариантам действий.
                reinforcement = self.__get_reinforcement(self.__inbound, len(commands), SLEEP_TIME, self.__finish_app_checking)

                # На основании подкреплений, рассчёт ошибки целевой функции ценности для каждого из N испытаний.
                err = self.__project.correction(reinforcement, self.__q_est, max_q_est_next)

                # На основании функций ценности из критика и рассчитанных целевых, посчитать N ошибок.

                # Усреднить N ошибок в одну, среднюю avrErr.

                # Произвести обратный проход по критику и актору на основании avrErr.

                # Оптимизировать критика и актора.

                # # # Отправка команды, согласно максимального значения функции ценности
                # # # Пока случайным образом в тестовых целях, чтобы работало.
                # for key in batch_dict:
                #     # Проходимся по словарю/массиву/тензору комманд
                #     # И отправляем их поочерёдно в модуль физической модели.
                #     #
                #     # Пока вот выбрано случайным образом в тестовых целях, чтобы работало.
                #     # И вместо реальных команд нолик и единица.
                #     random.seed()
                #     if random.choice([0, 1]):
                #         # Нейросеть не дала определённого вывода. Команды нет. Двигатели не включать, пропуск такта
                #         self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(
                #             Container(key, StageControlCommands(0)))
                #     else:
                #         # Нейросеть актора даёт команду
                #         self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(
                #             Container(key, StageControlCommands(1)))

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
                # self._training_state.save(self._save_storage_training_state)
                self.__project.save_state()
                # self.__two_nn.save(self._save_storage_model_state)

            except FinishAppException:
                # Поступила команда на завершение приложения.
                #
                # self._training_state.save(self._save_storage_training_state)
                self.__project.save_nn()
                self.__project.save_state()
                # self.__two_nn.save(self._save_storage_model)
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


# def load_nn(nn: InterfaceNeuronNet, storage: InterfaceStorage):
#     pass


# def actorInputTensor(environment: RealWorldStageStatusN):
#     """
#     Формирует тензор входных параметров актора
#
#     :param environment:
#     :return:
#     """
#     return tensor([[0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0.]], dtype=float)


# def criticInputTensor(environment: RealWorldStageStatusN, actorAction: tensor):
#     """
#     Формирует тензор входныx параметров критика.
#
#     :param environment:
#     :param actorOutputVariants:
#     :return: [[Состояние ОС, Вариант действия 1],[Состояние ОС, Вариант действия 2],[Состояние ОС, Вариант действия 3]]
#     """
#
#     return tensor([[0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 1., 0., 1., 0., 1., 0., ],
#                    [0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 0., 1., 1., 0., 1., 0., 1., 0., ]],
#                   dtype=float)


# def actorGradsFromCritic():
#     """
#     Метод выделяет градиенты актора с входных параметров критика (после обратного прохода по критику)
#
#     :return:
#     """
#     return tensor([[0., 1., 0., 1., 0.]], dtype=float)
