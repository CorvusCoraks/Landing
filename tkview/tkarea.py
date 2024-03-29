""" Модуль визуализации происходящего с испытуемым объектом. """
from logging import getLogger
from app_cons import logger_name, SLEEP_TIME, START_TESTID_FOR_VIEW
from app_type import TestId
from tkinter import Tk, Canvas
from typing import Optional, Dict
from stage import BigMap
from physics import CheckPeriod
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from tkview.primiteves import StageMark
from tkview.tkiface import WindowsMSInterface
from structures import RealWorldStageStatusN
from time import sleep
from point import VectorComplex
from con_intr.ifaces import ISocket, IReceiver, ISender, \
    AppModulesEnum, DataTypeEnum, BioEnum, Inbound, Outbound
from con_simp.contain import Container, BioContainer
from tkview.view_chn import ViewParts, ViewData
from copy import deepcopy
from tools import FinishAppBoolWrapper


logger = getLogger(logger_name+'.view')


ViewInbound = Dict[ViewParts, Dict[ViewData, IReceiver]]
ViewOutbound = Dict[ViewParts, Dict[ViewData, ISender]]


class PoligonWindow(WindowsMSInterface):
    """
    Окно испытательного полигона, на котором рисуется траектория. Главное окно.

    """
    # Окно с увеличенным изображением ступени рисутется как "дочернее" окно полигона.
    # При закрытии окна полигона, закрывается и окно ступени.

    def __init__(self, socket: ISocket, view_dispatcher: ISocket, fin_com: ISocket, area_data: ISocket,
                 poligon_width: float, poligon_heigt: float, poligon_scale: float):
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
        self.__inbound: Inbound = socket.get_in_dict()
        self.__outbound: Outbound = socket.get_out_dict()

        # Никто не может приказать блоку визуализации.
        # Но, на всякий случай, оставляем. Возможно в будущем будет разумно создать надстройку, управляющую
        # завершением ВСЕХ блоков приложения, в том числе и завершением Блока Визуализации.
        is_app_fin: FinishAppBoolWrapper = FinishAppBoolWrapper()
        is_fin_request: FinishAppBoolWrapper = FinishAppBoolWrapper()

        # Количество периодов ожидания данных. Поспал-Проснулся - 1 период.
        DATA_WAITING_MAX: int = 10

        # Идентификатор испытания предназначенного для отображения.
        # После показа испытания START_TESTID_FOR_VIEW начинается показ очередного нового.
        self.__test_id_for_view: TestId = START_TESTID_FOR_VIEW
        # Состояние (биография) демонстрируемого испытания.
        self.__bio: BioEnum = BioEnum.FIN

        # Стартовая точка отображаемого испытания в СКК. Значение по умолчанию.
        self.__start_point: VectorComplex = VectorComplex.get_instance()
        # Идентификатор стартовой точки на канве.
        self.__sp_mark: int = -1

        # точка посадки в СКК
        self.__end_point = complexChangeSystemCoordinatesUniversal(BigMap.landingPointInPoligonCoordinates,
                                                                   BigMap.canvasOriginInPoligonCoordinates,
                                                                   0., True) / self.__poligon_scale
        # Идентификатор точки финиша на канве.
        self.__ep_mark: int = -1

        # текущая координата ЦМ ступени в СКК
        self.__current_point: VectorComplex = VectorComplex.get_instance()

        # ВременнАя точка предыдущего состояния изделия
        self.__previous_status_time_stamp = 0

        self.__root = Tk()
        self.__root.geometry("+300+100")
        self.__root.title("Trajectory")
        self.__canvas = Canvas(self.__root,
                               width=self.__poligon_width / self.__poligon_scale,
                               height=self.__poligon_heigt / self.__poligon_scale)
        self._create_objects_on_canvas()
        self._preparation_movable_marks()
        self.__canvas.pack()

        self._preparation_static_marks()
        # Отметка на экране ЦМ ступени в СКК
        self.__stage_mark: StageMark
        # Устаналвиваем обработчик закрытия главного окна
        self.__root.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.__root.after(0, self._draw, (is_app_fin, is_fin_request, DATA_WAITING_MAX))

    def __state_dispatcher(self, is_fin_app: FinishAppBoolWrapper, is_fin_request: FinishAppBoolWrapper,
                           data_waiting_max: int) -> None:
        """ Метод отбирает из потока входящих состояний (из физ. модуля) только те, которые буду визуализироваться.
        """
        dw: int = data_waiting_max

        view_state: Optional[RealWorldStageStatusN] = None
        test_id: TestId = -1
        bio: BioEnum = BioEnum.INIT
        while view_state is None:
            # пока не дошли до визуализируемого испытания
            while not self.__inbound[AppModulesEnum.PHYSICS][DataTypeEnum.STAGE_STATUS].has_incoming():
                # ожидаем данные из канала связи
                sleep(SLEEP_TIME)
                self.__fintest(self.__dispatcher_in, self.__inbound, is_fin_app, is_fin_request)
                if is_fin_request():
                    # Если есть запрос на окончание приложения.
                    # Уменьшаем счётчик ожидания данных из очереди.
                    dw -= 1
                    if dw == 0:
                        # Если счётчик обнулился, прерываем ожидание и завершаем функцию.
                        # Иными словами, ожидание данных из очереди происходит в течение нескольких периодов сна.
                        return

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

                    logger.debug('Начало визуализации нового испытания: id = {}, bio = {}, time stamp = {}'.
                                 format(test_id, bio, state.time_stamp))

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
                logger.debug('Продолжение визуализации испытания: id = {}, bio = {}, time stamp = {}'.
                             format(test_id, bio, state.time_stamp))

        # Отсылаем состояние ступени другим визуализаторам этого испытания.
        container = BioContainer(test_id, bio, view_state)
        self.__dispatcher_out[ViewParts.AREA][ViewData.STAGE_STATUS].send(deepcopy(container))
        self.__dispatcher_out[ViewParts.STAGE][ViewData.STAGE_STATUS].send(deepcopy(container))
        self.__dispatcher_out[ViewParts.INFO][ViewData.STAGE_STATUS].send(deepcopy(container))

    def _draw(self, args):
        # метод для периодического вызова и отрисовки на канве (точка траектории, данные по высоте, тангажу, крену и пр)
        previous_status_duration: int = 0

        # is_app_fin: FinishAppBoolWrapper = FinishAppBoolWrapper()
        # fin_request: FinishAppBoolWrapper = FinishAppBoolWrapper()
        is_app_fin: FinishAppBoolWrapper = args[0]
        fin_request: FinishAppBoolWrapper = args[1]
        data_waiting_max: int = args[2]

        # Запуск диспетчера состояний.
        self.__state_dispatcher(is_app_fin, fin_request, data_waiting_max)

        # счётчик ожидания данных
        dw: int = data_waiting_max
        while not self.__area_inbound[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].has_incoming():
            # Ожидание очередного состояния.
            sleep(SLEEP_TIME)

            self.__fintest(self.__area_inbound, self.__inbound, is_app_fin, fin_request)
            if fin_request():
                # Если есть запрос на завершение приложения
                # Уменьшить счётчик ожидания данных из очереди.
                dw -= 1
                if dw == 0:
                    # Если счётчик обнулился (то есть, данных из очереди не дождались)
                    # Отправляем приказ на завершение в другие блоки приложения
                    self.__send_fin_command()
                    # Завершаем блок визуализации.
                    self.__finish_view()
                    # Выходим из функции отрисовки.
                    return
        else:
            # todo обработать вариант, когда данные в очереди есть, но и запрос на завершение приложения тоже есть.

            container = self.__area_inbound[ViewParts.DISPATCHER][ViewData.STAGE_STATUS].receive()
            assert isinstance(container, BioContainer), "Container class should be a BioContainer. " \
                                                        "Now: {}".format(container.__class__)
            test_id, bio = container.get()
            view_state = container.unpack()

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

        # Между испытаниями маркер точки старта и маркер ЦМ изделия находятся в точке (0, 0) канвы.

        if bio == BioEnum.INIT:
            # Стартовая точка = первая точка в данном испытании.
            self.__start_point.decart = stage_canvas_position.decart
            # Перемещаем маркер стартовой позиции из точки (0; 0) в истинную точку старта
            self.__canvas.move(self.__sp_mark, self.__start_point.x, self.__start_point.y)
            # Перемещаем маркер ЦМ изделия из точки (0, 0) в точку старта.
            self.__stage_mark.moveMark(self.__current_point, self.__start_point)
            # Сохраняем точку старта как текущее положение ЦМ изделия.
            self.__current_point = self.__start_point
        elif bio == BioEnum.FIN:
            # Испытание завершено, возвращаем маркер стартовой позиции в точку (0; 0)
            self.__canvas.move(self.__sp_mark, -self.__start_point.x, -self.__start_point.y)
            # Возвращаем маркер ЦМ изделия в точку (0, 0)
            self.__stage_mark.moveMark(self.__current_point, VectorComplex.get_instance())
            # Сохраняем точку положения маркера ЦМ как текущую точку.
            self.__current_point = VectorComplex.get_instance()
        else:
            # отрисовка нового положения объектов на основании полученных данных из self.__any_queue
            # сдвинуть отметку ЦМ ступени
            if self.__stage_mark.moveMark(self.__current_point, stage_canvas_position / self.__poligon_scale):
                # значение обновляем только тогда, если производился сдвиг отметки по канве
                # в противном случае, прошедшее значение смещения попало в трэшхолд и не является значимым
                self.__current_point = stage_canvas_position / self.__poligon_scale

        if fin_request():
            # Обрабатываем запрос на завершение приложения.
            self.__send_fin_command()
            self.__finish_view()
            return

        # запускаем отрисовку в цикл
        self.__root.after(CheckPeriod.to_mu_sec(previous_status_duration), self._draw,
                          (is_app_fin, fin_request, data_waiting_max))

    def _preparation_static_marks(self):
        pass

    def _preparation_movable_marks(self):
        self.__stage_mark = StageMark(self.__current_point, self.__canvas)

    def _create_objects_on_canvas(self):
        """ метод расставляет необходимые отметки по полигону (точка сброса ступени, точка посадки ступени и пр.) """

        # отметка точки посадки в виде треугольника
        start: VectorComplex = VectorComplex.get_instance(0, 0)
        finish: VectorComplex = VectorComplex.get_instance(0, 0)
        self.__ep_mark = self.__canvas.create_polygon([finish.x - 10, finish.y,
                                      finish.x, finish.y - 10,
                                      finish.x + 10, finish.y], fill="#1f1")
        self.__canvas.move(self.__ep_mark, self.__end_point.x, self.__end_point.y)

        # Отметка точки начала спуска ступени
        self.__sp_mark = self.__canvas.create_oval([start.x - 5, start.y - 5,
                                   start.x + 5, start.y + 5], fill="green")

    def __finish_view(self):
        """ Закрытие окон визуализации. """
        # Отправка команды на завершения приложения в подразделы визуализации. Направлена не для закрытия окон
        # (с этим справится и сам tkinter), а на ускоренное завершение/прерывание циклов и снов.
        self.__fin_outbound[ViewParts.AREA][ViewData.APP_FINISH].send(Container())
        self.__fin_outbound[ViewParts.STAGE][ViewData.APP_FINISH].send(Container())
        self.__fin_outbound[ViewParts.INFO][ViewData.APP_FINISH].send(Container())
        self.__fin_outbound[ViewParts.DISPATCHER][ViewData.APP_FINISH].send(Container())
        # закрываем главное окно
        self.__root.destroy()

    def __on_closing(self):
        """ Обработчик закрытия главного окна. """
        self.__send_fin_command()
        self.__finish_view()

    def __send_fin_command(self):
        """ Отправка приказов на завершение блоков приложения. """
        self.__outbound[AppModulesEnum.PHYSICS][DataTypeEnum.APP_FINISH].send(Container())
        self.__outbound[AppModulesEnum.NEURO][DataTypeEnum.APP_FINISH].send(Container())

    def __fintest(self, view_inbound: ViewInbound, inbound: Inbound,
                is_fin_app: FinishAppBoolWrapper, is_fin_request: FinishAppBoolWrapper) -> None:
        """ Проверка на наличие в системе запросов или команд на завершение приложения. """

        # Проверка запроса от блока нейросети на закрытие приложения.
        if inbound[AppModulesEnum.NEURO][DataTypeEnum.APP_FINISH_REQUEST].has_incoming():
            inbound[AppModulesEnum.NEURO][DataTypeEnum.APP_FINISH_REQUEST].receive()
            is_fin_request(True)
            logger.info("Получен запрос от БНС на завершение приложения.")

    @property
    def root(self) -> Tk:
        return self.__root

    @property
    def canvas(self) -> Canvas:
        return self.__canvas
