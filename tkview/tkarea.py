""" Модуль визуализации происходящего с испытуемым объектом. """
from logging import getLogger
from basics import logger_name, TestId, FinishAppException
from tkinter import Tk, Canvas
from typing import Optional, Dict, Tuple
from stage import BigMap
from physics import CheckPeriod
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from tkview.primiteves import StageMark
from tkview.tkiface import WindowsMSInterface
from structures import RealWorldStageStatusN
from time import sleep
from point import VectorComplex
from con_intr.ifaces import ISocket, IReceiver, ISender, AppModulesEnum, DataTypeEnum, BioEnum
from con_simp.contain import Container, BioContainer
from tkview.view_chn import ViewParts, ViewData, ViewDataSwitcher
from copy import deepcopy

logger = getLogger(logger_name+'.view')

Inbound = Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]]
Outbound = Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]]

ViewInbound = Dict[ViewParts, Dict[ViewData, IReceiver]]
ViewOutbound = Dict[ViewParts, Dict[ViewData, ISender]]

class PoligonWindow(WindowsMSInterface):
    """
    Окно испытательного полигона, на котором рисуется траектория. Главное окно.

    """
    # Окно с увеличенным изображением ступени рисутется как "дочернее" окно полигона.
    # При закрытии окна полигона, закрывается и окно ступени.

    def __init__(self, socket: ISocket, view_dispatcher: ISocket, fin_com: ISocket, area_data: ISocket, poligon_width: float,
                 poligon_heigt: float, poligon_scale: float):
        """

        :param socket: Интерфейс подключения модуля визуализации к системе обмена сообщений.
        :param view_dispatcher: Набор коммуникационных линий для получения/отправки данных в рамках приложения.
        :param fin_com: Канал для отправки команды на завершение приложения.
        :param area_data: Набор коммуникационных линий для получения данных в рамках блока визуализации.
        :param poligon_width: ширина испытательного полигона (точка посадки находится посередине)
        :param poligon_heigt: высота испытательного полигона (от уровня грунта)
        :param poligon_scale: масштаб отображения полигона. Количество метров на одну точку.
        """
        self.__poligon_width = poligon_width
        self.__poligon_heigt = poligon_heigt
        # масштаб изображения полигона пикселей на метр
        self.__poligon_scale = poligon_scale

        # Канал локального обмена данными между диспетчером и остальными частями модуля визуализации.
        self.__dispatcher_out: ViewOutbound = view_dispatcher.get_out_dict()
        self.__dispatcher_in: ViewInbound = view_dispatcher.get_in_dict()

        # Канал локальной передачи команды на завершение приложения.
        self.__fin_outbound: ViewOutbound = fin_com.get_out_dict()

        # Канал локальной связи, как канал приёма отфильтрованных состояний для отображения в окне исп. полигона.
        self.__area_inbound: ViewInbound = area_data.get_in_dict()

        # Каналы связи масштаба приложения.
        self.__data_socket = socket
        self.__inbound: Inbound = self.__data_socket.get_in_dict()
        self.__outbound: Outbound = self.__data_socket.get_out_dict()

        # todo передать из вышестоящего модуля
        # Время сна в ожидании данных в очереди
        self.__time_sleep: float = 0.001
        # todo проверить использование и удалить
        # Состояние изделия для отображения
        self.__any_state: RealWorldStageStatusN = RealWorldStageStatusN()
        # Состояние изделия не нужное для отображение, лишнее. Для сброса лишних состояний из очереди.
        self.__trash_state: RealWorldStageStatusN = RealWorldStageStatusN()
        # Идентификатор испытания предназначенного для отображения.
        self.__test_id_for_view: TestId = 0
        self.__bio: BioEnum = BioEnum.FIN
        # todo получать в draw()
        # Стартовая точка отображаемого испытания в СКК. Значение по умолчанию.
        self.__start_point: VectorComplex = VectorComplex.get_instance()

        # точка посадки в СКК
        self.__end_point = complexChangeSystemCoordinatesUniversal(BigMap.landingPointInPoligonCoordinates,
                                                                   BigMap.canvasOriginInPoligonCoordinates,
                                                                   0., True) / self.__poligon_scale
        # todo присваивать в draw()
        # текущая координата ЦМ ступени в СКК
        self.__current_point: VectorComplex = VectorComplex.get_instance()

        # ВременнАя точка предыдущего состояния изделия
        self.__previous_status_time_stamp = 0

        self.__root = Tk()
        self.__root.geometry("+300+100")
        self.__root.title("Trajectory")
        self.__canvas = Canvas(self.__root, width=self.__poligon_width / self.__poligon_scale, height=self.__poligon_heigt / self.__poligon_scale)
        self.__canvas.pack()

        self._preparation_static_marks()
        # Отметка на экране ЦМ ступени в СКК
        self.__stage_mark: StageMark
        # Устаналвиваем обработчик закрытия главного окна
        self.__root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__root.after(0, self._draw)

    def __state_dispatcher(self):
        """ Метод отбирает из потока входящих состояний (из физ. модуля) только те, которые буду визуализироваться. """
        try:

            view_state: Optional[RealWorldStageStatusN] = None
            test_id: TestId = -1
            while view_state is None:
                # пока не дошли до визуализируемого испытания
                while not self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.STAGE_STATUS].has_incoming():
                    # ожидаем данные из канала связи
                    sleep(self.__time_sleep)
                    # Проверка на завершение приложения.
                    if self.__dispatcher_in[ViewParts.AREA_WINDOW][ViewData.APP_FINISH].has_incoming():
                        self.__dispatcher_in[ViewParts.AREA_WINDOW][ViewData.APP_FINISH].receive()
                        raise FinishAppException

                container = self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.STAGE_STATUS].receive()
                assert isinstance(container, BioContainer), "Container class should be a BioContainer. " \
                                                            "Now: {}".format(container.__class__)
                test_id, bio = container.get()
                state = container.unpack()

                if self.__bio == BioEnum.FIN:
                    if bio == BioEnum.INIT:
                        # Если по контролируемому испытанию стоит метка - завершено.
                        # И у выпавшего из канала испытания стоит статус - инициализировано,
                        # то переходим на отслеживание этого инициализированного испытания.
                        self.__test_id_for_view = test_id
                        self.__bio = bio
                        view_state = state
                        # Переводим в координаты канвы.
                        self.__start_point = complexChangeSystemCoordinatesUniversal(view_state.position,
                                                                                     BigMap.canvasOriginInPoligonCoordinates,
                                                                                     0., True) / self.__poligon_scale
                        self.__current_point = self.__start_point
                        logger.debug('Начало визуализации нового испытания: id = {}, bio = {}, time stamp = {}'.format(test_id, bio, state.time_stamp))

                        # todo Метод будет создавать новые объекты раз за разом в том же месте! Неправильно!
                        self._create_objects_on_canvas()
                        # todo Метод будет создавать новые объекты раз за разом в том же месте! Неправильно!
                        self._preparation_movable_marks()

                        # Выход из цикла.
                        continue

                    if test_id == self.__test_id_for_view:
                        # Если по контролируемому испытанию стоит метка - завершено.
                        # и если из канала выпало именно контролируемое испытание,
                        # то отлавливаем следующее состояние из канала (Переходим к следующей итерации цикла.)
                        continue

                if test_id == self.__test_id_for_view:
                    # И если его идентификатор совпадает с идентификатором контролируемого испытания.
                    self.__bio = bio
                    view_state = state
                    logger.debug('Продолжение визуализации испытания: id = {}, bio = {}, time stamp = {}'.format(test_id, bio, state.time_stamp))

            # Отсылаем состояние ступени другим визуализаторам этого испытания.
            container = Container(test_id, view_state)
            self.__dispatcher_out[ViewParts.AREA][ViewData.STAGE_STATUS].send(deepcopy(container))
            self.__dispatcher_out[ViewParts.STAGE][ViewData.STAGE_STATUS].send(deepcopy(container))
            self.__dispatcher_out[ViewParts.INFO][ViewData.STAGE_STATUS].send(deepcopy(container))
            # self.__data_queues.get_wire(ViewParts.DISPATCHER, ViewParts.INFO, ViewData.STAGE_STATUS).send(deepcopy(container))

        except FinishAppException:
            logger.info('Поступила команда на завершение приложения. Завершаем работу диспетчера состояний.')

    def _draw(self):
        # метод для периодического вызова и отрисовки на канве (точка траектории, данные по высоте, тангажу, крену и пр)
        previous_status_duration: int = 0

        try:
            # Запуск диспетчера состояний.
            self.__state_dispatcher()

            while not self.__area_inbound[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].has_incoming():
                sleep(self.__time_sleep)
                if self.__area_inbound[ViewParts.AREA_WINDOW][ViewData.APP_FINISH].has_incoming():
                    self.__area_inbound[ViewParts.AREA_WINDOW][ViewData.APP_FINISH].receive()
                    raise FinishAppException
            else:
                container = self.__area_inbound[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].receive()
                assert isinstance(container, Container), "Container class should be a Container. " \
                                                            "Now: {}".format(container.__class__)
                test_id, view_state = container.get(), container.unpack()

            logger.debug('Положение изделия в СКИП. x: {}, y: {}'.format(view_state.position.x, view_state.position.y))
            # длительность предыдущего статуса изделия
            previous_status_duration = view_state.time_stamp - self.__previous_status_time_stamp
            self.__previous_status_time_stamp = view_state.time_stamp

            # преобразование из СКИП в СКК
            (stage_canvas_orientation, stage_canvas_position) = pointsListToNewCoordinateSystem(
                [view_state.orientation, view_state.position],
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

        except FinishAppException:
            logger.info('Поступила команда на завершение приложения. Завершаем работу метода отрисовки исп. полигона.')

        # запускаем отрисовку в цикл
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
        self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.APP_FINISH].send(Container())
        self.__outbound[AppModulesEnum.NEURO][DataTypeEnum.APP_FINISH].send(Container())
        # Отправка команды на завершения приложения в подразделы визуализации направлена не для закрытия окон
        # (с этим справится и сам tkinter), а на ускоренное завершение/прерывание циклов и снов.
        self.__fin_outbound[ViewParts.AREA][ViewData.APP_FINISH].send(Container())
        self.__fin_outbound[ViewParts.STAGE][ViewData.APP_FINISH].send(Container())
        self.__fin_outbound[ViewParts.INFO][ViewData.APP_FINISH].send(Container())
        self.__fin_outbound[ViewParts.DISPATCHER][ViewData.APP_FINISH].send(Container())
        # закрываем главное окно
        self.__root.destroy()

    @property
    def root(self) -> Tk:
        return self.__root

    @property
    def canvas(self) -> Canvas:
        return self.__canvas



