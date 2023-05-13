from types import ModuleType
import importlib
from logging import getLogger
from basics import logger_name, TestId, FinishAppException, SLEEP_TIME, ZeroOne, START_NEW_AGE, CLOSE_APP
from ifc_flow.i_flow import INeuronet
from thrds_tk.threads import AYarn
import structures
from structures import StageControlCommands, RealWorldStageStatusN, ReinforcementValue
from torch import device, float, Tensor
from typing import Dict, Callable, List
from time import sleep
from con_intr.ifaces import ISocket, ISender, AppModulesEnum, DataTypeEnum, Inbound, Outbound, finish_app_checking
from con_simp.contain import Container, BioContainer
from con_simp.wire import ReportWire
from nn_iface.ifaces import ProjectInterface, LossCriticInterface, LossActorInterface
from tools import q_est_init
from app_cfg import PROJECT_MAIN_CLASS, PROJECT_DIRECTORY_NAME, PROJECT_PY_FILE

logger = getLogger(logger_name + '.neuronet')
# Inbound = Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]]
# Outbound = Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]]


class NeuronetThread(INeuronet, AYarn):
    """ Нить нейросети. """

    def __init__(self, name: str, data_socket: ISocket, project_cfg: ModuleType,
                 savePath='.\\', actorCheckPointFile='actor.pth.tar',
                 criticCheckPointFile='critic.pth.tar'):
        AYarn.__init__(self, name)

        logger.info('Конструктор класса нити нейросети. {}.__init__'.format(self.__class__.__name__))

        self.__inbound: Inbound = data_socket.get_in_dict()
        self.__outbound: Outbound = data_socket.get_out_dict()

        # RunTime импортирование модуля с проектом.
        project_module: ModuleType = importlib.import_module('{}.{}'.format(PROJECT_DIRECTORY_NAME, PROJECT_PY_FILE[1:8]))
        # Создание объекта на основании класса проекта.
        self.__project : ProjectInterface = eval('project_module.{}()'.format(PROJECT_MAIN_CLASS))

        self.__project.load_nn()

        self.__project.load_state()

        self.__calc_device = device(self.__project.device)
        logger.debug('{}'.format(self.__calc_device))

        # Оценки функции ценности предыдущего прохода
        self.__q_est: Dict[TestId, ZeroOne] = {}

    def initialization(self) -> None:
        pass

    def run(self) -> None:
        pass

    # def __finish_app_checking(self, inbound: Inbound) -> None:
    #     """ Метод проверяет на появление в канале связи команды на заврешение приложения. """
    #     # Если команда на завершение приложения есть
    #     if inbound[AppModulesEnum.VIEW][DataTypeEnum.APP_FINISH].has_incoming():
    #         # Получаем эту команду
    #         inbound[AppModulesEnum.VIEW][DataTypeEnum.APP_FINISH].receive()
    #         # Возбуждаем исключение завершения приложения.
    #         raise FinishAppException
    #     # return False

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

            reinforcement: ReinforcementValue = container.unpack()

            _, reinf = reinforcement.get_reinforcement()
            result[container.get()] = reinf

        return result

    def _yarn_run(self, *args, **kwargs) -> None:

        # Проверка линии связи, на наличие встречной линии репорта.
        assert isinstance(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS], ReportWire), \
            'Data wire for remaining tests info should be a ReportWire class. But now is {}'. \
                format(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].__class__)
        # Ответная линия, по которой блок нейросети отправляет в блок физ. модели количество испытаний,
        # которые он готов принять и обработать.
        report_wire: ISender = self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS] \
            .get_report_sender()

        start_epoch: int = self.__project.state.epoch_current

        # Цикл по эпохам
        for current_epoch in range(start_epoch, self.__project.state.epoch_stop + 1):
            # Цикл по испытаниям в рамках одной эпохи.
            while True:
                try:
                    # Оставшееся количество запланированных испытаний.
                    remaining_tests: int = self.__get_remaining_tests(self.__inbound, SLEEP_TIME,
                                                                      finish_app_checking)

                    if remaining_tests == 0:
                        # Завершение одной эпохи, так как больше нет запланированных испытаний.
                        break

                    # Если размер планируемого батча на входе актора больше полного планируемого количества испытаний,
                    # то будем формировать
                    # батч размером в полное планируемое количество испытаний.
                    self.__project.state.batch_size = self.__project.state.batch_size \
                        if self.__project.state.batch_size <= remaining_tests else remaining_tests

                    # assert isinstance(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS], ReportWire), \
                    #     'Data wire for remaining tests info should be a ReportWire class. But now is {}'. \
                    #         format(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].__class__)
                    # # Отправляем в модуль физической модели число испытаний, которое хочет получить модуль нейросети.
                    # report_wire: ISender = self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS] \
                    #     .get_report_sender()
                    report_wire.send(Container(cargo=self.__project.state.batch_size))

                    # Сформировать словарь состояний изделия в различных испытаниях.
                    batch_dict: Dict[TestId, RealWorldStageStatusN] = \
                        self.__collect_batch(self.__inbound, SLEEP_TIME,
                                             finish_app_checking, self.__project.state.batch_size)

                    # Фиксируем порядок испытаний.
                    s_order: List[TestId] = []
                    for key in batch_dict:
                        s_order.append(key)

                    # Актуализировать словарь предыдущих оценок функции ценности действий.
                    self.__q_est: Dict[TestId, ZeroOne] = self._q_est_actual(batch_dict, self.__q_est)

                    # debug = self._q_est_actual({0: RealWorldStageStatusN(), 1: RealWorldStageStatusN()},
                    #                             {0: 12.0, 2: 13.0, 3: 14.0})

                    # сформировать батч-тензор для ввода в актора состояний N испытаний
                    # стейк слабой прожарки (предыдущая прожарка производится в вызываемом методе)
                    medium_rare: Tensor = self.__project.actor_input_preparation(batch_dict, s_order)

                    # получить тензор выхода (действий/команд) актора для каждого из N испытаний
                    # стейк средней прожарки
                    medium: Tensor = self.__project.actor_forward(medium_rare)

                    # сформировать батч-тензор для ввода в критика из NхV вариантов, где N-количество испытаний/состояний
                    # на входе в актора, V - количество вариантов действий актора
                    # (количество вариантов включений двигателей)
                    # Если батч-тензор на входе в актора состоит из 10 испытаний, количество вариантов
                    # включения двигателей - 32 (2^5), то на вход в критика пойдёт тензор размером 10 х 32,
                    # т. е. 320 векторов

                    medium_in_critic: Tensor = self.__project.critic_input_preparation(medium_rare, medium,
                                                                                       batch_dict, s_order)

                    # debug = self.__project.critic_input_preparation(
                    #     tensor([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]),
                    #     tensor([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]),
                    #     {0: RealWorldStageStatusN(), 1: RealWorldStageStatusN()},
                    #     [1, 0])

                    # Получить тензор значений функции ценности на выходе из критика размерностью NхV
                    # Нужно понимать, что первые V оценок в выходном тензоре критика относяться к первому испытанию.
                    # Вторые V оценок относятся ко второму испытанию.
                    # Третьи V оценок к третьему.
                    # И т. д.
                    q_est_next: Tensor = self.__project.critic_forward(medium_in_critic)

                    # Для каждого из N испытаний на выходе из критика
                    # выбрать максимальное значение функции ценности из соответствующих V вариантов.
                    # То есть, из первых V оценок надо выбрать максимальную,
                    # и это будет максимальная оценка для первого испытания.
                    # Из вторых V оценок надо выбрать максимальную, и это будет максимальная оценка для второго испытания.
                    # Из третьих V оценок надо выбрать максимальную, и это будет максимальная оценка для третьего.
                    # И т. д.

                    # Индексы максимальных значений оценки функции ценности.
                    max_q_est_next_index: Dict[TestId, int] = self.__project.max_in_q_est(q_est_next, s_order)

                    # Тензор максимальных оценок функции ценности.
                    max_q_est_next: Tensor = self.__project.critic_output_transformation(q_est_next, s_order,
                                                                                         max_q_est_next_index)

                    # Выбрать варианты действий актора,
                    # которые соответствуют выбранным максимальным N значениям функции ценности.
                    commands: Dict[TestId, Tensor] = self.__project.choose_max_q_action(s_order, max_q_est_next_index)

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
                    reinforcement: Dict[TestId, ZeroOne] = self.__get_reinforcement(self.__inbound, len(commands),
                                                                                    SLEEP_TIME, finish_app_checking)

                    # Объект функции потерь критика.
                    critic_loss_fn: LossCriticInterface = self.__project.critic_loss
                    # todo протестировать работу
                    # Ошибка критика
                    crititc_loss: Tensor = critic_loss_fn(s_order, reinforcement, self.__q_est, max_q_est_next)

                    # Произвести обратный проход по критику
                    crititc_loss.backward()

                    # Объект функции потерь актора
                    actor_loss_fn: LossActorInterface = self.__project.actor_loss

                    # Целевой тензор актора.
                    actor_target: Tensor = self.__project.actor_target(s_order, commands)

                    # Ошибка актора
                    actor_loss: Tensor = actor_loss_fn(medium, actor_target)

                    # Обратный проход по актору.
                    actor_loss.backward()

                    # Оптимизировать критика и актора.
                    self.__project.actor_optimizer.step()
                    self.__project.critic_optimizer.step()

                    # Сохранение по новым интерфейсам.
                    # self.__project.state.epoch_current = current_epoch
                    self.__project.save_state()

                except FinishAppException:
                    # Поступила команда на завершение приложения.
                    self.__project.save_nn()
                    self.__project.save_state()
                    logger.info('Нейросеть. Поступила команда на завершение приложения. Завершаем нить.')
                    break

            if current_epoch < self.__project.state.epoch_stop:
                # Запоминание факта перехода к новой эпохе
                self.__project.state.epoch_current = current_epoch + 1
                # Отправка в блок физ. модели указания на начало новой эпохи.
                report_wire.send(Container(cargo=START_NEW_AGE))
            elif current_epoch == self.__project.state.epoch_stop:
                # Запоминание факта завершения прохода по эпохам.
                self.__project.state.epoch_current = current_epoch
                # Запланированное количество эпох исполнено. Команда на завершение.
                report_wire.send(Container(cargo=CLOSE_APP))

            # Сохранение состояния в хранилище.
            self.__project.save_state()

        # # Вечный цикл. Выход из него по команде на завершение приложения.
        # while True:
        #     try:
        #         # Оставшееся количество запланированных испытаний.
        #         remaining_tests: int = self.__get_remaining_tests(self.__inbound, SLEEP_TIME,
        #                                                           self.__finish_app_checking)
        #
        #         if remaining_tests == 0:
        #             # Завершение одной эпохи, так как больше нет запланированных испытаний.
        #             # todo Инициализировать завершение приложения?
        #             # todo Инициализировать переход к новой эпохе?
        #             pass
        #
        #         # Если размер планируемого батча на входе актора больше полного планируемого количества испытаний,
        #         # то будем формировать
        #         # батч размером в полное планируемое количество испытаний.
        #         self.__project.state.batch_size = self.__project.state.batch_size \
        #             if self.__project.state.batch_size <= remaining_tests else remaining_tests
        #
        #         assert isinstance(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS], ReportWire), \
        #             'Data wire for remaining tests info should be a ReportWire class. But now is {}'.\
        #                 format(self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS].__class__)
        #         # Отправляем в модуль физической модели число испытаний, которое хочет получить модуль нейросети.
        #         report_wire: ISender = self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.REMANING_TESTS]\
        #             .get_report_sender()
        #         report_wire.send(Container(cargo=self.__project.state.batch_size))
        #
        #         # Сформировать словарь состояний изделия в различных испытаниях.
        #         batch_dict: Dict[TestId, RealWorldStageStatusN] = \
        #             self.__collect_batch(self.__inbound, SLEEP_TIME,
        #                                  self.__finish_app_checking, self.__project.state.batch_size)
        #
        #         # Фиксируем порядок испытаний.
        #         s_order: List[TestId] = []
        #         for key in batch_dict:
        #             s_order.append(key)
        #
        #         # Актуализировать словарь предыдущих оценок функции ценности действий.
        #         self.__q_est: Dict[TestId, ZeroOne] = self._q_est_actual(batch_dict, self.__q_est)
        #
        #         # debug = self._q_est_actual({0: RealWorldStageStatusN(), 1: RealWorldStageStatusN()},
        #         #                             {0: 12.0, 2: 13.0, 3: 14.0})
        #
        #         # сформировать батч-тензор для ввода в актора состояний N испытаний
        #         # стейк слабой прожарки (предыдущая прожарка производится в вызываемом методе)
        #         medium_rare: Tensor = self.__project.actor_input_preparation(batch_dict, s_order)
        #
        #         # получить тензор выхода (действий/команд) актора для каждого из N испытаний
        #         # стейк средней прожарки
        #         medium: Tensor = self.__project.actor_forward(medium_rare)
        #
        #         # сформировать батч-тензор для ввода в критика из NхV вариантов, где N-количество испытаний/состояний
        #         # на входе в актора, V - количество вариантов действий актора
        #         # (количество вариантов включений двигателей)
        #         # Если батч-тензор на входе в актора состоит из 10 испытаний, количество вариантов
        #         # включения двигателей - 32 (2^5), то на вход в критика пойдёт тензор размером 10 х 32,
        #         # т. е. 320 векторов
        #
        #         medium_in_critic: Tensor = self.__project.critic_input_preparation(medium_rare, medium,
        #                                                                            batch_dict, s_order)
        #
        #         # debug = self.__project.critic_input_preparation(
        #         #     tensor([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]),
        #         #     tensor([[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]),
        #         #     {0: RealWorldStageStatusN(), 1: RealWorldStageStatusN()},
        #         #     [1, 0])
        #
        #         # Получить тензор значений функции ценности на выходе из критика размерностью NхV
        #         # Нужно понимать, что первые V оценок в выходном тензоре критика относяться к первому испытанию.
        #         # Вторые V оценок относятся ко второму испытанию.
        #         # Третьи V оценок к третьему.
        #         # И т. д.
        #         q_est_next: Tensor = self.__project.critic_forward(medium_in_critic)
        #
        #         # Для каждого из N испытаний на выходе из критика
        #         # выбрать максимальное значение функции ценности из соответствующих V вариантов.
        #         # То есть, из первых V оценок надо выбрать максимальную,
        #         # и это будет максимальная оценка для первого испытания.
        #         # Из вторых V оценок надо выбрать максимальную, и это будет максимальная оценка для второго испытания.
        #         # Из третьих V оценок надо выбрать максимальную, и это будет максимальная оценка для третьего.
        #         # И т. д.
        #
        #         # Индексы максимальных значений оценки функции ценности.
        #         max_q_est_next_index: Dict[TestId, int] = self.__project.max_in_q_est(q_est_next, s_order)
        #
        #         # Тензор максимальных оценок функции ценности.
        #         max_q_est_next: Tensor = self.__project.critic_output_transformation(q_est_next, s_order,
        #                                                                              max_q_est_next_index)
        #
        #         # Выбрать варианты действий актора,
        #         # которые соответствуют выбранным максимальным N значениям функции ценности.
        #         commands: Dict[TestId, Tensor] = self.__project.choose_max_q_action(s_order, max_q_est_next_index)
        #
        #         # Отправка команд (планируемых действий), согласно максимального значения функции ценности
        #         for test_id, command_t in commands.items():
        #             # Проходимся по словарю команд
        #
        #             # Преобразование данных тензора в список
        #             command: List = command_t.tolist()[0]
        #
        #             # Отправка желаемых действий для каждого испытания в модуль физической модели.
        #             self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.JETS_COMMAND].send(
        #                 Container(test_id, StageControlCommands(0, 0, *command))
        #             )
        #
        #         # Для каждого из N испытаний получить подкрепления, соответствующие выбранным вариантам действий.
        #         reinforcement: Dict[TestId, ZeroOne] = self.__get_reinforcement(self.__inbound, len(commands),
        #                                                                         SLEEP_TIME, self.__finish_app_checking)
        #
        #         # Объект функции потерь критика.
        #         critic_loss_fn: LossCriticInterface = self.__project.critic_loss
        #         # todo протестировать работу
        #         # Ошибка критика
        #         crititc_loss: Tensor = critic_loss_fn(s_order, reinforcement, self.__q_est, max_q_est_next)
        #
        #         # Произвести обратный проход по критику
        #         crititc_loss.backward()
        #
        #         # Объект функции потерь актора
        #         actor_loss_fn: LossActorInterface = self.__project.actor_loss
        #
        #         # Целевой тензор актора.
        #         actor_target: Tensor = self.__project.actor_target(s_order, commands)
        #
        #         # Ошибка актора
        #         actor_loss: Tensor = actor_loss_fn(medium, actor_target)
        #
        #         # Обратный проход по актору.
        #         actor_loss.backward()
        #
        #         # Оптимизировать критика и актора.
        #         self.__project.actor_optimizer.step()
        #         self.__project.critic_optimizer.step()
        #
        #         # Сохранение по новым интерфейсам.
        #         self.__project.save_state()
        #
        #     except FinishAppException:
        #         # Поступила команда на завершение приложения.
        #         self.__project.save_nn()
        #         self.__project.save_state()
        #         logger.info('Нейросеть. Поступила команда на завершение приложения. Завершаем нить.')
        #         break
