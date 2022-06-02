""" Модуль визуализации происходящего с испытуемым объектом. """
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST, NE, NW
from queue import Queue
from point import VectorComplex
from stage import Sizes, BigMap
from kill_flags import KillNeuroNetThread, KillRealWorldThread
from physics import CheckPeriod
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from win_stageview import StageViewWindow
from primiteves import StageMark
from tools import WindowsMSInterface
from structures import RealWorldStageStatusN


class PoligonWindow(WindowsMSInterface):
    """
    Окно испытательного полигона, на котором рисуется траектория. Главное окно.

    """
    # Окно с увеличенным изображением ступени рисутется как "дочернее" окно полигона.
    # При закрытии окна полигона, закрывается и окно ступени.

    def __init__(self, frameRate: int, queue: Queue, to_stage_queue: Queue, poligonWidth: float,
                 poligonHeigt: float, poligonScale: float, stageSize: float, stageScale: float,
                 killNeuronetFlag: KillNeuroNetThread, killRealityFlag: KillRealWorldThread):
        """

        :param _frameRate: частота кадров (и поступления данных в очередь)
        :param queue: очередь данных для отрисовки траектории в главном окне.
        :param poligonWidth: ширина испытательного полигона (точка посадки находится посередине)
        :param poligonHeigt: высота испытательного полигона (от уровня грунта)
        :param poligonScale: масштаб отображения полигона. Количество метров на одну точку.
        :param stageSize: максимальный характерный размер ступени, метров
        :param stageScale: масштаб изображения ступени на канве увеличенного изображения
        :param killNeuronetFlag: флаг-команда на завершение нити нейросети
        :param killRealityFlag: флаг-команда на завершение нити состояния ступени
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

        self.__queue = queue
        # Очередь для передачи данных в дочернее окно
        self.__subQueue =to_stage_queue

        self.__killNeuroNetFlag = killNeuronetFlag
        self.__killRealityFlag = killRealityFlag

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
        if not self.__queue.empty():
            # print(self.__anyQueue.get())
            transform = self.__queue.get()

            previousStatusDuration = transform.timeStamp - self.__previousStatusTimeStamp
            self.__previousStatusTimeStamp = transform.timeStamp

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
            self.__subQueue.put(transform.lazyCopy())

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
        self.__killNeuroNetFlag.kill = True
        self.__killRealityFlag.kill = True
        # закрываем главное окно
        self.__root.destroy()

    @property
    def root(self):
        return self.__root

    @property
    def canvas(self):
        return self.__canvas




# class StageViewWindow():
#     """
#     Класс окна вывода увеличенного изображения ступени и числовых характеристик
#     """
#     class PositionLabelText(Text):
#         """
#         Текст на канве с информацией о текущих координатах ступени.
#         """
#         # todo не нужный класс?
#         def __init__(self, canvas: Canvas, start: VectorComplex, position: tuple, textAnchor):
#             super().__init__(canvas, start, "tempValue", textAnchor, "green")
#             self.__stringTemplate = "x = {0},\n y = {1}"
#             # self.text = self.__stringTemplate
#             # self.__position = position
#             self.text = position
#
#         @property
#         def text(self):
#             return super().text
#
#         @text.setter
#         def text(self, position: tuple):
#             """
#             :param value: кортеж из двух элементов (x. y)
#             """
#             x, y = position
#             # Присваивание свойству суперкласса только таким кривым образом....
#             # https://stackoverflow.com/questions/10810369/python-super-and-setting-parent-class-property
#             super(self.__class__, self.__class__).text.fset(self, self.__stringTemplate.format(x, y))
#
#     def __init__(self, root: Tk, stageSize: float, stageScale: float, frameRate: int, anyQueue: Queue):
#         """
#         :param root:
#         :param stageSize: максимальный характерный размер ступени, метров
#         :param stageScale: масштаб изображения ступени на канве
#         :param frameRate: частота "кадров" - частота, с которой окно запрашивает данные из очереди
#         :param anyQueue: очередь для передачи данных одного фрейма движения ступени
#         """
#         self.__stageSize = stageSize
#         self.__stageScale = stageScale
#         self.__anyQueue = anyQueue
#         # self.__frameRate = -1  # частота кадров
#
#         # ВременнАя точка предыдущего состояния изделия
#         self.__previousStatusTimeStamp = 0
#
#         # размеры окна в зависимости от максимального размера ступени и масштаба её изображения
#         # self.__windowWidth = self.__stageSize / self.__stageScale * 4
#         # self.__windowHeight = self.__stageSize / self.__stageScale * 2 * 4
#         # self.__leftTextBorder = self.__stageSize / self.__stageScale
#         # Ширина в пикселях, зарезервированная для текстовых меток
#         self.__forTextLabels = 200
#         # 1.3 эмпирическая добавка, так как центр тяжести ступени смещён от центра симметрии
#         self.__moreWidth = 1.3
#         self.__windowWidth = self.__stageSize / self.__stageScale * self.__moreWidth + self.__forTextLabels
#         self.__windowHeight = self.__stageSize / self.__stageScale * self.__moreWidth
#         # Виртуальная вертикальная линия, проходящая по двоеточиям (по середине) текстовых меток
#         # Необходима для компоновки текстовых меток
#         self.__centerTextLine = self.__stageSize / self.__stageScale * self.__moreWidth + self.__forTextLabels / 2
#
#         # size = 600
#         # self.__root = Tk()
#         self.__root = Toplevel(root)
#         self.__root.geometry("+{0:d}+{1:d}".format(600, 100))
#         # self.__root.geometry("300x600+600+100")
#         self.__root.title("Stage view")
#         self.__canvas = Canvas(self.__root, width=self.__windowWidth, height=self.__windowHeight)
#         # self.__canvas = Canvas(self.__root, width=)
#
#         # отметки привязанные к к канве
#         self.__canvasLinkedMarks: List[AbstractOnCanvasMark] = []
#         # отметки привязанные к изображению ступени
#         self.__stageLinkedMarks: List[AbstractOnCanvasMark] = []
#         # Координаты точки предварительной сборки (левый верхний угол прямоугольника ступени) в СКК
#         assemblingPoint = VectorComplex.getInstance(0., 0.)
#         # Координаты центра масс в СКК
#         massCenterInCanvas = assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__stageScale,
#                                                        Sizes.heightCenterBlock * 2 / 3 / self.__stageScale)
#         self.__orientation = VectorComplex.getInstance(0., -1.)
#         # Создаём информационные отметки в окне
#         self.__marksOnStageWindow(massCenterInCanvas)
#
#         self.__canvas.pack()
#         self.__stage = FirstStage2(self.__canvas, assemblingPoint, massCenterInCanvas, self.__stageLinkedMarks, self.__stageScale)
#
#         # Смещение собранной конструкции в конечную точку нахождения на канве
#         # self.__stage.move(VectorComplex.getInstance(50., 0.))
#
#         # self.__root.after(1000, function, self.__root)
#         # self.__root.after(1000, function, self.__root, 0, True)
#         # self.__stage.pack_foget
#         self.__createObjectsOnCanvas()
#         # self.__root.after(self.__frameRate, self.__draw)
#         self.__root.after(0, self.__draw)
#         self.__root.mainloop()
#
#     def __draw0(self):
#         # todo не нужная функция?
#         massCenterInCanvas = VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__stageScale,
#                                                    Sizes.heightCenterBlock * 2 / 3 / self.__stageScale)
#         # создаём список отметок, привязанных к центру масс ступени + просто создаём отметки не привязанные к ступени
#         # self.__marksOnStage = self.__marksOnStageWindow(massCenterInCanvas)
#         # рисуем все отметки на канве, как привязанные к ступени, так и нет.
#         # self.__createObjectsOnCanvas()
#         # рисуем изображение ступени на канве
#         # self.__stage = FirstStage2(self.__canvas, self.__stageScale, piningPoint, massCenterInCanvas)
#         pass
#
#     def __marksOnStageWindow(self, massCenterInCanvas: VectorComplex):
#         """
#             Создаём отметки в окне изображения ступени.
#         """
#         # тестовая точка на экране, показывающая ориентацию СКК. Монтажное положение ЦМ в СКК
#         # test = [Sizes.widthCenterBlock / 2 / self.__stageScale, Sizes.heightCenterBlock * 2 / 3 / self.__stageScale]
#         # self.__canvas.create_oval([test[0] - 5, test[1] - 5, test[0] + 5, test[1] + 5], fill="blue")
#         # self.__canvas.create_oval([massCenterInCanvas.x - 5, massCenterInCanvas.y - 5,
#         #                            massCenterInCanvas.x + 5, massCenterInCanvas.y + 5], fill="blue")
#
#         # стрелка ориентации, ставится в центре тяжести изображения ступени
#         self.__arrow = Arrow(self.__canvas, massCenterInCanvas,
#                              VectorComplex.getInstance(massCenterInCanvas.x,
#                                                        massCenterInCanvas.y + self.__orientation.y * 60.),
#                              5, "blue", massCenterInCanvas)
#         self.__stageLinkedMarks.append(self.__arrow)
#         # self.__testArrow = Arrow(self.__canvas, VectorComplex.getInstance(10, 10), VectorComplex.getInstance(10, 60), 5,
#         #                          "blue")
#
#         # отметка центра масс
#         self.__massCenterMark = CenterMassMark(self.__canvas, massCenterInCanvas, fill="blue")
#         self.__stageLinkedMarks.append(self.__massCenterMark)
#
#         # Текстовая информация
#         # # Метки
#         # self.__labelVhorizontal = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine, 50),
#         #                                "Vertical Velocity: ", NE, "green")
#         # self.__labelVvertical = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine, 70),
#         #                              "Horisontal Velocity: ", NE, "green")
#         # self.__labelPosition = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine, 100),
#         #                                "Position: ", NE, "green")
#         # self.__testArc = PsevdoArcArrow(self.__canvas, VectorComplex.getInstance(400, 300))
#         self.__arcAndTextTest = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(300, 300), "Header", 120., "Legend", "green")
#
#         self.__lineVelocityInfo = LineArrowAndText(self.__canvas, VectorComplex.getInstance(450, 200), "Velocity", 120., "{0:7.2f} m/s", "green")
#         self.__lineAxelerationInfo = LineArrowAndText(self.__canvas, VectorComplex.getInstance(550, 200), "Axeleration", 120., "{0:7.2f} m/s^2", "green")
#         self.__angleVelocity = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(450, 300), "Velocity", 120., "{0:7.2f} r/s", "green")
#         self.__angleAxeleration = ArcArrowAndText(self.__canvas, VectorComplex.getInstance(550, 300), "Axeleration", 120., "00,00 r/s^2", "green")
#         self.__stageDistance = LineArrowAndText(self.__canvas, VectorComplex.getInstance(450, 350), "Distance", 120., "{0:7.2f} m", "green")
#         self.__stageAltitude = LineArrowAndText(self.__canvas, VectorComplex.getInstance(550, 350), "Altitude", 120., "0000,00 m", "green")
#
#
#
#
#         # velocityPinPoint = VectorComplex.getInstance(self.__centerTextLine, 200)
#         # self.__velocityArrow = Arrow(self.__canvas,
#         #                              VectorComplex.getInstance(velocityPinPoint.x, velocityPinPoint.y + 20),
#         #                              VectorComplex.getInstance(velocityPinPoint.x, velocityPinPoint.y - 20),
#         #                              5, "green", velocityPinPoint)
#
#         self.__canvasLinkedMarks.extend([self.__arcAndTextTest,
#                                          self.__lineVelocityInfo, self.__lineAxelerationInfo,
#                                          self.__angleVelocity, self.__angleAxeleration,
#                                          self.__stageDistance, self.__stageAltitude])
#
#         # # Значения
#         # self.__valueVhorizontal = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine + 10, 50),
#         #                                "000,000 m/s", NW, "green")
#         # self.__valueVvertical = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine + 10, 70),
#         #                              "000,000 m/s", NW, "green")
#         # # self.__valuePosition = Text(self.__canvas, VectorComplex.getInstance(self.__centerTextLine + 10, 90),
#         # #                             "x = 000.000,\ny = 000.000", NW)
#         # self.__valuePosition = StageViewWindow.PositionLabelText(self.__canvas, VectorComplex.getInstance(
#         #     self.__centerTextLine + 10, 90),(0., 0.), NW)
#         # self.__canvasLinkedMarks.extend([self.__valueVhorizontal, self.__valueVvertical, self.__valuePosition])
#
#     def __createObjectsOnCanvas(self):
#         """
#         Отрисовываем на канве графические элементы
#         """
#         self.__stage.createOnCanvas()
#
#         for value in self.__stageLinkedMarks:
#             value.createOnCanvas()
#
#         for value in self.__canvasLinkedMarks:
#             value.createOnCanvas()
#
#         self.__lineVelocityInfo.direction = VectorComplex.getInstance(1., 0.)
#         # self.__arcAndTextTest.direction = PsevdoArcArrow.ZERO
#
#     def canvas(self):
#         return self.__canvas
#
#     def __draw(self):
#         """ метод для периодической перерисовки объектов на канве """
#
#         transform = None
#         # Длительность предыдущего состояния
#         previousStatusDuration = 0
#
#         # получение данных из внешних источников self.__anyQueue
#         if not self.__anyQueue.empty():
#             transform = self.__anyQueue.get()
#
#             previousStatusDuration = transform.timeStamp - self.__previousStatusTimeStamp
#             self.__previousStatusTimeStamp = transform.timeStamp
#
#         # отрисовка нового положения объектов на основании полученных данных из очереди
#         if transform is not None:
#             # изменить значение
#             # self.__valuePosition.text = (transform.position, transform.position.y)
#
#             # переводим свободный вектор расстояния в СКК
#             distanceVectorCCS = complexChangeSystemCoordinatesUniversal(transform.position,
#                                                                         VectorComplex.getInstance(0., 0.), 0., True)
#             self.__stageDistance.setInfo(abs(transform.position), distanceVectorCCS)
#             # переводим свободный вектор скорости в СКК
#             velocityVectorCCS = complexChangeSystemCoordinatesUniversal(transform.velocity,
#                                                                         VectorComplex.getInstance(0., 0.), 0., True)
#             self.__lineVelocityInfo.setInfo(abs(transform.velocity), velocityVectorCCS)
#             # переводим свободный вектор ускорения в СКК
#             axelerationVectorCCS = complexChangeSystemCoordinatesUniversal(transform.axeleration,
#                                                                            VectorComplex.getInstance(0., 0.), 0., True)
#             self.__lineAxelerationInfo.setInfo(abs(transform.axeleration), axelerationVectorCCS)
#
#             self.__angleVelocity.setInfo(transform.angularVelocity)
#
#             self.__angleAxeleration.setInfo(transform.angularAxeleration)
#
#             # На всякий случай вытаскиваем величину. Пока не понятно зачем она нам понадобится.
#             BigMap.stageViewOriginInPoligonCoordinates = transform.position
#             stageViewOrientation: VectorComplex
#
#             # Вектор ориентации это - свободный вектор. От нуля любой СК.
#             stageViewOrientation, _ = pointsListToNewCoordinateSystem(
#                 [transform.orientation, transform.orientation],
#                 VectorComplex.getInstance(0., 0.),
#                 0., True
#             )
#
#             # print("{0} Get. Orientation: {1}".format(transform.text, stageViewOrientation))
#
#             # value: Arrow
#             # вращать метки, привязанные к изображению ступени
#             for value in self.__stageLinkedMarks:
#                 value.rotate(stageViewOrientation, self.__orientation)
#             # текстовые метки не вращаем
#
#             # Вращаем стрелки индикаторов
#             # self.__velocityArrow.rotate(transform.stageStatus.velocity, self.__velocityArrow)
#
#             self.__orientation = stageViewOrientation
#
#         # запускаем отрисовку цикл
#         # self.__root.after(self.__frameRate, self.__draw)
#         # duration = CheckPeriod.to_Sec()
#         self.__root.after(CheckPeriod.to_mSec(previousStatusDuration), self.__draw)


