""" Модуль визуализации состояния изделия в процесси испытания """
from primiteves import Text, Arrow, ArcArrowAndText, LineArrowAndText, AbstractOnCanvasMark, CenterMassMark
from tkinter import Canvas, Toplevel, Tk
from queue import Queue
from point import VectorComplex
from typing import List, Dict, AnyStr, Union
from win_firststage import FirstStage2
from stage import Sizes, BigMap
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import  CheckPeriod
from win_interface import WindowsMSInterface
from structures import RealWorldStageStatusN
from tools import MetaQueue

# OnCanvasStaticObjectDict = Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]

class StageViewWindow(WindowsMSInterface):
    """
    Класс окна вывода увеличенного изображения ступени и числовых характеристик
    """
    # def __init__(self, root: Tk, stageSize: float, stageScale: float, frameRate: int, anyQueue: Queue, to_info_queue: Queue, info_block: Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]):
    def __init__(self, root: Tk, stageSize: float, stageScale: float, queues: MetaQueue):
        """
        :param root: родительский оконный менеджер
        :param stageSize: максимальный характерный размер ступени, метров
        :param stageScale: масштаб изображения ступени на канве
        :param queues: очередь для передачи данных одного фрейма движения ступени
        """
        self.__stageSize = stageSize
        self.__stageScale = stageScale
        self.__anyQueue = queues.get_queue("stage")
        self.__to_info_queue = queues.get_queue("info")

        # ВременнАя точка предыдущего состояния изделия
        self.__previousStatusTimeStamp = 0

        # Ширина в пикселях, зарезервированная для текстовых меток
        self.__forTextLabels = 200
        # 1.3 эмпирическая добавка, так как центр тяжести ступени смещён от центра симметрии
        self.__moreWidth = 1.3
        self.__windowWidth = self.__stageSize / self.__stageScale * self.__moreWidth + self.__forTextLabels
        self.__windowHeight = self.__stageSize / self.__stageScale * self.__moreWidth
        # Виртуальная вертикальная линия, проходящая по двоеточиям (по середине) текстовых меток
        # Необходима для компоновки текстовых меток
        self.__centerTextLine = self.__stageSize / self.__stageScale * self.__moreWidth + self.__forTextLabels / 2

        self.__root = Toplevel(root)
        self.__root.geometry("+{0:d}+{1:d}".format(600, 100))
        self.__root.title("Stage view")
        self.__canvas = Canvas(self.__root, width=self.__windowWidth, height=self.__windowHeight)
        self.__canvas.pack()

        # отметки привязанные к к канве
        self.__canvasLinkedMarks: Dict[AnyStr, Union[LineArrowAndText, ArcArrowAndText]] = None

        # отметки привязанные к изображению ступени
        self.__stageLinkedMarks: List[AbstractOnCanvasMark] = []
        # Координаты точки предварительной сборки (левый верхний угол прямоугольника ступени) в СКК
        assemblingPoint = VectorComplex.getInstance(0., 0.)
        # Координаты центра масс в СКК
        # massCenterInCanvas: VectorComplex = assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__stageScale,
        #                                                Sizes.heightCenterBlock * 2 / 3 / self.__stageScale)

        self.__mass_center_on_canvas: VectorComplex = assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__stageScale,
                                                       Sizes.heightCenterBlock * 2 / 3 / self.__stageScale)
        self.__orientation = VectorComplex.getInstance(0., -1.)

        self._preparation_static_marks()
        self._preparation_movable_marks()

        self.__stage = FirstStage2(self.__canvas, assemblingPoint, self.__mass_center_on_canvas, self.__stageLinkedMarks, self.__stageScale)

        self._create_objects_on_canvas()

        self.__root.after(0, self._draw)

    def _draw(self):
        """ метод для периодической перерисовки объектов на канве """

        transform: RealWorldStageStatusN = None
        # Длительность предыдущего состояния
        previousStatusDuration = 0

        # получение данных из внешних источников self.__anyQueue
        if not self.__anyQueue.empty():
            transform = self.__anyQueue.get()

            previousStatusDuration = transform.timeStamp - self.__previousStatusTimeStamp
            self.__previousStatusTimeStamp = transform.timeStamp

            self.__to_info_queue.put(transform.lazyCopy)

        # отрисовка нового положения объектов на основании полученных данных из очереди
        if transform is not None:
            self.__change_static_marks(transform)
            if self.__canvasLinkedMarks is not None: self.__change_movable_marks(transform)

        # запускаем отрисовку цикл
        self.__root.after(CheckPeriod.to_mSec(previousStatusDuration), self._draw)
        # self.__root.after(500, self._draw)


    def __change_static_marks(self, transform: RealWorldStageStatusN):
        """ Обновление неподвижных отметок в соответствии с актуальной информацией """
        # переводим свободный вектор расстояния в СКК
        distanceVectorCCS = complexChangeSystemCoordinatesUniversal(transform.position,
                                                                    VectorComplex.getInstance(0., 0.), 0., True)
        self.__canvasLinkedMarks["distance"].setInfo(abs(transform.position), distanceVectorCCS)
        # переводим свободный вектор скорости в СКК
        velocityVectorCCS = complexChangeSystemCoordinatesUniversal(transform.velocity,
                                                                    VectorComplex.getInstance(0., 0.), 0., True)
        # self.__lineVelocityInfo.setInfo(abs(transform.velocity), velocityVectorCCS)
        self.__canvasLinkedMarks["line_velocity"].setInfo(abs(transform.velocity), velocityVectorCCS)
        # переводим свободный вектор ускорения в СКК
        axelerationVectorCCS = complexChangeSystemCoordinatesUniversal(transform.axeleration,
                                                                       VectorComplex.getInstance(0., 0.), 0., True)
        # self.__lineAxelerationInfo.setInfo(abs(transform.axeleration), axelerationVectorCCS)
        self.__canvasLinkedMarks["line_accel"].setInfo(abs(transform.axeleration), axelerationVectorCCS)

        # self.__angleVelocity.setInfo(transform.angularVelocity)
        self.__canvasLinkedMarks["angle_velocity"].setInfo(transform.angularVelocity)

        # self.__angleAxeleration.setInfo(transform.angularAxeleration)
        self.__canvasLinkedMarks["angle_accel"].setInfo(transform.angularAxeleration)

    def __change_movable_marks(self, transform: RealWorldStageStatusN):
        """ Обновление подвижных отметок в соответствии с актуальной информацией. """
        # На всякий случай вытаскиваем величину. Пока не понятно зачем она нам понадобится.
        BigMap.stageViewOriginInPoligonCoordinates = transform.position
        stageViewOrientation: VectorComplex

        # Вектор ориентации это - свободный вектор. От нуля любой СК.
        stageViewOrientation, _ = pointsListToNewCoordinateSystem(
            [transform.orientation, transform.orientation],
            VectorComplex.getInstance(0., 0.),
            0., True
        )

        # вращать метки, привязанные к изображению ступени
        for value in self.__stageLinkedMarks:
            value.rotate(stageViewOrientation, self.__orientation)
        # текстовые метки не вращаем

        # Вращаем стрелки индикаторов
        # self.__velocityArrow.rotate(transform.stageStatus.velocity, self.__velocityArrow)

        self.__orientation = stageViewOrientation

    def _preparation_static_marks(self):
        pass

    def _preparation_movable_marks(self):
        # стрелка ориентации, ставится в центре тяжести изображения ступени
        self.__arrow = Arrow(self.__canvas, self.__mass_center_on_canvas,
                             VectorComplex.getInstance(self.__mass_center_on_canvas.x,
                                                       self.__mass_center_on_canvas.y + self.__orientation.y * 60.),
                             5, "blue", self.__mass_center_on_canvas)
        self.__stageLinkedMarks.append(self.__arrow)
        # self.__testArrow = Arrow(self.__canvas, VectorComplex.getInstance(10, 10), VectorComplex.getInstance(10, 60), 5,
        #                          "blue")

        # отметка центра масс
        self.__massCenterMark = CenterMassMark(self.__canvas, self.__mass_center_on_canvas, fill="blue")
        # del self.__mass_center_on_canvas
        self.__stageLinkedMarks.append(self.__massCenterMark)

    def _create_objects_on_canvas(self):
        """
        Отрисовываем на канве графические элементы (кроме информационного блока)
        """
        self.__stage.createOnCanvas()

        for value in self.__stageLinkedMarks:
            value.createOnCanvas()
        pass

    @property
    def root(self):
        return self.__root

    @property
    def canvas(self):
        return self.__canvas

    def create_info_block_on_canvas(self, block: Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]):
        """ Создать блок информации о процессе на канве """
        self.__canvasLinkedMarks = block

        for value in self.__canvasLinkedMarks.values():
            value.createOnCanvas()

        self.__canvasLinkedMarks["line_velocity"].direction = VectorComplex.getInstance(1., 0.)

