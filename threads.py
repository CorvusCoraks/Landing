""" Класс нитей и инструментов работы с ними. """
# from builtins import function
import tools
from physics import Moving
from tools import Finish, MetaQueue, InitialStatus, InitialStatusAbstract
from threading import Thread
from training import start_nb
from kill_flags import KillCommandsContainer
from structures import RealWorldStageStatusN, ReinforcementValue, StageControlCommands
from datadisp.adisp import DispatcherAbstract
from carousel.metaque import MetaQueueN
from typing import Callable, Optional, Iterator, Tuple
from time import sleep
from carousel.atrolley import TestId
from abc import ABC
from con_intr.ifaces import ISocket


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


class RealThread(Thread):
    def __init__(self, name: str, dispatcher: DispatcherAbstract, data_transfer: ISocket, meta_queue: MetaQueueN, initial_state: InitialStatusAbstract, kill: KillCommandsContainer, batch_size=1):
        """

        :param name: Thread name
        :param dispatcher: диспетчер тестовых данных
        :param meta_queue:
        :param initial_state:
        :param kill:
        :param batch_size:
        """
        Thread.__init__(self, name=name)
        self.__dispatcher = dispatcher
        self.__data_transfer = data_transfer
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

    def __send_new_state_to_receivers(self, test_id: TestId, new_state: RealWorldStageStatusN, is_new_state: bool) -> bool:
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
