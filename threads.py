""" Класс нитей и инструментов работы с ними. """
# from builtins import function
import tools
from physics import Moving
from tools import Finish, MetaQueue, InitialStatus, InitialStatusAbstract
from threading import Thread
from training import start_nb
from kill_flags import KillCommandsContainer, KillCommandsContainerN, KillInterface
from structures import RealWorldStageStatusN, ReinforcementValue, StageControlCommands, StageState, ControlCommands, ReinforcementMessage
from datadisp.adisp import DispatcherAbstract
from carousel.metaque import MetaQueueN, MetaQueue2
from typing import Callable, Optional, Iterator, Tuple
from time import sleep
from carousel.atrolley import TestId
from abc import ABC


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

# Время сна между запросами о наличии блока данных в очереди, сек
SLEEP_TIME = 0.001

def neuronet_thread(queues: MetaQueue, kill: KillCommandsContainer, initial_status: RealWorldStageStatusN):
    """
    Метод, запускаемый в отдельной нитке для обучения нейросети.

    :param queues: очередь, для передачи даннных
    :param kill: контейнер флагов на завершение нитей
    :param initial_status: начальное состояние изделия в СКИП
    """
    print("Вход в нить нейросети.\n")

    # запуск дочерней нити, так как в этой цикла не предусматривается, а вот в дочерней будет цикл обучения
    # todo возможно, следует вызывать из модуля main сразу функцию обучения как нить, без этой промежуточной
    neuro_net_training_thread = Thread(target=start_nb, name="neuroNetTraningThread",
                                       args=(queues, kill, initial_status))
    # запуск метода обучения сети
    neuro_net_training_thread.start()

    neuro_net_training_thread.join()

    print("Завершение нити нейросети.\n")


