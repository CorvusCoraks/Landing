""" Модуль реализации абстрактной фабрики визуального представления в Tkinter. """
from view import ViewInterface
from tkview.tkarea import PoligonWindow
from tkview.tkstview import StageViewWindow, InfoView
from stage import Sizes
from con_intr.ifaces import ISocket
from tkview.view_chn import ViewParts, ViewDataSwitcher
from con_simp.switcher import Switchboard, Socket

# Техническое описание обработки очереди сообщений.
#
#  Объект визуализации имеет отдельный обработчик сообщений, фунционирующий в отдельной нити.
#  Этот обработчик занят одним: фильтрует очередь состояний от ненужных и закончившихся испытаний.
# Этот обработчик передаёт очищенную информацию об отслеживаемом испытании в блок окончательной очистки,
# где удаляются состояния попатающие в трэшхолд.
# Очищенный поток состояний, дробится на три части (три очереди) и раздаётся в модуль визуализации полигона,
# в модуль визуализации ступени и в модуль числовой информации.
# Объект с этими тремя очередями того же типа, что и основаной информационный диспетчер приложения.
#
# Исходя из выше изложенной концепции.
#
# - Конструктор TkinterView получает ссылку ISocket VIEW (из физ. модели.) получателя-визуализатора.
# - Создаёт объект локальной передачи данных (для передачи ISender на очиститель)
# - Тот же конструктор создаёт объект отдельной нити для очистителя данных
#
# Входные данные очистителя.
# - индентификатор первого визуализируемого испытания (по умолчанию - 0)
# - Интерфейс IReceiver VIEW объекта передачи состояний из физ. модели.
# - Интерфейс ISender локального объекта передачи данных (на полигон, ступень и мод. информации)
# - Параметры для отправления близких состояний в трэшхолд.
#
# Локальный класс передачи данных.
# - Он имеет свой набор Enum-ов, кодирующих тип передаваемых данных и отправителей/получателей.
# - Если мы хотим наследовать от класса главного Диспетчера, то в его интерфейсе-предке надо использовать не специали-
# зированных потомков Enum, а дженерик вида:
# A = TypeVar('A', bound=Enum)
# Т. о. и интерфейс-предок Диспетчера, и сам Диспетчер будут знать, что работают не с каким-то там любым Enum,
# а Enum, определённом в реализации данного интерфейса-предка.
#
# Каналы передачи данных очистителя:
# - ВСЕ состояния из физ. модели в очиститель.
# - Поток состояний ТОЛЬКО визуализируемого испытания в модуль полигона
# - Поток состояний ТОЛЬКО визуализируемого испытания в модуль ступени
# - Поток состояний ТОЛЬКО визуализируемого испытания в модуль информации.
#
# - Нить очистителя данных запускается после вызова mainloop() - НЕЛЬЗЯ!

class TkinterView(ViewInterface):
    """ ConcreteFactory """

    def __init__(self, socket: ISocket):
        """

        :param socket: Интерфейс получения/передачи данных уровня приложения.
        """
        self.__socket: ISocket = socket
        # Локальные очереди для передачи состояния в окно визуализации крупного вида ступени и данных.
        self.__data_queues: Switchboard = ViewDataSwitcher()

    def set_poligon_state(self, poligon_width: float, poligon_height: float):
        self.__poligon_width = poligon_width
        self.__poligon_height = poligon_height

    def set_kill_threads(self):
        pass

    def set_stage_parameters(self, top_mass_from_mc: float, down_mass_from_mc: float,
                             mc_from_bottom: float, stage_width: float, stage_height: float,
                             leg_plane_from_mc: float):

        self.__top_mass_from_mc = top_mass_from_mc
        self.__down_mass_from_mc = down_mass_from_mc
        self.__mc_from_bottom = mc_from_bottom
        self.__stage_width = stage_width
        self.__stage_height = stage_height
        self.__leg_plane_from_mc = leg_plane_from_mc

    def create_poligon_view(self):

        self.__poligon_scale = 1.
        # stage_view_scale = 0.1
        self.__poligon_window = PoligonWindow(self.__socket,
                                              Socket(ViewParts.DISPATCHER, self.__data_queues),
                                              Socket(ViewParts.AREA_WINDOW, self.__data_queues),
                                              Socket(ViewParts.AREA, self.__data_queues),
                                              self.__poligon_width, self.__poligon_height,
                                              self.__poligon_scale)

    def create_stage_view(self):
        stage_view_scale = 0.1

        self.__stage_window = StageViewWindow(self.__poligon_window.root, Socket(ViewParts.STAGE, self.__data_queues), Sizes.overallDimension, stage_view_scale)

    def create_info_view(self):
        info_view = InfoView(Socket(ViewParts.INFO, self.__data_queues))
        self.__stage_window.set_info_block(info_view)
        # Запустить главный цикл событий tkinter, так как в main.py этот метод вызывается последним.
        # Запущен mainloop() от окна ступени, так как информация тоже находится в этом окне.
        # Т. е. main_loop() вызывается на последнем инициализированном окне?
        self.__stage_window.root.mainloop()
        # после вызова mainloop() никакие инструкции не выполняются