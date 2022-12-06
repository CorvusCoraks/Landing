""" Модуль классов диспетчера передачи состояний в блоке визуализации. """
from con_simp.switcher import Switchboard, Socket
from con_simp.wire import Wire, ReportWire
from enum import Enum

class ViewParts(Enum):
    """ Части блока визуализации приложения. """
    DISPATCHER = 0  # Диспетчер, фильтрующий входящий в модуль визуализации поток состояний.
    AREA = 1        # Окно визуализации испытательного полигона
    STAGE = 2       # Окно визуализации увеличенного изображения изделия.
    INFO = 3        # Окно визуализации цифровой и векторной информации.
    AREA_WINDOW = 4 # Окно, закрытие которого подаёт команду на завершение приложения.


class ViewData(Enum):
    """ Данные, передаваемые внутри блока визуализации. """
    STAGE_STATUS = 0
    APP_FINISH = 1


class ViewDataSwitcher(Switchboard):
    """ 'Распределительный щиток', объединяющий каналы связи блока визуализации. """
    def __init__(self):
        super().__init__()
        self.add_wire(Wire(ViewParts.DISPATCHER, ViewParts.AREA, ViewData.STAGE_STATUS))
        self.add_wire(Wire(ViewParts.DISPATCHER, ViewParts.STAGE, ViewData.STAGE_STATUS))
        self.add_wire(Wire(ViewParts.DISPATCHER, ViewParts.INFO, ViewData.STAGE_STATUS))
        self.add_wire(Wire(ViewParts.AREA_WINDOW, ViewParts.AREA, ViewData.APP_FINISH))
        self.add_wire(Wire(ViewParts.AREA_WINDOW, ViewParts.STAGE, ViewData.APP_FINISH))
        self.add_wire(Wire(ViewParts.AREA_WINDOW, ViewParts.INFO, ViewData.APP_FINISH))
        self.add_wire(Wire(ViewParts.AREA_WINDOW, ViewParts.DISPATCHER, ViewData.APP_FINISH))