# def reality_thread_2(queues: MetaQueue, kill: KillCommandsContainer,
#                      max_tests: int, initial_status: RealWorldStageStatusN):
#     """
#     Функция моделирующая поведение ступени в реальной физической среде
#
#     :param queues: Контейнер очередей передачи данных.
#     :param kill: Контейнер команд на завершение нитей.
#     :param max_tests: Количество запланированных испытательных посадок.
#     :param initial_status: Начальное состояние (положение) изделия в СКИП
#     """
#     print("Вход в нить окружающей среды.")
#
#     finish_control = Finish()
#
#     # провести указанное число испытательных посадок
#     for i in range(max_tests):
#         # предыдущее состояние изделия
#         previous_stage_status: RealWorldStageStatusN = initial_status
#         # Информация о начальном положении изделия отправляется в нити
#         queues.put(initial_status)
#
#         while not kill.reality:
#             # ждём команду для двигателей из нейросети на отправленное начальное состояние
#             if not queues.empty("command"):
#                 command = queues.get("command")
#                 # команда, ведущая к новому состоянию, получена
#                 break
#         else:
#             break
#
#         # цикл последовательной генерации состояний в процессе одной тестовой посадки
#         # цикл прерывается, только если во время посадки случилась удача / неудача
#         # или поступила команда на заверешение работы программы
#         while not finish_control.is_one_test_failed(previous_stage_status.position) and not kill.reality:
#             # очередное состояние изделия в СКИП
#             new_stage_status = Moving.get_new_status(command, previous_stage_status)
#             # Подкрепление действий системы управления, которые привели к новому состоянию
#             reinforcement = ReinforcementValue(new_stage_status.time_stamp,
#                                                tools.Reinforcement.get_reinforcement(new_stage_status, command)
#                                                )
#
#             # Отправляем величину подкрепления в НС
#             queues.put(reinforcement)
#             # добавить в выходную очередь очередную порцию информации о состоянии ступени
#             queues.put(new_stage_status)
#
#             # если удачная посадка
#             if finish_control.is_one_test_success(new_stage_status, tools.Reinforcement.accuracy):
#                 # переходим к следующему испытанию
#                 break
#
#             while not kill.reality:
#                 # ждём команду из нейросети на отправленное состояние и подкрепление
#                 if not queues.empty("command"):
#                     command = queues.get("command")
#                     # команда, ведущая к новому состоянию, получена
#                     break
#             else:
#                 break
#
#             previous_stage_status = new_stage_status
#             print("{0}. Time: {1}, Posititon: {2}, Velocyty: {3},\n Axelerantion: {4}, Orientation: {5}\n".
#                   format(i, new_stage_status.time_stamp, new_stage_status.position, new_stage_status.velocity,
#                          new_stage_status.acceleration, new_stage_status.orientation))
#
#         # прекращаем испытания, завершение программы
#         if kill.reality:
#             break
#
#     print("Завершение нити реальности.")
#
#
# def reality_thread_3(dispatcher: DispatcherAbstract, meta_queue: MetaQueueN, initial_status: InitialStatusAbstract,
#                      batch_size: int, kill: KillCommandsContainer):
#     """ Функция нити реальности. Получет данные из очереди и отправляет сообщения в очередь. """
#     # dispatcher: DispatcherAbstract = ListDispatcher(meta_queue, batch_size, kill)
#     print("Вход в нить окружающей среды.")
#
#     finish_control = Finish()
#
#     sleep_time = 0.001
#
#     command: Optional[StageControlCommands] = None
#
#     init_iter: Iterator = iter(initial_status)
#
#     #####
#     # цикл установки исходных положений изделия
#     #####
#     for i in range(batch_size):
#         # инициализация начальными данными
#         state = next(init_iter)
#         dispatcher.put_zero_state(i, state)
#         while not meta_queue.state_to_neuronet.has_void_trolley():
#             sleep(sleep_time)
#         else:
#             meta_queue.state_to_neuronet.load(i, state, True)
#
#     #####
#     # главный цикл получения команд из очереди нейросети и отправки в нейросеть обработанных данных
#     #####
#     while not initial_status.is_empty or not kill.reality:
#         # Пока есть в запасе исходные данные и пока нет команды на завершение нити
#         while not meta_queue.command_to_real.has_new_cargo():
#             # пока нет в очереди очередной команды - ждём
#             sleep(sleep_time)
#             if kill.reality: return
#         else:
#             # Получение команды из нейросети
#             test_id, _ = meta_queue.command_to_real.unload(command)
#
#         test_id, new_state = dispatcher.run(test_id, command)
#
#         # Подкрепление действий системы управления, которые привели к новому состоянию
#         reinf = ReinforcementValue(new_state.time_stamp,
#                                            tools.Reinforcement.get_reinforcement(new_state, command)
#                                            )
#         # Передача подкрепления в нейросеть
#         meta_queue.reinf_to_neuronet.load(test_id, reinf)
#
#         # Если это конкретное испытание закончилось
#         is_new_state: bool = False
#         if finish_control.is_one_test_failed(new_state.position) \
#                 or finish_control.is_one_test_success(new_state, tools.Reinforcement.accuracy):
#             # отправляем в диспетчер новые исходные данные для закончившегося теста
#             new_state = next(init_iter)
#             dispatcher.put_zero_state(test_id, new_state)
#             is_new_state = True
#
#         # отправка нового состояния в очереди сообщений
#         meta_queue.state_to_neuronet.load(test_id, new_state, is_new_state)
#         meta_queue.state_to_view.load(test_id, new_state, is_new_state)
#
#     print("Завершение нити реальности.")