# class FirstStage2():
#     """
#     Класс изображения первой ступени
#     """
#     #
#     # сначала необходимо отрисовать (создать) объект на канве:
#     # draw()
#     #
#     # в дальнейшем, движение и поворот объекта на канве реализуется последовательным применением этих двух методов
#     # move()
#     # rotate()
#     #
#     # метод draw() можно вызывать неоднократно, так как объект на канве создаётся только при ПЕРВОМ вызове метода.
#     # При последующих вызовах новые объекты не создаются, а методы move() и rotate() применяются к объекту,
#     # который был создан при ПЕРВОМ вызове метода draw()
#     #
#     # Ступень представляет из себя связанный набор стандартных примитивов (в основном многоугольники)
#     def __init__(self, canvas: Canvas, assemblingPoint: VectorComplex, massCenterInCanvas: VectorComplex, linkedMarks: list, scale: float):
#         """
#
#         :param canvas: канва
#         :param scale: масштаб изображения ступени на канве
#         """
#         self.__canvas = canvas
#         self.__scale = scale
#         # Алгоритм сборки.
#         # -----
#         # Во время графической сборки примитивов, все вектора отсчитываются (для простоты) от левого верхнего угла
#         # центрального блока. То есть, левый верхний угол центрального блока находится в начале координат канвы (1).
#         #
#         # После сборки, координаты ступени пересчитываются в точку координат её центра масс (2)
#         #
#         # Затем ступень переносится в своё начальное положение (3)
#         # -----
#         # Установка ракеты в позицию на холсте приозводится за счёт указания вектора центра масс ступени,
#         # привязанного к системе координат холста.
#         # В данном случае, установка произведена так, чтобы верхний левый угол центрального блока
#         # совпал с началом координат канвы
#         #
#         # центр масс (центр вращения) в системе координат канвы
#         # self.__massCenter \
#         #     = VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__scale, Sizes.heightCenterBlock * 2/3 / self.__scale)
#         self.__massCenter = massCenterInCanvas.lazyCopy()
#         #
#         # Так как при создании ступень стоит вертикально, данный вектор (вектор продольной оси) направлен по оси Y
#         # в системе отсчёта канвы
#         # self.__directionVector = Point(0., 1.)
#         # todo возможно (0, -1)?
#         self.__directionVector = VectorComplex.getInstance(0., -1.)
#
#         # Все примитивы изначально рисуются в привязке к началу координат канвы, с целью упрощения задания координат
#         # ключевых точек.
#         # В последствии, при не обходимости, примитивы перемещаются в нужное положение целиком.
#
#         # массив всех примитивов ступени
#         self.__allPrimitives = []
#
#         # # отметка центра масс
#         # self.__massCenterMark = CenterMassMark(self.__canvas, VectorComplex.getInstance(self.__massCenter.x - 2, self.__massCenter.y - 2),
#         #                                                   VectorComplex.getInstance(self.__massCenter.x + 2, self.__massCenter.y + 2),
#         #                                        self.__massCenter,
#         #                                                   fill="green")
#         # self.__allPrimitives.append(self.__massCenterMark)
#
#         # Корпус ступени.
#         # Верхний левый угол ступени находится в начале координат канвы. В этом положении ступень находится до конца
#         # сборки всех примитивов
#         self.__tank = PoligonRectangleA(self.__canvas).\
#             create2points(assemblingPoint + VectorComplex.getInstance(0., 0.),
#                           assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / self.__scale, Sizes.heightCenterBlock / self.__scale),
#                           self.__massCenter)
#         self.__allPrimitives.append(self.__tank)
#
#         # верхний левый маневровый двигатель
#         # создание в нулевой позиции
#         self.__topLeftJet = PoligonRectangleA(self.__canvas).\
#             create2points(assemblingPoint + VectorComplex.getInstance(0, 0),
#                           assemblingPoint + VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
#                           self.__massCenter)
#         # смещение примитива в монтажную позицию
#         self.__topLeftJet.preliminaryMove(assemblingPoint + VectorComplex.getInstance(- Sizes.widthJet / self.__scale, 0))
#         self.__allPrimitives.append(self.__topLeftJet)
#
#         # верхний правый маневровый двигатель
#         # создание в нулевой позиции
#         self.__topRightJet = PoligonRectangleA(self.__canvas).\
#             create2points(assemblingPoint + VectorComplex.getInstance(0, 0),
#                           assemblingPoint + VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
#                           self.__massCenter)
#         # смещение примитива в монтажную позицию
#         self.__topRightJet.preliminaryMove(assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / self.__scale, 0))
#         self.__allPrimitives.append(self.__topRightJet)
#
#         # нижний левый маневровый двигатель
#         # создание в нулевой позиции
#         self.__downLeftJet = PoligonRectangleA(self.__canvas).\
#             create2points(assemblingPoint + VectorComplex.getInstance(0, 0),
#                           assemblingPoint + VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
#                           self.__massCenter)
#         # смещение примитива в монтажную позицию
#         self.__downLeftJet.preliminaryMove(assemblingPoint + VectorComplex.getInstance(- Sizes.widthJet / self.__scale, (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))
#         self.__allPrimitives.append(self.__downLeftJet)
#
#         # нижний правый маневровый двигатель
#         # создание в нулевой позиции
#         self.__downRightJet = PoligonRectangleA(self.__canvas).\
#             create2points(assemblingPoint + VectorComplex.getInstance(0, 0),
#                           assemblingPoint + VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
#                           self.__massCenter)
#         # смещение примитива в монтажную позицию
#         self.__downRightJet.preliminaryMove(assemblingPoint + VectorComplex.getInstance(Sizes.widthCenterBlock / self.__scale, (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))
#         self.__allPrimitives.append(self.__downRightJet)
#
#         # маршевый двигатель
#         # создание в нулевой позиции
#         self.__mainJet = PoligonRectangleA(self.__canvas).\
#             create2points(assemblingPoint + VectorComplex.getInstance(0, 0),
#                           assemblingPoint + VectorComplex.getInstance(Sizes.widthMainJet / self.__scale, Sizes.heightMainJet / self.__scale),
#                           self.__massCenter)
#         # смещение примитива в монтажную позицию
#         self.__mainJet.preliminaryMove(assemblingPoint + VectorComplex.getInstance((Sizes.widthCenterBlock-Sizes.widthMainJet)/2 / self.__scale, Sizes.heightCenterBlock / self.__scale))
#         self.__allPrimitives.append(self.__mainJet)
#
#         # смещение собранного изображения ступени в нужную позицию на канве
#         prelimenaryMoveVector = VectorComplex.getInstance(50., 50.)
#         # создаём копию объекта "координаты центра масс"
#         massCenter = massCenterInCanvas.lazyCopy()
#         # смещаем центр масс
#         massCenter += prelimenaryMoveVector
#         for primitive in self.__allPrimitives:
#             primitive.preliminaryMove(prelimenaryMoveVector)
#             # все примитивы ступени привязываются к одному объекту "координаты центра масс", как к центру вращения
#             primitive.rotationCenter = massCenter
#
#         for mark in linkedMarks:
#             mark.preliminaryMove(prelimenaryMoveVector)
#             # все метки, связанные со ступенью, так же привязываются к одному и тому же объекту "координаты центра масс"
#             mark.rotationCenter = massCenter
#
#     def createOnCanvas(self):
#         """
#         Рисовать (создать) ступень на канве. Создаётся один единственный раз только при ПЕРВОМ вызове.
#         """
#         for primitive in self.__allPrimitives:
#             primitive.createOnCanvas()
#
#     def move(self, newMassCenter: VectorComplex):
#         """
#         Двигать ступень.
#
#         :param newMassCenter: новые координаты ЦМ в СКК
#         """
#         # смещение ЦМ в СКК
#         # moveVector = VectorComplex.sub(newMassCenter, self.__massCenter)
#         moveVector = newMassCenter - self.__massCenter
#
#         for primitive in self.__allPrimitives:
#             primitive.move(moveVector)
#
#         self.__massCenter = newMassCenter
#
#     def rotate(self, newVector: VectorComplex):
#         """
#         Вращать ступень.
#
#         :param newVector:
#         """
#         for primitive in self.__allPrimitives:
#             primitive.rotate(newVector, self.__directionVector)
#
#         # Обновляем значение
#         self.__directionVector = newVector