class InfoView():
    """ Блок информации о процессе. """
    def __init__(self):
        pass

    @classmethod
    def get_info_block(cls, canvas: Canvas) -> Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]:
        """ Получить блок информации о процессе """
        arcAndTextTest = ArcArrowAndText(canvas, VectorComplex.getInstance(300, 300), "Header", 120.,
                                                "Legend", "green")

        lineVelocityInfo = LineArrowAndText(canvas, VectorComplex.getInstance(450, 200), "Velocity", 120.,
                                                   "{0:7.2f} m/s", "green")
        lineAxelerationInfo = LineArrowAndText(canvas, VectorComplex.getInstance(550, 200), "Axeleration",
                                                      120., "{0:7.2f} m/s^2", "green")
        angleVelocity = ArcArrowAndText(canvas, VectorComplex.getInstance(450, 300), "Velocity", 120.,
                                               "{0:7.2f} r/s", "green")
        angleAxeleration = ArcArrowAndText(canvas, VectorComplex.getInstance(550, 300), "Axeleration",
                                                  120., "00,00 r/s^2", "green")
        stageDistance = LineArrowAndText(canvas, VectorComplex.getInstance(450, 350), "Distance", 120.,
                                                "{0:7.2f} m", "green")
        stageAltitude = LineArrowAndText(canvas, VectorComplex.getInstance(550, 350), "Altitude", 120.,
                                                "0000,00 m", "green")

        return {"test": arcAndTextTest, "line_velocity": lineVelocityInfo, "line_accel": lineAxelerationInfo, "angle_velocity": angleVelocity,
               "angle_accel": angleAxeleration, "distance": stageDistance, "altitude": stageAltitude}

