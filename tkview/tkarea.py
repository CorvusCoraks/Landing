""" Модуль визуализации происходящего с испытуемым объектом. """
from tkinter import Tk, Canvas
from typing import Optional
from stage import BigMap
from kill_flags import KillCommandsContainerN
from physics import CheckPeriod
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from tkview.primiteves import StageMark
from tkview.tkiface import WindowsMSInterface
from structures import RealWorldStageStatusN, StageState
from tools import MetaQueue
from time import sleep
from point import VectorComplex
from carousel.metaque import MetaQueueN
from carousel.atrolley import TestId
from carousel.metaque import MetaQueue2


class PoligonWindow(WindowsMSInterface):
    """
    Окно испытательного полигона, на котором рисуется траектория. Главное окно.

    """
    # Окно с увеличенным изображением ступени рисутется как "дочернее" окно полигона.
    # При закрытии окна полигона, закрывается и окно ступени.

    def __init__(self, queues: MetaQueue2, poligon_width: float,
                 poligon_heigt: float, poligon_scale: float,
                 kill: KillCommandsContainerN):
        """

        :param _frameRate: частота кадров (и поступления данных в очередь). Устарело.
        :param queues: контейнер очередей
        :param poligon_width: ширина испытательного полигона (точка посадки находится посередине)
        :param poligon_heigt: высота испытательного полигона (от уровня грунта)
        :param poligon_scale: масштаб отображения полигона. Количество метров на одну точку.
        :param kill: контейнер флагов отключения нитей
        """
        self.__poligon_width = poligon_width
        self.__poligon_heigt = poligon_heigt
        # масштаб изображения полигона пикселей на метр
        self.__poligon_scale = poligon_scale


        # self.__queue = queues.get("area")
        self.__queues = queues
        # Очередь для передачи данных в дочернее окно
        # self.__subQueue = queues.get_queue("stage")

        # self.__killNeuroNetFlag = killNeuronetFlag
        # self.__killRealityFlag = killRealityFlag
        self.__kill = kill

        # Время сна в ожидании данных в очереди
        self.__time_sleep: float = 0.001
        # Состояние изделия для отображения
        self.__any_state: RealWorldStageStatusN = RealWorldStageStatusN()
        # Состояние изделия не нужное для отображение, лишнее. Для сброса лишних состояний из очереди.
        self.__trash_state: RealWorldStageStatusN = RealWorldStageStatusN()
        # Идентификатор испытания предназначенного для отображения.
        self.__test_id_for_view: TestId = 0
        # Стартовая точка отображаемого испытания.
        self.__start_point: VectorComplex = VectorComplex.get_instance()

        # # Получение начального положения изделия в СКИП (первое сообщение в очереди им и является)
        # # todo устанавливать отметку старта именно по этим данным
        # while self.__queues.empty('area'):
        #     sleep(self.__time_sleep)
        # else:
        #     self.__start_point: VectorComplex = complexChangeSystemCoordinatesUniversal(
        #         self.__queues.get('area').position, BigMap.canvasOriginInPoligonCoordinates, 0., True) / self.__poligon_scale

        # Получение начального положения изделия
        # Ждём блок данных из очереди
        self.__queues.state_to_view.parsel_waiting(None)
        if issubclass(self.__queues.state_to_view.parsel_type, StageState):
            # Если тип контейнера совпадает с типом ожидаемого груза
            test_id, _ = self.__queues.state_to_view.receive_parsel(self.__trash_state)

            if test_id == self.__test_id_for_view:
                # Если тест, который закреплён для отображения - сохраняем его.
                self.__trash_state.data_copy(self.__any_state)
        else:
            raise TypeError('Data block type {0} from queue and target object {1} type mismatch.'
                            .format(self.__queues.state_to_view.parsel_type, StageState))

        # # Получение начального положения изделия
        # while not self.__queues.state_to_view.has_new_cargo():
        #     # Пока нет вагонеток с начальными состояниями - засыпаем
        #     sleep(self.__time_sleep)
        # else:
        #     # Есть вагонетка
        #     test_id, init_flag = self.__queues.state_to_view.unload(self.__trash_state)
        #     if test_id == self.__test_id_for_view:
        #         # Если тест, который закреплён для отображения - сохраняем его.
        #         self.__trash_state.data_copy(self.__any_state)

        # Стартовая точка в СКК
        self.__start_point: VectorComplex = complexChangeSystemCoordinatesUniversal(
            self.__any_state.position, BigMap.canvasOriginInPoligonCoordinates, 0., True) / self.__poligon_scale

        # точка посадки в СКК
        self.__end_point = complexChangeSystemCoordinatesUniversal(BigMap.landingPointInPoligonCoordinates,
                                                                   BigMap.canvasOriginInPoligonCoordinates,
                                                                   0., True) / self.__poligon_scale
        # текущая координата ЦМ ступени в СКК
        self.__current_point = self.__start_point

        # ВременнАя точка предыдущего состояния изделия
        self.__previous_status_time_stamp = 0

        self.__root = Tk()
        self.__root.geometry("+300+100")
        self.__root.title("Trajectory")
        self.__canvas = Canvas(self.__root, width=self.__poligon_width / self.__poligon_scale, height=self.__poligon_heigt / self.__poligon_scale)
        self.__canvas.pack()

        self._preparation_static_marks()
        self._preparation_movable_marks()
        # Отметка на экране ЦМ ступени в СКК
        self.__stage_mark: StageMark
        self._create_objects_on_canvas()
        # Устаналвиваем обработчик закрытия главного окна
        self.__root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__root.after(0, self._draw)

        # Окно увеличенного изображения ступени в процессе посадки
        # self.__stageWindow = StageViewWindow(self.__root, stage_size, stage_scale, -1, self.__subQueue, Queue())

    def _draw(self):
        # метод для периодического вызова и отрисовки на канве (точка траектории, данные по высоте, тангажу, крену и пр)
        transform: Optional[RealWorldStageStatusN] = None
        # длительность предыдущего статуса изделия
        previous_status_duration = 0

        # получение данных из внешних источников
        parsel_was_received = self.__queues.state_to_view.parsel_waiting()
        if not issubclass(self.__queues.state_to_view.parsel_type, StageState):
            raise TypeError('Data block type {0} from queue and target object {1} type mismatch.'
                            .format(self.__queues.state_to_view.parsel_type, StageState))
        else:
            test_id, _ = self.__queues.state_to_view.receive_parsel(self.__trash_state)
            if test_id == self.__test_id_for_view:
                self.__trash_state.data_copy(self.__any_state)

        # # получение данных из внешних источников self.__any_queue
        # while not self.__queues.state_to_view.has_new_cargo():
        #     sleep(self.__time_sleep)
        # else:
        #     test_id, _ = self.__queues.state_to_view.unload(self.__trash_state)
        #     if test_id == self.__test_id_for_view:
        #         self.__trash_state.data_copy(self.__any_state)

        # if self.__queues.state_to_view.has_new_cargo():
        # if not self.__queues.empty('area'):
            # print(self.__any_queue.get())
            transform = self.__any_state

            previous_status_duration = transform.time_stamp - self.__previous_status_time_stamp
            self.__previous_status_time_stamp = transform.time_stamp

            # преобразование из СКИП в СКК
            (stage_canvas_orientation, stage_canvas_position) = pointsListToNewCoordinateSystem(
                [transform.orientation, transform.position],
                BigMap.canvasOriginInPoligonCoordinates,
                0., True
            )

            # отрисовка нового положения объектов на основании полученных данных из self.__any_queue
            # if transform is not None:
            # сдвинуть отметку ЦМ ступени
            if self.__stage_mark.moveMark(self.__current_point, stage_canvas_position / self.__poligon_scale):
                # значение обновляем только тогда, если производился сдвиг отметки по канве
                # в противном случае, прошедшее значение смещения попало в трэшхолд и не является значимым
                self.__current_point = stage_canvas_position / self.__poligon_scale
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
        self.__root.after(CheckPeriod.to_mu_sec(previous_status_duration), self._draw)

    def _preparation_static_marks(self):
        pass

    def _preparation_movable_marks(self):
        self.__stage_mark = StageMark(self.__current_point, self.__canvas)

    def _create_objects_on_canvas(self):
        """ метод расставляет необходимые отметки по полигону (точка сброса ступени, точка посадки ступени и пр.) """
        # отметка точки посадки в виде треугольника
        self.__canvas.create_polygon([self.__end_point.x - 10, self.__end_point.y,
                                      self.__end_point.x, self.__end_point.y - 10,
                                      self.__end_point.x + 10, self.__end_point.y], fill="#1f1")
        # Отметка точки начала спуска ступени
        self.__canvas.create_oval([self.__start_point.x - 5, self.__start_point.y - 5,
                                   self.__start_point.x + 5, self.__start_point.y + 5], fill="green")

    def __on_closing(self):
        """ Обработчик закрытия главного окна. """
        # убиваем дополнительные нити
        self.__kill.neuro.kill = True
        self.__kill.reality.kill = True
        # закрываем главное окно
        self.__root.destroy()

    @property
    def root(self) -> Tk:
        return self.__root

    @property
    def canvas(self) -> Canvas:
        return self.__canvas



