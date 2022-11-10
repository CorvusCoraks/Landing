""" Главный файл. Диспетчер. Здесь создаются нити для параллельного исполнения """

from threading import Thread
from stage import Sizes, BigMap
from threads import neuronet_thread, RealThread
from kill_flags import KillCommandsContainer
from tkview.tkview import TkinterView
from tools import MetaQueue, InitialStatusAbstract, InitialStatus
from structures import RealWorldStageStatusN, ReinforcementValue, StageControlCommands
from typing import Dict, Any
from point import VectorComplex
from cmath import pi
from view import ViewInterface
from carousel.metaque import MetaQueueN
from datadisp.adisp import DispatcherAbstract
from datadisp.listdisp import ListDispatcher

if __name__ == "__main__":
    # максимальное количество тестовых посадок
    max_tests = 7

    # Очередь данных в вид испытательного полигона (из нити реальности)
    # Очередь данных в вид изделия (из нити реальности)
    # Очередь данных в вид информации о процессе (из нити реальности)
    # Очерердь данных в нейросеть (из нити реальности)
    # Очередь данных с подкреплениями (из нити реальности)
    # Очередь данных с управляющими командами (из нейросети)

    # note забавно, если не указать тип dict (или Dict[str, Any]) данной переменной,
    # то при передаче данных в MetaQueue.get_instance(temp)
    # будет ошибка несоответствия типа
    temp: Dict[str, Any] = {'area': RealWorldStageStatusN, 'stage': RealWorldStageStatusN, 'info': RealWorldStageStatusN,
            'neuro': RealWorldStageStatusN, 'reinf': ReinforcementValue, 'command': StageControlCommands}
    # объект очередей передачи данных
    queues = MetaQueue.get_instance(temp)

    # контейнер с командами на остановку нитей
    kill = KillCommandsContainer.get_instance()

    batch_size = 1
    queues_m: MetaQueueN = MetaQueueN(batch_size)
    dispatcher: DispatcherAbstract = ListDispatcher(batch_size, kill)

    # Нить модели реального мира
    realWorldThread: Thread = RealThread('realWorldThread', dispatcher, queues_m, InitialStatus(max_tests), kill, batch_size)
    realWorldThread.start()

    # Для нейросети надо создать отдельную нить, так как tkinter может работать исключительно в главном потоке.previous_status
    # Т. е. отображение хода обучения идёт через tkinter в главной нити,
    # расчёт нейросети и физическое моделирование в отдельной нити

    # Создание отдельной нити для нейросети
    neuroNetThread = Thread(target=neuronet_thread,
                            name="NeuroNetThread",
                            args=(queues_m,
                                  kill, batch_size))
    neuroNetThread.start()

    # Размер полигона в метрах!
    # Мостшаб изображения
    # poligon_scale = 4 / 1000  # при ширине полигона 300000 м., ширина окна - 1200 точек
    # количество метров на одну точку
    poligonScale = 1
    stageScale = 0.1
    # Создание окна (визуально показывает ситуацию) испытательного полигона. Главная, текущая нить.
    view: ViewInterface = TkinterView()
    view.set_poligon_state(queues_m, BigMap.width, BigMap.height)
    view.set_kill_threads(kill)
    view.set_stage_parameters(Sizes.topMassDistance,
                              Sizes.downMassDistance,
                              Sizes.downMassDistance,
                              Sizes.widthCenterBlock, Sizes.heightCenterBlock, Sizes.massCenterFromLandingPlaneDistance)

    view.create_poligon_view()
    view.create_stage_view()
    view.create_info_view()

    realWorldThread.join()
    neuroNetThread.join()
