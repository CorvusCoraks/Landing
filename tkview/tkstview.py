""" Модуль визуализации состояния изделия в процесси испытания """
from tkview.primiteves import Arrow, ArcArrowAndText, LineArrowAndText, AbstractOnCanvasMark, CenterMassMark
from tkinter import Canvas, Toplevel, Tk
from point import VectorComplex
from typing import List, Dict, AnyStr, Union, Optional
from tkview.tkstmacr import FirstStage2
from stage import Sizes, BigMap
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import  CheckPeriod
from tkview.tkiface import WindowsMSInterface
from structures import RealWorldStageStatusN
from tools import MetaQueue

# OnCanvasStaticObjectDict = Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]

class StageViewWindow(WindowsMSInterface):
    """
    Класс окна вывода увеличенного изображения ступени и числовых характеристик
    """
    # def __init__(self, root: Tk, stage_size: float, stage_scale: float, frameRate: int, anyQueue: Queue, to_info_queue: Queue, info_block: Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]):
    def __init__(self, root: Tk, stage_size: float, stage_scale: float, queues: MetaQueue):
        """
        :param root: родительский оконный менеджер
        :param stage_size: максимальный характерный размер ступени, метров
        :param stage_scale: масштаб изображения ступени на канве
        :param queues: очередь для передачи данных одного фрейма движения ступени
        """
        self.__stage_size = stage_size
        self.__stage_scale = stage_scale
        self.__any_queue = queues
        # self.__to_info_queue = queues.get_queue("info")

        # ВременнАя точка предыдущего состояния изделия
        self.__previous_status_time_stamp = 0

        # Ширина в пикселях, зарезервированная для текстовых меток
        self.__for_text_labels = 200
        # 1.3 эмпирическая добавка, так как центр тяжести ступени смещён от центра симметрии
        self.__more_width = 1.3
        self.__window_width = self.__stage_size / self.__stage_scale * self.__more_width + self.__for_text_labels
        self.__window_height = self.__stage_size / self.__stage_scale * self.__more_width
        # Виртуальная вертикальная линия, проходящая по двоеточиям (по середине) текстовых меток
        # Необходима для компоновки текстовых меток
        self.__center_text_line = self.__stage_size / self.__stage_scale * self.__more_width + self.__for_text_labels / 2

        self.__root = Toplevel(root)
        self.__root.geometry("+{0:d}+{1:d}".format(600, 100))
        self.__root.title("Stage view")
        self.__canvas = Canvas(self.__root, width=self.__window_width, height=self.__window_height)
        self.__canvas.pack()

        # отметки привязанные к к канве
        self.__canvas_linked_marks: Optional[Dict[AnyStr, Union[LineArrowAndText, ArcArrowAndText]]] = None

        # отметки привязанные к изображению ступени
        self.__stage_linked_marks: List[AbstractOnCanvasMark] = []
        # Координаты точки предварительной сборки (левый верхний угол прямоугольника ступени) в СКК
        assembling_point = VectorComplex.get_instance(0., 0.)
        # Координаты центра масс в СКК
        self.__mass_center_on_canvas: VectorComplex = assembling_point + VectorComplex.get_instance(Sizes.widthCenterBlock / 2 / self.__stage_scale,
                                                                                                   Sizes.heightCenterBlock * 2 / 3 / self.__stage_scale)
        self.__orientation = VectorComplex.get_instance(0., -1.)

        self._preparation_static_marks()
        self._preparation_movable_marks()

        self.__stage = FirstStage2(self.__canvas, assembling_point, self.__mass_center_on_canvas, self.__stage_linked_marks, self.__stage_scale)

        self._create_objects_on_canvas()

        self.__root.after(0, self._draw)

    def _draw(self):
        """ метод для периодической перерисовки объектов на канве """

        transform: Optional[RealWorldStageStatusN] = None
        # Длительность предыдущего состояния
        previous_status_duration = 0

        # получение данных из внешних источников self.__any_queue
        if not self.__any_queue.empty('stage'):
            transform = self.__any_queue.get('stage')

            previous_status_duration = transform.time_stamp - self.__previous_status_time_stamp
            self.__previous_status_time_stamp = transform.time_stamp

            # self.__to_info_queue.put(transform.lazy_copy)

        # отрисовка нового положения объектов на основании полученных данных из очереди
        if transform is not None:
            self.__change_static_marks(transform)
            if self.__canvas_linked_marks is not None: self.__change_movable_marks(transform)

        # запускаем отрисовку цикл
        self.__root.after(CheckPeriod.to_mu_sec(previous_status_duration), self._draw)
        # self.__root.after(500, self._draw)


    def __change_static_marks(self, transform: RealWorldStageStatusN):
        """ Обновление неподвижных отметок в соответствии с актуальной информацией """
        # переводим свободный вектор расстояния в СКК
        distance_vector_ccs = complexChangeSystemCoordinatesUniversal(transform.position,
                                                                    VectorComplex.get_instance(0., 0.), 0., True)
        self.__canvas_linked_marks["distance"].setInfo(abs(transform.position), distance_vector_ccs)
        # переводим свободный вектор скорости в СКК
        velocity_vector_ccs = complexChangeSystemCoordinatesUniversal(transform.velocity,
                                                                    VectorComplex.get_instance(0., 0.), 0., True)
        # self.__lineVelocityInfo.setInfo(abs(transform.velocity), velocity_vector_ccs)
        self.__canvas_linked_marks["line_velocity"].setInfo(abs(transform.velocity), velocity_vector_ccs)
        # переводим свободный вектор ускорения в СКК
        axeleration_vector_ccs = complexChangeSystemCoordinatesUniversal(transform.acceleration,
                                                                       VectorComplex.get_instance(0., 0.), 0., True)
        # self.__lineAxelerationInfo.setInfo(abs(transform.acceleration), axeleration_vector_ccs)
        self.__canvas_linked_marks["line_accel"].setInfo(abs(transform.acceleration), axeleration_vector_ccs)

        # self.__angleVelocity.setInfo(transform.angular_velocity)
        self.__canvas_linked_marks["angle_velocity"].setInfo(transform.angular_velocity)

        # self.__angleAxeleration.setInfo(transform.angular_acceleration)
        self.__canvas_linked_marks["angle_accel"].setInfo(transform.angular_acceleration)

    def __change_movable_marks(self, transform: RealWorldStageStatusN):
        """ Обновление подвижных отметок в соответствии с актуальной информацией. """
        # На всякий случай вытаскиваем величину. Пока не понятно зачем она нам понадобится.
        BigMap.stageViewOriginInPoligonCoordinates = transform.position
        stage_view_orientation: VectorComplex

        # Вектор ориентации это - свободный вектор. От нуля любой СК.
        stage_view_orientation, _ = pointsListToNewCoordinateSystem(
            [transform.orientation, transform.orientation],
            VectorComplex.get_instance(0., 0.),
            0., True
        )

        # вращать метки, привязанные к изображению ступени
        for value in self.__stage_linked_marks:
            value.rotate(stage_view_orientation, self.__orientation)
        # текстовые метки не вращаем

        # Вращаем стрелки индикаторов
        # self.__velocityArrow.rotate(transform.stage_status.velocity, self.__velocityArrow)

        self.__orientation = stage_view_orientation

    def _preparation_static_marks(self):
        pass

    def _preparation_movable_marks(self):
        # стрелка ориентации, ставится в центре тяжести изображения ступени
        self.__arrow = Arrow(self.__canvas, self.__mass_center_on_canvas,
                             VectorComplex.get_instance(self.__mass_center_on_canvas.x,
                                                        self.__mass_center_on_canvas.y + self.__orientation.y * 60.),
                             5, "blue", self.__mass_center_on_canvas)
        self.__stage_linked_marks.append(self.__arrow)
        # self.__testArrow = Arrow(self.__canvas, VectorComplex.get_instance(10, 10), VectorComplex.get_instance(10, 60), 5,
        #                          "blue")

        # отметка центра масс
        self.__mass_center_mark = CenterMassMark(self.__canvas, self.__mass_center_on_canvas, fill="blue")
        # del self.__mass_center_on_canvas
        self.__stage_linked_marks.append(self.__mass_center_mark)

    def _create_objects_on_canvas(self):
        """
        Отрисовываем на канве графические элементы (кроме информационного блока)
        """
        self.__stage.create_on_canvas()

        for value in self.__stage_linked_marks:
            value.create_on_canvas()
        pass

    @property
    def root(self):
        return self.__root

    @property
    def canvas(self):
        return self.__canvas

    def create_info_block_on_canvas(self, block: Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]):
        """ Создать блок информации о процессе на канве """
        self.__canvas_linked_marks = block

        for value in self.__canvas_linked_marks.values():
            value.createOnCanvas()

        self.__canvas_linked_marks["line_velocity"].direction = VectorComplex.get_instance(1., 0.)

