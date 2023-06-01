# todo Физическую модель перенести в директорию проекта, так как реализация окр. среды относится к конкретному проекту
from types import ModuleType
from basics import logger_name, TestId, FinishAppException, SLEEP_TIME, START_NEW_AGE
from logging import getLogger
from ifc_flow.i_flow import IPhysics
from thrds_tk.threads import AYarn
import tools
from tools import finish_app_checking
from structures import RealWorldStageStatusN, ReinforcementValue, StageControlCommands
from typing import Dict, Callable
from time import sleep
from con_intr.ifaces import ISocket, ISender, IReceiver, AppModulesEnum, DataTypeEnum, IContainer, BioEnum, \
    Inbound, Outbound
from con_simp.contain import Container, BioContainer
from con_simp.wire import ReportWire
from physics import Moving
from copy import deepcopy
from states.i_states import IStatesStore
from states.s_states import IInitStates


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

logger = getLogger(logger_name + '.physics')


class PhysicsThread(IPhysics, AYarn):
    """ Нить физической модели. """

    def __init__(self, name: str, data_socket: ISocket, project_cfg: ModuleType, birth: bool = False):
        """

        :param name: Имя нити.
        :param data_socket: Сокет модуля физической модели для работы с каналами передачи данных
        :param project_cfg: Объект модуля конфигурации конкретного проекта.
        """
        AYarn.__init__(self, name)

        # Загрузка количества элементов в обучающей выборке.
        self.__max_tests = project_cfg.TRANING_SET_LENGTH

        self.__incoming: Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]] = data_socket.get_in_dict()
        logger.debug('{}.__init__(), На входе в конструктор. \n\t{}, \n\t{}, \n\t{}\n'.
                     format(self.__class__.__name__, data_socket, data_socket.get_all_in(),
                            self.__incoming))
        self.__outgoing: Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]] = data_socket.get_out_dict()
        logger.debug('{}.__init__(), На входе в конструктор. \n\t{}, \n\t{}, \n\t{}\n'.
                     format(self.__class__.__name__, data_socket, data_socket.get_all_out(),
                            self.__outgoing))

        self.__birth = birth

        # Условие окончания одного конкретного испытания.
        self.__finish_criterion = project_cfg.FINISH

        if birth:
            # Обучение начинается с начала.
            # Генератор начальных состояний.
            self.__initial_states: IInitStates = project_cfg.START_STATES

            # Объект-хранилище текущих испытаний
            self.__store: IStatesStore = project_cfg.STATES_STORE

            # Оставшееся количество испытаний в обучающей выборке, сохранённое до перерыва процесса обучения.
            # Задано незначимое значение, так как в этой ветке перерыва не было.
            self.__tests_left_before_break: int = -1
        else:
            # todo Загрузить реальное значение вместо Ellipsis
            # загрузка сериализованных объектов предыдущего этапа прерванного обучения.
            self.__initial_states: IInitStates = ...
            self.__store: IStatesStore = ...
            self.__tests_left_before_break: int = ...

    def initialization(self) -> None:
        pass

    def run(self) -> None:
        pass

    def __get_states_count(self, inbound: Inbound, report_line: IReceiver,
                           sleep_time: float, finish_app_checking: Callable[[Inbound], None]) -> int:
        """ Получить из нейросети количество испытаний, которое она готова обработать.

        :param inbound: словарь исходящих каналов передачи данных
        :param report_line: Канал передачи данной информации.
        :param sleep_time: время сна нити, в ожидании появления очередной команды в канале.
        :param finish_app_checking: метод, перехватывающий команду на завершение нити
        и генерирующий исключение завершения нити.
        :return: Количество испытаний, которое готова обработать нейросеть.
        """
        while not report_line.has_incoming():
            finish_app_checking(inbound)
            sleep(sleep_time)

        container: IContainer = report_line.receive()
        assert isinstance(container, Container), "Receiving container should be a Container class, but now is: "\
            .format(container.__class__)
        count: int = container.unpack()
        return count

    def __set_initial_states(self, states_count: int) -> Dict[TestId, RealWorldStageStatusN]:
        """ Установка начальных положений изделия в испытаниях.

        :param states_count: Сколько сгенерировать начальных состояний. Если == 0, то на выходе пустой словарь.
        :return: Если на выходе пустой словарь, значит у итератора/генератора закончились начальные состояния,
        либо запрошено ноль состояний. """
        result: Dict[TestId, RealWorldStageStatusN] = {}

        if states_count == 0:
            # Если количество затребованных начальных состояний - 0, то на выходе пустой словарь.
            return result

        for i in range(states_count):
            # инициализация начальными данными
            test_id, state = self.__initial_states.get_state()
            logger.debug('__set_initial_state. Начальное состояние: {}, {}'.format(i, state.position))

            if state is None:
                # Итератор начальных состояний пуст?
                pass
            else:
                # начальные состояния пока поступают из итератора
                # В результирующий словарь заносим только те начальные состояния, которые не равны None
                result[test_id] = state

        return result

    def __command_waiting(self, waiting_count: int, inbound: Inbound,
                          sleep_time: float, finish_app_checking: Callable[[Inbound], None])\
            -> Dict[TestId, StageControlCommands]:
        """ Ожидание и получение команды из нейросети.

        :param waiting_count: количество ожидаемых команд из блока нейросети.
        :param inbound: словарь исходящих каналов передачи данных
        :param sleep_time: время сна нити, в ожидании появления очередной команды в канале.
        :param finish_app_checking: метод, перехватывающий команду на завершение нити
        и генерирующий исключение завершения нити.
        """

        result: Dict[TestId, StageControlCommands] = {}
        for i in range(waiting_count):

            while not inbound[AppModulesEnum.NEURO][DataTypeEnum.JETS_COMMAND].has_incoming():
                finish_app_checking(inbound)
                sleep(sleep_time)

            container = inbound[AppModulesEnum.NEURO][DataTypeEnum.JETS_COMMAND].receive()
            assert isinstance(container, Container), "Receiving container should be a Container class, but now is: " \
                .format(container.__class__)
            test_id, command = container.get(), container.unpack()
            result[test_id] = command

        return result

    def __get_reinforcement(self, new_state: RealWorldStageStatusN, command: StageControlCommands) -> ReinforcementValue:
        """ Подкрепление действий системы управления, которые привели к новому состоянию

        :param new_state: новое состояние изделия
        :param command: команда нейросети, которая привела к этому состоянию. """
        return ReinforcementValue(new_state.time_stamp,
                                           tools.Reinforcement.get_reinforcement(new_state, command)
                                           )

    def __test_end(self, state: RealWorldStageStatusN) -> bool:
        """ Проверка на окончание этого конкретного испытания.

        :param state: Новое состояние теста, проверяемое на то что он терминальный
        :return: Испытание закончилось? """

        if self.__finish_criterion.is_one_test_failed(state.position) \
                or self.__finish_criterion.is_one_test_success(state, tools.Reinforcement.accuracy):
            return True
        else:
            return False

    def __states_distribution(self, outbound: Outbound, states: Dict[TestId, RealWorldStageStatusN],
                              bio=BioEnum.ALIVE, quantity=-1) -> None:
        """ Рассылка состояний по потребителям информации.

        :param outbound: Словарь выходных каналов передачи данных.
        :param states: Словарь состояний. Может быть пустой {}, и тогда никакие данные не будут рассылаться.
        :param bio: Состояние для рассылаемых испытаний.
        :param quantity: Какое количество состояний из словаря надо распространить. Если == -1 (по умолчанию), то все.
        :type quantity: int
        """
        assert quantity <= len(states), \
            "Ошибка! Запрошенное количество для передачи должно быть МЕНЬШЕ или РАВНО доступному."

        amount = quantity if quantity != -1 else len(states)

        i = 0
        for key in states.keys():
            # Если на входе был пустой словарь, то мы сразу же выходим из цикла.
            # При amount == 3, будут отправки при i == 0, 1, 2 (то есть - три штуки)
            if i == amount: break

            container: BioContainer = BioContainer(key, bio, states[key])
            outbound[AppModulesEnum.NEURO][DataTypeEnum.STAGE_STATUS].send(deepcopy(container))
            outbound[AppModulesEnum.VIEW][DataTypeEnum.STAGE_STATUS].send(deepcopy(container))
            i += 1
            logger.debug("В НС и Вид отправятся {} испытаний.".format(i))

    def _yarn_run(self, *args, **kwargs) -> None:
        logger.info('Вход в нить.')

        # Канал для передачи в нейросеть количества запланированных испытаний
        report_wire = self.__outgoing[AppModulesEnum.NEURO][DataTypeEnum.REMANING_TESTS]
        # Канал должен быть двусторонним.
        assert isinstance(report_wire, ReportWire), 'Data wire for remaining tests info should be a ReportWire class.'

        # Осталось провести запланированных испытаний.
        tests_left: int = self.__max_tests if self.__birth else self.__tests_left_before_break

        while tests_left >= 0:
            # Пока ещё есть испытания в планах, цикл работает.
            logger.info("Вход в цикл генерации и передачи состояний изделия.")
            try:
                # отправляем в нейросеть количество оставшихся по программе испытаний
                report_wire.send(Container(cargo=tests_left))

                logger.debug("Испытаний в плане: {}".format(tests_left))

                # Нейросеть сообщает, какое количество испытаний она готова обработать в этом проходе
                # Когда осталось 0 испытаний, блок физ. модели либо получит указание на новую эпоху,
                # либо зависнет в вызове этой функции в ожидании команды на завершение приложения.
                requested_states_count = self.__get_states_count(self.__incoming, report_wire.get_report_receiver(),
                                                                 SLEEP_TIME, finish_app_checking)
                logger.debug("НС готова принять состояний: {}".format(requested_states_count))

                if requested_states_count == START_NEW_AGE:
                    # Блок нейросети сигнализирует, что надо начать новую эпоху.
                    # Обновляем переменную.
                    tests_left = self.__max_tests
                    # Инициализируем новый объект начальных состояний.
                    self.__initial_states = self.__initial_states.__class__(self.__max_tests)
                    # Заходим на новую эпоху.
                    continue

                # if requested_states_count == CLOSE_APP:

                assert tests_left >= requested_states_count, \
                    "Ошибка! Количество запрошенных модулем нейросети состояний должно быть МЕНЬШЕ," \
                    "чем количество оставшихся доступных состояний (испытания в работе плюс испытания в генераторе)"

                if requested_states_count <= self.__store.get_amount():
                    # Если запрошенное блоком нейросети количество состояний МЕНЬШЕ,
                    # чем оставшееся после предыдущего прохода по нейросети.
                    self.__states_distribution(self.__outgoing, self.__store.all_states(), BioEnum.ALIVE, requested_states_count)
                    logger.debug("Отправлено в НС {} испытаний.".format(requested_states_count))
                else:
                    # Если запрошенное блоком нейросети количество состояний БОЛЬШЕ,
                    # чем оставшееся после предыдущего прохода по нейросети.
                    # Добиваем до нужного количества, генерацией новых состояний.
                    new_states = self.__set_initial_states(requested_states_count - self.__store.get_amount())
                    # Отправляем потребителям инициализированные состояния
                    self.__states_distribution(self.__outgoing, new_states, BioEnum.INIT)
                    # И отправляем все оставшиеся имеющиеся состояния потребителям, в т. ч. и модулю нейросети.
                    self.__states_distribution(self.__outgoing, self.__store.all_states(), BioEnum.ALIVE)
                    logger.debug("Отправлено в НС {} (новых) + {} (старых) испытаний.".
                                 format(len(new_states), self.__store.get_amount()))
                    # добавляем новые состояния к общему словарю
                    if not self.__store.add_state(states=new_states):
                        raise KeyError("Any adding test identificators is already in store.")

                # Получение команд из блока нейросети.
                commands: Dict[TestId, StageControlCommands] = \
                    self.__command_waiting(requested_states_count, self.__incoming,
                                           SLEEP_TIME, finish_app_checking)

                assert len(commands) == requested_states_count, \
                    "Ошибка! Количество полученных из блока нейросети команд - {}, должно быть равно количеству " \
                    "отосланных туда ДЕЙСТВИТЕЛЬНЫХ испытаний - {}.". format(len(commands), requested_states_count)

                logger.debug("Словарь команд из нейросети: {}".format(commands))

                # Вычитаем из запланированных испытаний те, которые уже в работе.
                future_tests = tests_left - self.__store.get_amount()

                fin_states: Dict[TestId, RealWorldStageStatusN] = {}
                # Цикл получения новых состояний (после применения команд нейросети)
                for key in commands:
                    # Меняем состояния изделия в словаре текущих испытаний на новые (после применения команд)
                    if not self.__store.update_state(key, Moving.get_new_status(commands[key], self.__store.get_state(key))):
                        raise KeyError("Updated test with this identificator is not present in store.")

                    state = self.__store.get_state(key)
                    if state is None:
                        raise KeyError("Requested test identificator is not present in store.")
                    reinf: ReinforcementValue = self.__get_reinforcement(state, commands[key])
                    container: Container = Container(key, reinf)
                    self.__outgoing[AppModulesEnum.NEURO][DataTypeEnum.REINFORCEMENT].send(deepcopy(container))

                    # Если данное испытание подошло к концу, исключаем его из общего словаря.
                    state = self.__store.get_state(key)
                    if state is not None and self.__test_end(state):
                        # Словарь завершённых тестов.
                        fin_states[key] = state
                        # Словарь текущих испытаний, очищенный от завершённых испытаний.
                        self.__store.del_state(key)
                    elif state is None:
                        raise KeyError("Requested test identificator is not present in store.")

                # Так как словарь с испытаниями подчистился от тех испытаний, которые уже завершились.
                # То приплюсовываем к количеству незапущенных испытаний, количество "живых" испытаний в обработке.
                # |----------------------------tests_left-------------------------------|
                # |--ongoing_states--|-----------------future_tests---------------------|

                tests_left = self.__store.get_amount() + future_tests

                # Отправляем в модуль вида завершённые состояния для отображения.
                for key in fin_states:
                    container: BioContainer = BioContainer(key, BioEnum.FIN, fin_states[key])
                    self.__outgoing[AppModulesEnum.VIEW][DataTypeEnum.STAGE_STATUS].\
                        send(deepcopy(container))

            except FinishAppException:
                logger.info('Поступила команда на завершение приложения. Завершаем нить.')
                if tests_left > 0:
                    # Команда на закрытие приложения, но, так как ещё остались элементы в обучающей выборке,
                    # Сохраняем промежуточное состояние.
                    #
                    # Сохранить состояния находящиеся в процессе испытаний self.__store
                    #
                    # Сохранить состояние источника элементов обучающей выборки self.__initial_states
                    #
                    # Сохранить оставшееся число испытаний в обучающей выборке tests_left
                    pass
                else:
                    # Элементов в обучающей выборке не осталось, значит - завершаем обучение.
                    #
                    # Сохраняем tests_left = 0, как знак того, что обучение в объёме Эры закончено.
                    # Продолжить ли обучение с новой Эры будет решать при загрузке блок нейросети.
                    pass
                break
