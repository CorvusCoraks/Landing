""" Главный файл. Диспетчер. Здесь создаются нити для параллельного исполнения """
import basics
import sys

from basics import log_file_name, logger_name
from logging import getLogger, FileHandler, StreamHandler, Formatter, DEBUG
from stage import Sizes, BigMap
from tkview.tkview import TkinterView
from view import ViewInterface
from con_simp.switcher import Switchboard, Socket
from con_simp.wire import Wire, ReportWire
from con_intr.ifaces import AppModulesEnum, DataTypeEnum, RoadEnum
from thrds_tk.neuronet import NeuronetThread
from thrds_tk.physics import PhysicsThread
import importlib
from app_cfg import PROJECT_DIRECTORY_NAME, PROJECT_CONFIG_NAME
from tools import KeyPressCheck

def get_log_handler(out: str):
    if out == "file":
        return FileHandler(log_file_name, mode='w', encoding='UTF-8')
    if out == "stdout":
        return StreamHandler(stream=sys.stdout)


def log_init(output: str) -> None:
    """ Инициализация логирования.

    :param output: 'file' or 'stdout'
    """
    logger = getLogger(logger_name)
    logger.setLevel(DEBUG)

    logger = getLogger(logger_name + '.view')
    formatter = Formatter('Визуализация. - %(message)s')
    handler = get_log_handler(output)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger = getLogger(logger_name + '.physics')
    formatter = Formatter('БФМ. - %(message)s')
    handler = get_log_handler(output)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger = getLogger(logger_name + '.main')
    formatter = Formatter('%(name)s - %(levelname)s - %(message)s')
    handler = get_log_handler(output)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger = getLogger(logger_name + '.neuronet')
    formatter = Formatter('НН - %(message)s')
    handler = get_log_handler(output)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def wires() -> Switchboard:
    """ Реализация сообщений через распределительный щит. """

    switchboard = Switchboard()
    switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.NEURO, DataTypeEnum.STAGE_STATUS))
    switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.VIEW, DataTypeEnum.STAGE_STATUS))
    switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.NEURO, DataTypeEnum.REINFORCEMENT))
    switchboard.add_wire(ReportWire(AppModulesEnum.PHYSICS, AppModulesEnum.NEURO,
                                    DataTypeEnum.REMANING_TESTS, DataTypeEnum.REQUESTED_TESTS))
    switchboard.add_wire(Wire(AppModulesEnum.NEURO, AppModulesEnum.PHYSICS, DataTypeEnum.JETS_COMMAND))

    # Команды на завершение вычислительных блоков приложения (по закрытия главного окна, например)н
    # из блока визуализации во все остальные блоки приложения.
    switchboard.add_wire(Wire(AppModulesEnum.VIEW, AppModulesEnum.PHYSICS, DataTypeEnum.APP_FINISH))
    switchboard.add_wire(Wire(AppModulesEnum.VIEW, AppModulesEnum.NEURO, DataTypeEnum.APP_FINISH))

    # Если какой-либо блок приложение желает закрыть приложение,
    # то он должен отправить запрос на это в блок визуализации.
    # В свою очередь, блок визуализации отправит команду на завершение приложения
    # во ВСЕ блоки приложения (включая и тот, который отправлял запрос.) для завершения их работы.
    # Каналы для запросов закрытия приложения (получатель - модуль визуализации)
    switchboard.add_wire(Wire(AppModulesEnum.NEURO, AppModulesEnum.VIEW, DataTypeEnum.APP_FINISH_REQUEST))

    # Сигнальная линия для передачи команд-семафоров из БНС в БФМ.
    switchboard.add_wire(Wire(AppModulesEnum.NEURO, AppModulesEnum.PHYSICS, DataTypeEnum.ENV_ROAD))

    return switchboard

if __name__ == "__main__":
    log_init("stdout")

    logger = getLogger(logger_name + '.main')

    logger.info("Input in {0} module\n".format(__name__))

    # RunTime импортирование файла конфигурации проекта.
    project_cfg = importlib.import_module('{}.{}'.format(PROJECT_DIRECTORY_NAME, PROJECT_CONFIG_NAME))

    # keypress: KeyPressCheck = KeyPressCheck("Продолжить обучение? [y] Или начать с нуля?", 'y', ['n'])
    # if keypress.input() == 'y':
    #     birth = True
    # else:
    #     birth = False

    birth = True

    switchboard = wires()

    # Нить модели реального мира
    # todo Абстрагировать тип нити, ибо структура вычислительных модулей может быть и не нитевой.
    realWorldThread: PhysicsThread = PhysicsThread('realWorldThread',
                                                   Socket(AppModulesEnum.PHYSICS, switchboard), project_cfg, birth)
    realWorldThread.start()

    # Для нейросети надо создать отдельную нить,
    # так как tkinter может работать исключительно в главном потоке.previous_status
    # Т. е. отображение хода обучения идёт через tkinter в главной нити,
    # расчёт нейросети и физическое моделирование в отдельной нити

    neuroNetThread: NeuronetThread = NeuronetThread('Neuron Net Thread',
                                                    Socket(AppModulesEnum.NEURO, switchboard), project_cfg, birth)

    neuroNetThread.start()

    # Создание окна (визуально показывает ситуацию) испытательного полигона. Главная, текущая нить.
    view: ViewInterface = TkinterView(Socket(AppModulesEnum.VIEW, switchboard))
    view.set_poligon_state(BigMap.width, BigMap.height)
    # todo удалить метод за ненадобностью
    view.set_kill_threads()
    view.set_stage_parameters(Sizes.topMassDistance,
                              Sizes.downMassDistance,
                              Sizes.downMassDistance,
                              Sizes.widthCenterBlock, Sizes.heightCenterBlock, Sizes.massCenterFromLandingPlaneDistance)

    view.create_poligon_view()
    view.create_stage_view()
    view.create_info_view()

    realWorldThread.join()
    neuroNetThread.join()

    # Вывод результирующего сообщения по завершению приложения.
    if hasattr(project_cfg, 'project_report'):
        # Если сообщение определено в файле настроек проекта.
        print(project_cfg.project_report)
    else:
        # Или сообщение по умолчанию.
        print(basics.DEFAULT_REPORT)