class InfoView():
    """ Блок информации о процессе. """
    def __init__(self):
        pass

    @classmethod
    def get_info_block(cls, canvas: Canvas) -> Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]:
        """ Получить блок информации о процессе """
        arc_and_text_test = ArcArrowAndText(canvas, VectorComplex.get_instance(300, 300), "Header", 120.,
                                                "Legend", "green")

        line_velocity_info = LineArrowAndText(canvas, VectorComplex.get_instance(450, 200), "Velocity", 120.,
                                                   "{0:7.2f} m/s", "green")
        line_axeleration_info = LineArrowAndText(canvas, VectorComplex.get_instance(550, 200), "Axeleration",
                                               120., "{0:7.2f} m/s^2", "green")
        angle_velocity = ArcArrowAndText(canvas, VectorComplex.get_instance(450, 300), "Velocity", 120.,
                                               "{0:7.2f} r/s", "green")
        angle_axeleration = ArcArrowAndText(canvas, VectorComplex.get_instance(550, 300), "Axeleration",
                                           120., "00,00 r/s^2", "green")
        stage_distance = LineArrowAndText(canvas, VectorComplex.get_instance(450, 350), "Distance", 120.,
                                                "{0:7.2f} m", "green")
        stage_altitude = LineArrowAndText(canvas, VectorComplex.get_instance(550, 350), "Altitude", 120.,
                                                "0000,00 m", "green")

        return {"test": arc_and_text_test, "line_velocity": line_velocity_info, "line_accel": line_axeleration_info, "angle_velocity": angle_velocity,
               "angle_accel": angle_axeleration, "distance": stage_distance, "altitude": stage_altitude}