class RealThread(Thread):
    def __init__(self, name: str, dispatcher: DispatcherAbstract, meta_queue: MetaQueueN,
                 initial_state: InitialStatusAbstract, kill: KillCommandsContainer, batch_size=1):
        Thread.__init__(self, name=name)
        self.__dispatcher = dispatcher
        self.__meta_queue = meta_queue
        self.__initial_states = initial_state
        self.__kill = kill
        self.__batch_size = batch_size

        # Итератор прохода по начальным состояниям изделия (исходным положениям)
        self.__iterator = iter(initial_state)
        # Время сна нити в ожидании сообщений в очереди
        self.__sleep_time = 0.001
        # Условие окончания одного конкретного испытания.
        self.__finish_criterion = Finish()
        # self.__neuronet_command: Optional[StageControlCommands] = None

        # в блок визуализации будут отсылаться только испытания с этим Id
        self.__test_id_for_view: TestId = 0
        # атрибут уровня объекта для загрузки / выгрузки состояния изделия в / из очереди
        self.__test_id: TestId = -1
        # атрибут уровня объекта для загрузки / выгрузки состояния изделия в / из очереди
        self.__state: Optional[RealWorldStageStatusN] = RealWorldStageStatusN()
        # атрибут уровня объекта для загрузки / выгрузки состояния изделия в / из очереди
        self.__neuronet_command: Optional[StageControlCommands] = StageControlCommands(time_stamp=-1)


    def __set_initial_states(self) -> bool:
        """ Установка начальных положений изделия в испытаниях.

        :return: Поступил сигнал на завершение нити. """
        for i in range(self.__batch_size):
            # инициализация начальными данными
            state = next(self.__iterator)
            self.__dispatcher.put_zero_state(i, state)
            while not self.__meta_queue.state_to_neuronet.has_void_trolley():
                sleep(self.__sleep_time)
                if self.__kill.reality: return True
            else:
                self.__meta_queue.state_to_neuronet.load(i, state, True)

        return self.__kill.reality

    def __command_waiting(self) -> bool:
        """ Ожидание команды из нейросети.

         :return: Поступил сигнал на завершение нити. """
        # Пока есть в запасе исходные данные и пока нет команды на завершение нити
        while not self.__meta_queue.command_to_real.has_new_cargo():
            # пока нет в очереди очередной команды - ждём
            sleep(self.__sleep_time)
            if self.__kill.reality: return True
        else:
            # Получение команды из нейросети
            self.__test_id, _ = self.__meta_queue.command_to_real.unload(self.__neuronet_command)

        return self.__kill.reality

    def __get_reinforcement(self, new_state: RealWorldStageStatusN, command: StageControlCommands):
        """ Подкрепление действий системы управления, которые привели к новому состоянию

        :param new_state: новое состояние изделия
        :param command: команда нейросети, которая привела к этому состоянию. """
        return ReinforcementValue(new_state.time_stamp,
                                           tools.Reinforcement.get_reinforcement(new_state, command)
                                           )

    def __send_reinforcement_to_neuronet(self, test_id: TestId, reinf: ReinforcementValue) -> bool:
        """ Передача подкрепления в нейросеть

        :param test_id: Идентификатор испытания
        :param reinf: Подкрепление данного испытания.
        :return: Поступил сигнал на завершение нити. """
        while not self.__meta_queue.reinf_to_neuronet.has_void_trolley():
            sleep(self.__sleep_time)
            if self.__kill.reality: return True
        else:
            self.__meta_queue.reinf_to_neuronet.load(test_id, reinf)

        return self.__kill.reality

    def __test_end(self, test_id: TestId, new_state: RealWorldStageStatusN) -> bool:
        """ Проверка на окончание этого конкретного испытания.


        :param test_id: Идентификатор теста
        :param new_state: Новое состояние теста, проверяемое на то что он терминальный
        :return: Испытание закончилось? Новое исходное положение установлено? """

        is_new_state: bool = False
        if self.__finish_criterion.is_one_test_failed(new_state.position) \
                or self.__finish_criterion.is_one_test_success(new_state, tools.Reinforcement.accuracy):
            # отправляем в диспетчер новые исходные данные для закончившегося теста
            new_state = next(self.__iterator)
            # Когда источник начальных данных иссякает, то в список испытаний заносится None
            self.__dispatcher.put_zero_state(test_id, new_state)
            is_new_state = True
        return is_new_state

    def __send_new_state_to_receivers(self, test_id: TestId, new_state: RealWorldStageStatusN,
                                      is_new_state: bool) -> bool:
        """ Отправка нового состояния в очереди сообщений.

         :param test_id: Идентификатор теста
         :param new_state: Новое состояние изделия
         :param is_new_state: Состояние является начальным для нового теста?
         :return: Поступил сигнал на завершение нити. """

        while not self.__meta_queue.state_to_neuronet.has_void_trolley():
            sleep(self.__sleep_time)
            if self.__kill.reality: return True
        else:
            self.__meta_queue.state_to_neuronet.load(test_id, new_state, is_new_state)

        if test_id == self.__test_id_for_view:
            while not self.__meta_queue.state_to_view.has_void_trolley():
                sleep(self.__sleep_time)
                if self.__kill.reality: return True
            else:
                self.__meta_queue.state_to_view.load(test_id, new_state, is_new_state)

            while not self.__meta_queue.state_to_stage_view.has_void_trolley():
                sleep(self.__sleep_time)
                if self.__kill.reality: return True
            else:
                self.__meta_queue.state_to_stage_view.load(test_id, new_state, is_new_state)

        return self.__kill.reality

    def run(self):
        """ Note. Именно этот метод запускает в нити. """
        print('Вхоть в нить физ. модели')
        if self.__set_initial_states(): return

        while not self.__dispatcher.is_all_tests_ended() and not self.__kill.reality:

            if self.__command_waiting(): break

            self.__dispatcher.run(self.__test_id, self.__neuronet_command, self.__state)

            reinf = self.__get_reinforcement(self.__state, self.__neuronet_command)

            if self.__send_reinforcement_to_neuronet(self.__test_id, reinf): break

            is_new_state = self.__test_end(self.__test_id, self.__state)
            if self.__send_new_state_to_receivers(self.__test_id, self.__state, is_new_state): break

        print('Выход из нити физ. модели.')


