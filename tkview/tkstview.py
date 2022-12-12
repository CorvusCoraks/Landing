""" Модуль визуализации состояния изделия в процесси испытания """
from tkview.primiteves import Arrow, ArcArrowAndText, LineArrowAndText, AbstractOnCanvasMark, CenterMassMark
from tkinter import Canvas, Toplevel, Tk
from point import VectorComplex
from typing import List, Dict, AnyStr, Union, Optional, Tuple
from tkview.tkstmacr import FirstStage2
from stage import Sizes, BigMap
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import  CheckPeriod
from tkview.tkiface import WindowsMSInterface
from structures import RealWorldStageStatusN
from con_intr.ifaces import ISocket, IReceiver, ISender, BioEnum
from tkview.view_chn import ViewParts, ViewData
from time import sleep
from basics import FinishAppException, TestId
from con_simp.contain import BioContainer

ViewInbound = Dict[ViewParts, Dict[ViewData, IReceiver]]
ViewOutbound = Dict[ViewParts, Dict[ViewData, ISender]]

class StageViewWindow(WindowsMSInterface):
    """
    Класс окна вывода увеличенного изображения ступени и числовых характеристик
    """
    def __init__(self, root: Tk, data_queue: ISocket, stage_size: float, stage_scale: float):
        """
        :param root: родительский оконный менеджер
        :param data_queue: Интерфейс для получения данных в рамках блока визуализации
        :param stage_size: максимальный характерный размер ступени, метров
        :param stage_scale: масштаб изображения ступени на канве
        """
        # todo время сна перенести в вышестоящий вызов
        self.__sleep_time = 0.001
        self.__stage_size = stage_size
        self.__stage_scale = stage_scale

        self.__states_in: ViewInbound = data_queue.get_in_dict()

        self.__any_state: RealWorldStageStatusN = RealWorldStageStatusN()

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

        # Визуализатор информации.
        self.__info_view: Optional[InfoView] = None
        # Если == True, значит визуализатор информации уже присутствует на канве.
        # Если == False, значит визуализатора на канве ещё нет.
        self.__info_view_ready: bool = False

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
        try:
            # Получение данных для отображения изделия.
            while not self.__states_in[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].has_incoming():
                sleep(self.__sleep_time)
                if self.__states_in[ViewParts.AREA_WINDOW][ViewData.APP_FINISH].has_incoming():
                    raise FinishAppException
            else:
                container = self.__states_in[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].receive()
                assert isinstance(container, BioContainer), "Container class should be a BioContainer. " \
                                                         "Now: {}".format(container.__class__)
                test_id, bio = container.get()
                self.__any_state = container.unpack()

                transform = self.__any_state
                previous_status_duration = transform.time_stamp - self.__previous_status_time_stamp
                self.__previous_status_time_stamp = transform.time_stamp

            # Визуализация информации
            while self.__info_view is None:
                # Если визуализатор ещё не создан
                sleep(self.__sleep_time)
                if self.__states_in[ViewParts.STAGE][ViewData.APP_FINISH].has_incoming():
                    raise FinishAppException
            else:
                # Визуализатор информации есть.
                if not self.__info_view_ready:
                    # Если визуализатор информации ещё не насторен
                    # Получаем блок визуальных элементов визуализации информации.
                    info_block: Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]] = self.__info_view.get_info_block(self.__canvas)
                    # Создаём блок визуальных элементов на канве.
                    self.create_info_block_on_canvas(info_block)
                    # Фиксируем создание блока визуализации информации.
                    self.__info_view_ready = True

                # Получить данных из канала связи, поставляющего данные в блок визуализации информации.
                # На данном этапе проектирования приложения, этот канал поступления данных не используется.
                test_id, bio, state = self.__info_view.info_block_data(self.__info_view.data_inbound, self.__sleep_time)

            # отрисовка нового положения объектов на основании полученных данных из очереди
            if transform is not None:
                self.__change_static_marks(transform)
                if self.__canvas_linked_marks is not None: self.__change_movable_marks(transform)

        except FinishAppException:
            pass

        # запускаем отрисовку цикл
        self.__root.after(CheckPeriod.to_mu_sec(previous_status_duration), self._draw)


    def __change_static_marks(self, transform: RealWorldStageStatusN):
        """ Обновление неподвижных отметок в соответствии с актуальной информацией """
        # переводим свободный вектор расстояния в СКК
        distance_vector_ccs = complexChangeSystemCoordinatesUniversal(transform.position,
                                                                    VectorComplex.get_instance(0., 0.), 0., True)
        self.__canvas_linked_marks["distance"].setInfo(abs(transform.position), distance_vector_ccs)
        # переводим свободный вектор скорости в СКК
        velocity_vector_ccs = complexChangeSystemCoordinatesUniversal(transform.velocity,
                                                                    VectorComplex.get_instance(0., 0.), 0., True)

        self.__canvas_linked_marks["line_velocity"].setInfo(abs(transform.velocity), velocity_vector_ccs)
        # переводим свободный вектор ускорения в СКК
        axeleration_vector_ccs = complexChangeSystemCoordinatesUniversal(transform.acceleration,
                                                                       VectorComplex.get_instance(0., 0.), 0., True)

        self.__canvas_linked_marks["line_accel"].setInfo(abs(transform.acceleration), axeleration_vector_ccs)

        self.__canvas_linked_marks["angle_velocity"].setInfo(transform.angular_velocity)

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

    def set_info_block(self, info: 'InfoView'):
        self.__info_view = info


class InfoView():
    """ Блок информации о процессе. """
    def __init__(self, socket: ISocket):
        """

        :param socket: Поток данных для отображения.
        """
        self.__data_inbound: ViewInbound = socket.get_in_dict()

    def info_block_data(self, info_in: ViewInbound, sleep_time: float) -> Tuple[TestId, BioEnum, RealWorldStageStatusN]:
        """ Извлечение из канала данных для информационного блока. (Пока данные отсюда не используются)

        :param info_in: входные каналы информации
        :param sleep_time: время сна в ожидании появления даанных
        :return: Данные для отображения по текущему испытанию.
        """
        # Ждём установления фактического, реального значения атрибута.
        while len(info_in) == 0:
            sleep(sleep_time)
            if info_in[ViewParts.AREA_WINDOW][ViewData.APP_FINISH].has_incoming():
                raise FinishAppException

        # Извлекаем из канала значения данных для информационного блока.
        # В данный момент эти значения не используются, в работу берутся значения из канала данных для
        # визуализации изделия.
        while not info_in[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].has_incoming():
            sleep(sleep_time)
            if info_in[ViewParts.DISPATCHER][ViewData.APP_FINISH].has_incoming():
                raise FinishAppException
        else:
            container = info_in[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].receive()
            test_id, bio = container.get()
            state = container.unpack()

        return test_id, bio, state

    @property
    def data_inbound(self) -> ViewInbound:
        return self.__data_inbound

    def get_info_block(self, canvas: Canvas) -> Dict[AnyStr, Union[ArcArrowAndText, LineArrowAndText]]:
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

