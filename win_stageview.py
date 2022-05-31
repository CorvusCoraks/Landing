from primiteves import Text, Arrow, ArcArrowAndText, LineArrowAndText, AbstractOnCanvasMark, CenterMassMark
from tkinter import Canvas, Toplevel, Tk
from queue import Queue
from point import VectorComplex
from typing import List
from win_firststage import FirstStage2
from stage import Sizes, BigMap
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import  CheckPeriod
from tools import WindowsMSInterface


class StageViewWindow(WindowsMSInterface):
    """
    Класс окна вывода увеличенного изображения ступени и числовых характеристик
    """
    def __init__(self, root: Tk, stageSize: float, stageScale: float, frameRate: int, anyQueue: Queue):
        """
        :param root:
        :param stageSize: максимальный характерный размер ступени, метров
        :param stageScale: масштаб изображения ступени на канве
        :param frameRate: частота "кадров" - частота, с которой окно запрашивает данные из очереди
        :param anyQueue: очередь для передачи данных одного фрейма движения ступени
        """
        self.__stageSize = stageSize
        self.__stageScale = stageScale
        self.__anyQueue = anyQueue
        # self.__frameRate = -1  # частота кадров

        # ВременнАя точка предыдущего состояния изделия
        self.__previousStatusTimeStamp = 0

        # размеры окна в зависимости от максимального размера ступени и масштаба её изображения
        # self.__windowWidth = self.__stageSize / self.__stageScale * 4
        # self.__windowHeight = self.__stageSize / self.__stageScale * 2 * 4
        # self.__leftTextBorder = self.__stageSize / self.__stageScale
        # Ширина в пикселях, зарезервированная для текстовых меток
        self.__forTextLabels = 200
        # 1.3 эмпирическая добавка, так как центр тяжести ступени смещён от центра симметрии
        self.__moreWidth = 1.3
        self.__windowWidth = self.__stageSize / self.__stageScale * self.__moreWidth + self.__forTextLabels
        self.__windowHeight = self.__stageSize / self.__stageScale * self.__moreWidth
        # Виртуальная вертикальная линия, проходящая по двоеточиям (по середине) текстовых меток
        # Необходима для компоновки текстовых меток
        self.__centerTextLine = self.__stageSize / self.__stageScale * self.__moreWidth + self.__forTextLabels / 2

        # size = 600
        # self.__root = Tk()
        self.__root = Toplevel(root)
        self.__root.geometry("+{0:d}+{1:d}".format(600, 100))
        # self.__root.geometry("300x600+600+100")
        self.__root.title("Stage view")
        self.__canvas = Canvas(self.__root, width=self.__windowWidth, height=self.__windowHeight)
        # self.__canvas = Canvas(self.__root, width=)

        # отметки привязанные к к канве
        self.__canvasLinkedMarks: List[AbstractOnCanvasMark] = []
        # отметки привязанные к изображению ступени
        self.__stageLinkedMarks: List[AbstractOnCanvasMark] = []
        # Координаты точки предварительной сборки (левый верхний угол прямоугольника ступени) в СКК
        assemblingPoint = VectorComplex.getInstance(0., 0.)
        # Координаты центра масс в СКК
        # massCenterInCanvas: VectorComplex = assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__stageScale,
        #                                                Sizes.heightCenterBlock * 2 / 3 / self.__stageScale)
        # весьма временный атрибут для передачи значения в одну из внутренних функций класса.
        # Там же этот атрибут и будет убит
        self.__mass_center_on_canvas: VectorComplex = assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__stageScale,
                                                       Sizes.heightCenterBlock * 2 / 3 / self.__stageScale)
        self.__orientation = VectorComplex.getInstance(0., -1.)
        # Создаём информационные отметки в окне
        # self.__marksOnStageWindow(massCenterInCanvas)
        self._preparation_static_marks()
        self._preparation_movable_marks()


        self.__canvas.pack()
        self.__stage = FirstStage2(self.__canvas, assemblingPoint, massCenterInCanvas, self.__stageLinkedMarks, self.__stageScale)

        # Смещение собранной конструкции в конечную точку нахождения на канве
        # self.__stage.move(VectorComplex.getInstance(50., 0.))

        # self.__root.after(1000, function, self.__root)
        # self.__root.after(1000, function, self.__root, 0, True)
        # self.__stage.pack_foget
        # self.__createObjectsOnCanvas()
        self._create_objects_on_canvas()
        # self.__root.after(self.__frameRate, self.__draw)
        # self.__root.after(0, self.__draw)
        self.__root.after(0, self._draw)
        self.__root.mainloop()

    def _draw(self):
        """ метод для периодической перерисовки объектов на канве """

        transform = None
        # Длительность предыдущего состояния
        previousStatusDuration = 0

        # получение данных из внешних источников self.__anyQueue
        if not self.__anyQueue.empty():
            transform = self.__anyQueue.get()

            previousStatusDuration = transform.timeStamp - self.__previousStatusTimeStamp
            self.__previousStatusTimeStamp = transform.timeStamp

        # отрисовка нового положения объектов на основании полученных данных из очереди
        if transform is not None:
            # изменить значение
            # self.__valuePosition.text = (transform.position, transform.position.y)

            # переводим свободный вектор расстояния в СКК
            distanceVectorCCS = complexChangeSystemCoordinatesUniversal(transform.position,
                                                                        VectorComplex.getInstance(0., 0.), 0., True)
            self.__stageDistance.setInfo(abs(transform.position), distanceVectorCCS)
            # переводим свободный вектор скорости в СКК
            velocityVectorCCS = complexChangeSystemCoordinatesUniversal(transform.velocity,
                                                                        VectorComplex.getInstance(0., 0.), 0., True)
            self.__lineVelocityInfo.setInfo(abs(transform.velocity), velocityVectorCCS)
            # переводим свободный вектор ускорения в СКК
            axelerationVectorCCS = complexChangeSystemCoordinatesUniversal(transform.axeleration,
                                                                           VectorComplex.getInstance(0., 0.), 0., True)
            self.__lineAxelerationInfo.setInfo(abs(transform.axeleration), axelerationVectorCCS)

            self.__angleVelocity.setInfo(transform.angularVelocity)

            self.__angleAxeleration.setInfo(transform.angularAxeleration)

            # На всякий случай вытаскиваем величину. Пока не понятно зачем она нам понадобится.
            BigMap.stageViewOriginInPoligonCoordinates = transform.position
            stageViewOrientation: VectorComplex

            # Вектор ориентации это - свободный вектор. От нуля любой СК.
            stageViewOrientation, _ = pointsListToNewCoordinateSystem(
                [transform.orientation, transform.orientation],
                VectorComplex.getInstance(0., 0.),
                0., True
            )

            # print("{0} Get. Orientation: {1}".format(transform.text, stageViewOrientation))

            # value: Arrow
            # вращать метки, привязанные к изображению ступени
            for value in self.__stageLinkedMarks:
                value.rotate(stageViewOrientation, self.__orientation)
            # текстовые метки не вращаем

            # Вращаем стрелки индикаторов
            # self.__velocityArrow.rotate(transform.stageStatus.velocity, self.__velocityArrow)

            self.__orientation = stageViewOrientation

        # запускаем отрисовку цикл
        # self.__root.after(self.__frameRate, self.__draw)
        # duration = CheckPeriod.to_Sec()
        self.__root.after(CheckPeriod.to_mSec(previousStatusDuration), self._draw)

    def _preparation_static_marks(self):
        self.__arcAndTextTest = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(300, 300), "Header", 120.,
                                                "Legend", "green")

        self.__lineVelocityInfo = LineArrowAndText(self.__canvas, VectorComplex.getInstance(450, 200), "Velocity", 120.,
                                                   "{0:7.2f} m/s", "green")
        self.__lineAxelerationInfo = LineArrowAndText(self.__canvas, VectorComplex.getInstance(550, 200), "Axeleration",
                                                      120., "{0:7.2f} m/s^2", "green")
        self.__angleVelocity = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(450, 300), "Velocity", 120.,
                                               "{0:7.2f} r/s", "green")
        self.__angleAxeleration = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(550, 300), "Axeleration",
                                                  120., "00,00 r/s^2", "green")
        self.__stageDistance = LineArrowAndText(self.__canvas, VectorComplex.getInstance(450, 350), "Distance", 120.,
                                                "{0:7.2f} m", "green")
        self.__stageAltitude = LineArrowAndText(self.__canvas, VectorComplex.getInstance(550, 350), "Altitude", 120.,
                                                "0000,00 m", "green")

        self.__canvasLinkedMarks.extend([self.__arcAndTextTest,
                                         self.__lineVelocityInfo, self.__lineAxelerationInfo,
                                         self.__angleVelocity, self.__angleAxeleration,
                                         self.__stageDistance, self.__stageAltitude])

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
        del self.__mass_center_on_canvas
        self.__stageLinkedMarks.append(self.__massCenterMark)

    def _create_objects_on_canvas(self):
        """
        Отрисовываем на канве графические элементы
        """
        self.__stage.createOnCanvas()

        for value in self.__stageLinkedMarks:
            value.createOnCanvas()

        for value in self.__canvasLinkedMarks:
            value.createOnCanvas()

        self.__lineVelocityInfo.direction = VectorComplex.getInstance(1., 0.)
        # self.__arcAndTextTest.direction = PsevdoArcArrow.ZERO

    # def __marksOnStageWindow(self, massCenterInCanvas: VectorComplex):
    #     """
    #         Создаём отметки в окне изображения ступени.
    #     """
    #     # тестовая точка на экране, показывающая ориентацию СКК. Монтажное положение ЦМ в СКК
    #     # test = [Sizes.widthCenterBlock / 2 / self.__stageScale, Sizes.heightCenterBlock * 2 / 3 / self.__stageScale]
    #     # self.__canvas.create_oval([test[0] - 5, test[1] - 5, test[0] + 5, test[1] + 5], fill="blue")
    #     # self.__canvas.create_oval([massCenterInCanvas.x - 5, massCenterInCanvas.y - 5,
    #     #                            massCenterInCanvas.x + 5, massCenterInCanvas.y + 5], fill="blue")
    #
    #     # стрелка ориентации, ставится в центре тяжести изображения ступени
    #     self.__arrow = Arrow(self.__canvas, massCenterInCanvas,
    #                          VectorComplex.getInstance(massCenterInCanvas.x,
    #                                                    massCenterInCanvas.y + self.__orientation.y * 60.),
    #                          5, "blue", massCenterInCanvas)
    #     self.__stageLinkedMarks.append(self.__arrow)
    #     # self.__testArrow = Arrow(self.__canvas, VectorComplex.getInstance(10, 10), VectorComplex.getInstance(10, 60), 5,
    #     #                          "blue")
    #
    #     # отметка центра масс
    #     self.__massCenterMark = CenterMassMark(self.__canvas, massCenterInCanvas, fill="blue")
    #     self.__stageLinkedMarks.append(self.__massCenterMark)
    #
    #     # Текстовая информация
    #     # # Метки
    #     # self.__labelVhorizontal = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine, 50),
    #     #                                "Vertical Velocity: ", NE, "green")
    #     # self.__labelVvertical = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine, 70),
    #     #                              "Horisontal Velocity: ", NE, "green")
    #     # self.__labelPosition = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine, 100),
    #     #                                "Position: ", NE, "green")
    #     # self.__testArc = PsevdoArcArrow(self.__canvas, VectorComplex.getInstance(400, 300))
    #     self.__arcAndTextTest = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(300, 300), "Header", 120., "Legend", "green")
    #
    #     self.__lineVelocityInfo = LineArrowAndText(self.__canvas, VectorComplex.getInstance(450, 200), "Velocity", 120., "{0:7.2f} m/s", "green")
    #     self.__lineAxelerationInfo = LineArrowAndText(self.__canvas, VectorComplex.getInstance(550, 200), "Axeleration", 120., "{0:7.2f} m/s^2", "green")
    #     self.__angleVelocity = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(450, 300), "Velocity", 120., "{0:7.2f} r/s", "green")
    #     self.__angleAxeleration = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(550, 300), "Axeleration", 120., "00,00 r/s^2", "green")
    #     self.__stageDistance = LineArrowAndText(self.__canvas, VectorComplex.getInstance(450, 350), "Distance", 120., "{0:7.2f} m", "green")
    #     self.__stageAltitude = LineArrowAndText(self.__canvas, VectorComplex.getInstance(550, 350), "Altitude", 120., "0000,00 m", "green")
    #
    #
    #
    #
    #     # velocityPinPoint = VectorComplex.getInstance(self.__centerTextLine, 200)
    #     # self.__velocityArrow = Arrow(self.__canvas,
    #     #                              VectorComplex.getInstance(velocityPinPoint.x, velocityPinPoint.y + 20),
    #     #                              VectorComplex.getInstance(velocityPinPoint.x, velocityPinPoint.y - 20),
    #     #                              5, "green", velocityPinPoint)
    #
    #     self.__canvasLinkedMarks.extend([self.__arcAndTextTest,
    #                                      self.__lineVelocityInfo, self.__lineAxelerationInfo,
    #                                      self.__angleVelocity, self.__angleAxeleration,
    #                                      self.__stageDistance, self.__stageAltitude])
    #
    #     # # Значения
    #     # self.__valueVhorizontal = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine + 10, 50),
    #     #                                "000,000 m/s", NW, "green")
    #     # self.__valueVvertical = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine + 10, 70),
    #     #                              "000,000 m/s", NW, "green")
    #     # # self.__valuePosition = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine + 10, 90),
    #     # #                             "x = 000.000,\ny = 000.000", NW)
    #     # self.__valuePosition = StageViewWindow.PositionLabelText(self.__canvas, VectorComplex.getInstance(
    #     #     self.__centerTextLine + 10, 90),(0., 0.), NW)
    #     # self.__canvasLinkedMarks.extend([self.__valueVhorizontal, self.__valueVvertical, self.__valuePosition])



    # def __createObjectsOnCanvas(self):
    #     """
    #     Отрисовываем на канве графические элементы
    #     """
    #     self.__stage.createOnCanvas()
    #
    #     for value in self.__stageLinkedMarks:
    #         value.createOnCanvas()
    #
    #     for value in self.__canvasLinkedMarks:
    #         value.createOnCanvas()
    #
    #     self.__lineVelocityInfo.direction = VectorComplex.getInstance(1., 0.)
    #     # self.__arcAndTextTest.direction = PsevdoArcArrow.ZERO

    # def canvas(self):
    #     return self.__canvas

    # def __draw(self):
    #     """ метод для периодической перерисовки объектов на канве """
    #
    #     transform = None
    #     # Длительность предыдущего состояния
    #     previousStatusDuration = 0
    #
    #     # получение данных из внешних источников self.__anyQueue
    #     if not self.__anyQueue.empty():
    #         transform = self.__anyQueue.get()
    #
    #         previousStatusDuration = transform.timeStamp - self.__previousStatusTimeStamp
    #         self.__previousStatusTimeStamp = transform.timeStamp
    #
    #     # отрисовка нового положения объектов на основании полученных данных из очереди
    #     if transform is not None:
    #         # изменить значение
    #         # self.__valuePosition.text = (transform.position, transform.position.y)
    #
    #         # переводим свободный вектор расстояния в СКК
    #         distanceVectorCCS = complexChangeSystemCoordinatesUniversal(transform.position,
    #                                                                     VectorComplex.getInstance(0., 0.), 0., True)
    #         self.__stageDistance.setInfo(abs(transform.position), distanceVectorCCS)
    #         # переводим свободный вектор скорости в СКК
    #         velocityVectorCCS = complexChangeSystemCoordinatesUniversal(transform.velocity,
    #                                                                     VectorComplex.getInstance(0., 0.), 0., True)
    #         self.__lineVelocityInfo.setInfo(abs(transform.velocity), velocityVectorCCS)
    #         # переводим свободный вектор ускорения в СКК
    #         axelerationVectorCCS = complexChangeSystemCoordinatesUniversal(transform.axeleration,
    #                                                                        VectorComplex.getInstance(0., 0.), 0., True)
    #         self.__lineAxelerationInfo.setInfo(abs(transform.axeleration), axelerationVectorCCS)
    #
    #         self.__angleVelocity.setInfo(transform.angularVelocity)
    #
    #         self.__angleAxeleration.setInfo(transform.angularAxeleration)
    #
    #         # На всякий случай вытаскиваем величину. Пока не понятно зачем она нам понадобится.
    #         BigMap.stageViewOriginInPoligonCoordinates = transform.position
    #         stageViewOrientation: VectorComplex
    #
    #         # Вектор ориентации это - свободный вектор. От нуля любой СК.
    #         stageViewOrientation, _ = pointsListToNewCoordinateSystem(
    #             [transform.orientation, transform.orientation],
    #             VectorComplex.getInstance(0., 0.),
    #             0., True
    #         )
    #
    #         # print("{0} Get. Orientation: {1}".format(transform.text, stageViewOrientation))
    #
    #         # value: Arrow
    #         # вращать метки, привязанные к изображению ступени
    #         for value in self.__stageLinkedMarks:
    #             value.rotate(stageViewOrientation, self.__orientation)
    #         # текстовые метки не вращаем
    #
    #         # Вращаем стрелки индикаторов
    #         # self.__velocityArrow.rotate(transform.stageStatus.velocity, self.__velocityArrow)
    #
    #         self.__orientation = stageViewOrientation
    #
    #     # запускаем отрисовку цикл
    #     # self.__root.after(self.__frameRate, self.__draw)
    #     # duration = CheckPeriod.to_Sec()
    #     self.__root.after(CheckPeriod.to_mSec(previousStatusDuration), self.__draw)