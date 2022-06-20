""" Модуль визуализации происходящего с испытуемым объектом. """
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST, NE, NW
from queue import Queue
from stage import Sizes, BigMap
from kill_flags import KillNeuroNetThread, KillRealWorldThread, KillCommandsContainer
from physics import CheckPeriod
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from primiteves import StageMark
from win_interface import WindowsMSInterface
from structures import RealWorldStageStatusN
from tools import MetaQueue


class PoligonWindow(WindowsMSInterface):
    """
    Окно испытательного полигона, на котором рисуется траектория. Главное окно.

    """
    # Окно с увеличенным изображением ступени рисутется как "дочернее" окно полигона.
    # При закрытии окна полигона, закрывается и окно ступени.

    # def __init__(self, frameRate: int, queue: Queue, to_stage_queue: Queue, poligonWidth: float,
    #              poligonHeigt: float, poligonScale: float, stageSize: float, stageScale: float,
    #              killNeuronetFlag: KillNeuroNetThread, killRealityFlag: KillRealWorldThread):
    def __init__(self, queues: MetaQueue, poligonWidth: float,
                 poligonHeigt: float, poligonScale: float,
                 kill: KillCommandsContainer):
        """

        :param _frameRate: частота кадров (и поступления данных в очередь). Устарело.
        :param queues: контейнер очередей
        :param poligonWidth: ширина испытательного полигона (точка посадки находится посередине)
        :param poligonHeigt: высота испытательного полигона (от уровня грунта)
        :param poligonScale: масштаб отображения полигона. Количество метров на одну точку.
        :param kill: контейнер флагов отключения нитей
        """
        self.__poligonWidth = poligonWidth
        self.__poligonHeigt = poligonHeigt
        # масштаб изображения полигона пикселей на метр
        self.__poligonScale = poligonScale
        # стартовая точка испытаний в СКК
        self.__startPoint = complexChangeSystemCoordinatesUniversal(BigMap.startPointInPoligonCoordinates,
                                                                    BigMap.canvasOriginInPoligonCoordinates,
                                                                    0., True) / self.__poligonScale
        # точка посадки в СКК
        self.__endPoint = complexChangeSystemCoordinatesUniversal(BigMap.landingPointInPoligonCoordinates,
                                                                  BigMap.canvasOriginInPoligonCoordinates,
                                                                  0., True) / self.__poligonScale
        # текущая координата ЦМ ступени в СКК
        self.__currentPoint = self.__startPoint

        # self.__queue = queues.get("area")
        self.__queues = queues
        # Очередь для передачи данных в дочернее окно
        # self.__subQueue = queues.get_queue("stage")

        # self.__killNeuroNetFlag = killNeuronetFlag
        # self.__killRealityFlag = killRealityFlag
        self.__kill = kill

        # ВременнАя точка предыдущего состояния изделия
        self.__previousStatusTimeStamp = 0

        self.__root = Tk()
        self.__root.geometry("+300+100")
        self.__root.title("Trajectory")
        self.__canvas = Canvas(self.__root, width=self.__poligonWidth / self.__poligonScale, height=self.__poligonHeigt / self.__poligonScale)
        self.__canvas.pack()

        self._preparation_static_marks()
        self._preparation_movable_marks()
        # Отметка на экране ЦМ ступени в СКК
        self.__stageMark: StageMark
        self._create_objects_on_canvas()
        # Устаналвиваем обработчик закрытия главного окна
        self.__root.protocol("WM_DELETE_WINDOW", self.__onClosing)
        self.__root.after(0, self._draw)

        # Окно увеличенного изображения ступени в процессе посадки
        # self.__stageWindow = StageViewWindow(self.__root, stageSize, stageScale, -1, self.__subQueue, Queue())

    def _draw(self):
        # метод для периодического вызова и отрисовки на канве (точка траектории, данные по высоте, тангажу, крену и пр)
        transform: RealWorldStageStatusN = None
        # длительность предыдущего статуса изделия
        previousStatusDuration = 0
        # получение данных из внешних источников self.__anyQueue
        if not self.__queues.empty('area'):
            # print(self.__anyQueue.get())
            transform = self.__queues.get('area')

            previousStatusDuration = transform.time_stamp - self.__previousStatusTimeStamp
            self.__previousStatusTimeStamp = transform.time_stamp

            # преобразование из СКИП в СКК
            # inCanvasCoordSystem = RealWorldStageStatus()

            # (stageCanvasOrientation, stageCanvasPosition) = pointsListToNewCoordinateSystem(
            #     [transform.orientation2d, transform.vector2d],
            #     BigMap.canvasOriginInPoligonCoordinates,
            #     0., True
            # )
            (stageCanvasOrientation, stageCanvasPosition) = pointsListToNewCoordinateSystem(
                [transform.orientation, transform.position],
                BigMap.canvasOriginInPoligonCoordinates,
                0., True
            )

            # прозрачно ретранслируем блок данных в следующее окно
            # self.__subQueue.put(transform.lazy_copy())

        # отрисовка нового положения объектов на основании полученных данных из self.__anyQueue
        if transform is not None:
            # сдвинуть отметку ЦМ ступени
            if self.__stageMark.moveMark(self.__currentPoint, stageCanvasPosition / self.__poligonScale):
                # значение обновляем только тогда, если производился сдвиг отметки по канве
                # в противном случае, прошедшее значение смещения попало в трэшхолд и не является значимым
                self.__currentPoint = stageCanvasPosition / self.__poligonScale
            # self.__drawMassCenterMark()
            # рисовать
            # self.__stage.draw()
            # двигать
            # self.__stage.move(transform.vector2d)
            # вращать
            # self.__stage.rotate(transform.orientation2d)
            # print(transform.orientation2d.cardanus)
            # print(transform.text)
            # обновляем текущую точку ступени

        # запускаем отрисовку в цикл
        # self.__root.after(self.__frameRate, self.__draw)
        self.__root.after(CheckPeriod.to_mSec(previousStatusDuration), self._draw)

    def _preparation_static_marks(self):
        pass

    def _preparation_movable_marks(self):
        self.__stageMark = StageMark(self.__currentPoint, self.__canvas)

    def _create_objects_on_canvas(self):
        """ метод расставляет необходимые отметки по полигону (точка сброса ступени, точка посадки ступени и пр.) """
        # отметка точки посадки в виде треугольника
        self.__canvas.create_polygon([self.__endPoint.x - 10, self.__endPoint.y,
                                      self.__endPoint.x, self.__endPoint.y - 10,
                                      self.__endPoint.x + 10, self.__endPoint.y], fill="#1f1")
        # Отметка точки начала спуска ступени
        self.__canvas.create_oval([self.__startPoint.x - 5, self.__startPoint.y - 5,
                                   self.__startPoint.x + 5, self.__startPoint.y + 5], fill="green")

    def __onClosing(self):
        """ Обработчик закрытия главного окна. """
        # убиваем дополнительные нити
        self.__kill.neuro = True
        self.__kill.reality = True
        # закрываем главное окно
        self.__root.destroy()

    @property
    def root(self) -> Tk:
        return self.__root

    @property
    def canvas(self) -> Canvas:
        return self.__canvas



