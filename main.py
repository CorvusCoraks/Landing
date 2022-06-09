""" Главный файл. Диспетчер. Здесь создаются нити для параллельного исполнения """

from queue import Queue
from threading import Thread
from stage import Sizes, BigMap
from threads import reality_thread, neuronet_thread
from kill_flags import  KillNeuroNetThread, KillRealWorldThread, KillCommandsContainer
from win import WindowsMSView
from tools import MetaQueue, Un
from structures import RealWorldStageStatusN, ReinforcementValue, StageControlCommands
from typing import Dict

if __name__ == "__main__":
    # Частота считывания/передачи данных с датчиков ступени
    # todo устаревшее, убрать
    # frameRate = 1000

    # stage = Rocket()
    # qPoligon = Queue()

    # # Очередь для передачи величины подкрепления из нити реального мира в нейросеть
    # reinfFromRealToNeuroQueue = Queue()
    # # Очередь, через которую возвращаются данные о поведении ступени в реальном мире.
    # envFromRealWorldQueue = Queue()
    # # очередь для передачи информации из нити нейтросети в основную нить (нить канвы)
    # controlFromNeuroNetQueue = Queue()
    # # очередь, для передачи инфомации в нейросеть
    # envToNeuroNetQueue = Queue()

    # объект очередей передачи данных
    # queues = MetaQueue.getInstance()
    temp = {'area': RealWorldStageStatusN, 'stage': RealWorldStageStatusN, 'info': RealWorldStageStatusN,
            'neuro': RealWorldStageStatusN, 'reinf': ReinforcementValue, 'command': StageControlCommands}
    queues = MetaQueue.get_instance(temp)

    # # envFromRealWorldQueue: Queue
    # # Команда на завершение нити реального мира
    # killRealWorldThread = KillRealWorldThread(False)
    # # команда на завершение нити нейросети
    # killNeuronetThread = KillNeuroNetThread(False)

    # контейнер с командами на остановку нитей
    kill = KillCommandsContainer.get_instance()

    # Нить модели реального мира
    # realWorldThread = Thread(target=reality_thread, name="realWorldThread",
    #                          args=(envFromRealWorldQueue, envToNeuroNetQueue, controlFromNeuroNetQueue, reinfFromRealToNeuroQueue, killRealWorldThread, killNeuronetThread,))
    realWorldThread = Thread(target=reality_thread, name="realWorldThread", args=(queues, kill,))
    realWorldThread.start()

    # Для нейросети надо создать отдельную нить, так как tkinter может работать исключительно в главном потоке.
    # Т. е. отображение хода обучения идёт через tkinter в главной нити,
    # расчёт нейросети и физическое моделирование в отдельной нити

    # Создание отдельной нити для нейросети
    neuroNetThread = Thread(target=neuronet_thread,
                            name="NeuroNetThread",
                            args=(queues,
                                  kill,))
    neuroNetThread.start()

    # Размер полигона в метрах!
    # Мостшаб изображения
    # poligonScale = 4 / 1000  # при ширине полигона 300000 м., ширина окна - 1200 точек
    # количество метров на одну точку
    poligonScale = 1
    stageScale = 0.1
    # Создание окна (визуально показывает ситуацию) испытательного полигона. Главная, текущая нить.
    # poligonWindow = PoligonWindow(-1, envFromRealWorldQueue, Queue(),
    #                               BigMap.width, BigMap.height, poligonScale, Sizes.overallDimension, stageScale,
    #                               killNeuronetThread, killRealWorldThread)

    view = WindowsMSView()
    view.set_poligon_state(queues, BigMap.width, BigMap.height)
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
