""" Класс нитей и инструментов работы с ними. """
import tools
from physics import Moving
from tools import Finish, MetaQueue
from threading import Thread
from training import start_nb
from kill_flags import KillCommandsContainer
from structures import RealWorldStageStatusN, ReinforcementValue


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


def reality_thread_2(queues: MetaQueue, kill: KillCommandsContainer,
                     max_tests: int, initial_status: RealWorldStageStatusN):
    """
    Функция моделирующая поведение ступени в реальной физической среде

    :param queues: Контейнер очередей передачи данных.
    :param kill: Контейнер команд на завершение нитей.
    :param max_tests: Количество запланированных испытательных посадок.
    :param initial_status: Начальное состояние (положение) изделия в СКИП
    """
    print("Вход в нить окружающей среды.")

    finish_control = Finish()

    # провести указанное число испытательных посадок
    for i in range(max_tests):
        # предыдущее состояние изделия
        previous_stage_status: RealWorldStageStatusN = initial_status
        # Информация о начальном положении изделия отправляется в нити
        queues.put(initial_status)

        while not kill.reality:
            # ждём команду для двигателей из нейросети на отправленное начальное состояние
            if not queues.empty("command"):
                command = queues.get("command")
                # команда, ведущая к новому состоянию, получена
                break
        else:
            break

        # цикл последовательной генерации состояний в процессе одной тестовой посадки
        # цикл прерывается, только если во время посадки случилась удача / неудача
        # или поступила команда на заверешение работы программы
        while not finish_control.is_one_test_failed(previous_stage_status.position) and not kill.reality:
            # очередное состояние изделия в СКИП
            new_stage_status = Moving.get_new_status(command, previous_stage_status)
            # Подкрепление действий системы управления, которые привели к новому состоянию
            reinforcement = ReinforcementValue(new_stage_status.time_stamp,
                                               tools.Reinforcement.get_reinforcement(new_stage_status, command)
                                               )

            # Отправляем величину подкрепления в НС
            queues.put(reinforcement)
            # добавить в выходную очередь очередную порцию информации о состоянии ступени
            queues.put(new_stage_status)

            # если удачная посадка
            if finish_control.is_one_test_success(new_stage_status, tools.Reinforcement.accuracy):
                # переходим к следующему испытанию
                break

            while not kill.reality:
                # ждём команду из нейросети на отправленное состояние и подкрепление
                if not queues.empty("command"):
                    command = queues.get("command")
                    # команда, ведущая к новому состоянию, получена
                    break
            else:
                break

            previous_stage_status = new_stage_status
            print("{0}. Time: {1}, Posititon: {2}, Velocyty: {3},\n Axelerantion: {4}, Orientation: {5}\n".
                  format(i, new_stage_status.time_stamp, new_stage_status.position, new_stage_status.velocity,
                         new_stage_status.acceleration, new_stage_status.orientation))

        # прекращаем испытания, завершение программы
        if kill.reality:
            break

    print("Завершение нити реальности.")