class RealThread2(Thread):
    def __init__(self, name: str, dispatcher: DispatcherAbstract, meta_queue: MetaQueue2,
                 initial_state: InitialStatusAbstract, reality: KillInterface, batch_size=1):
        Thread.__init__(self, name=name)
        self.__dispatcher = dispatcher
        # self.__meta_queue = meta_queue
        self.__meta_queue = MetaQueue2()
        self.__initial_states = initial_state
        self.__reality = reality
        self.__batch_size = batch_size

        # Итератор прохода по начальным состояниям изделия (исходным положениям)
        self.__iterator = iter(initial_state)
        # Время сна нити в ожидании сообщений в очереди
        # self.__sleep_time = 0.001
        # Условие окончания одного конкретного испытания.
        self.__finish_criterion = Finish()
        # self.__neuronet_command: Optional[StageControlCommands] = None

        # в блок визуализации будут отсылаться только испытания с этим Id
        self.__test_id_for_view: TestId = 0
        # атрибут уровня объекта для загрузки / выгрузки состояния изделия в / из очереди
        self.__test_id: TestId = -1
        # атрибут уровня объекта для загрузки / выгрузки состояния изделия в / из очереди
        self.__state: Optional[RealWorldStageStatusN] = RealWorldStageStatusN()
        # атрибут уровня объекта для загрузки / выгрузки состояния изделия в / из очереди
        self.__neuronet_command: Optional[StageControlCommands] = StageControlCommands(time_stamp=-1)

    def __set_initial_states(self) -> bool:
        """ Установка начальных положений изделия в испытаниях.

        :return: Поступил сигнал на завершение нити. """
        for i in range(self.__batch_size):
            # инициализация начальными данными
            state = next(self.__iterator)
            self.__dispatcher.put_zero_state(i, state)

            self.__meta_queue.state_to_neuronet.send_parsel(state, StageState, i)

        return self.__reality.kill

    def __command_waiting(self) -> bool:
        """ Ожидание команды из нейросети.

         :return: Поступил сигнал на завершение нити. """

        if self.__meta_queue.command_to_real.parsel_waiting():
            return self.__reality.kill

        parsel_type = self.__meta_queue.command_to_real.parsel_type

        if self.__meta_queue.command_to_real.parsel_type == ControlCommands:
            self.__meta_queue.command_to_real.receive_parsel(self.__neuronet_command)
        else:
            raise TypeError('Data type {0} from queue is unknown.'.format(parsel_type))

        return self.__reality.kill

    def __get_reinforcement(self, new_state: RealWorldStageStatusN, command: StageControlCommands):
        """ Подкрепление действий системы управления, которые привели к новому состоянию

        :param new_state: новое состояние изделия
        :param command: команда нейросети, которая привела к этому состоянию. """
        return ReinforcementValue(new_state.time_stamp,
                                           tools.Reinforcement.get_reinforcement(new_state, command)
                                           )

    def __send_reinforcement_to_neuronet(self, test_id: TestId, reinf: ReinforcementValue) -> bool:
        """ Передача подкрепления в нейросеть

        :param test_id: Идентификатор испытания
        :param reinf: Подкрепление данного испытания.
        :return: Поступил сигнал на завершение нити. """

        self.__meta_queue.reinf_to_neuronet.send_parsel(reinf, ReinforcementMessage, test_id)

        return self.__reality.kill

    def __test_end(self, test_id: TestId, new_state: RealWorldStageStatusN) -> bool:
        """ Проверка на окончание этого конкретного испытания.

        :param test_id: Идентификатор теста
        :param new_state: Новое состояние теста, проверяемое на то что он терминальный
        :return: Испытание закончилось? Новое исходное положение установлено? """

        is_new_state: bool = False
        if self.__finish_criterion.is_one_test_failed(new_state.position) \
                or self.__finish_criterion.is_one_test_success(new_state, tools.Reinforcement.accuracy):
            # отправляем в диспетчер новые исходные данные для закончившегося теста
            new_state = next(self.__iterator)
            # Когда источник начальных данных иссякает, то в список испытаний заносится None
            self.__dispatcher.put_zero_state(test_id, new_state)
            is_new_state = True
        return is_new_state

    def __send_new_state_to_receivers(self, test_id: TestId, new_state: RealWorldStageStatusN,
                                      is_new_state: bool) -> bool:
        """ Отправка нового состояния в очереди сообщений.

         :param test_id: Идентификатор теста
         :param new_state: Новое состояние изделия
         :param is_new_state: Состояние является начальным для нового теста?
         :return: Поступил сигнал на завершение нити. """

        self.__meta_queue.state_to_neuronet.send_parsel(new_state, StageState, test_id)
        self.__meta_queue.state_to_view.send_parsel(new_state, StageState, test_id)
        self.__meta_queue.state_to_stage_view.send_parsel(new_state, StageState, test_id)

        return self.__reality.kill

    def run(self):
        """ Note. Именно этот метод запускает в нити. """
        print('Вхоть в нить физ. модели')
        if self.__set_initial_states(): return

        while not self.__dispatcher.is_all_tests_ended() and not self.__reality.kill:

            if self.__command_waiting(): break

            self.__dispatcher.run(self.__test_id, self.__neuronet_command, self.__state)

            reinf = self.__get_reinforcement(self.__state, self.__neuronet_command)

            if self.__send_reinforcement_to_neuronet(self.__test_id, reinf): break

            is_new_state = self.__test_end(self.__test_id, self.__state)
            if self.__send_new_state_to_receivers(self.__test_id, self.__state, is_new_state): break

        print('Выход из нити физ. модели.')