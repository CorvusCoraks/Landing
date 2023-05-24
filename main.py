""" Главный файл. Диспетчер. Здесь создаются нити для параллельного исполнения """
import basics
import sys

from basics import log_file_name, logger_name
from logging import getLogger, FileHandler, StreamHandler, Formatter, INFO, DEBUG, Logger
from stage import Sizes, BigMap
from tkview.tkview import TkinterView
from view import ViewInterface
from con_simp.switcher import Switchboard, Socket
from con_simp.wire import Wire, ReportWire
from con_intr.ifaces import AppModulesEnum, DataTypeEnum, TransferredData, ISocket
from thrds_tk.neuronet import NeuronetThread
from thrds_tk.physics import PhysicsThread
from states.s_states import InitGenerator
import importlib
from app_cfg import PROJECT_DIRECTORY_NAME, PROJECT_CONFIG_FILE


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
    formatter = Formatter('Физическая модель. - %(message)s')
    handler = get_log_handler(output)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger = getLogger(logger_name + '.main')
    formatter = Formatter('%(name)s - %(levelname)s - %(message)s')
    handler = get_log_handler(output)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if __name__ == "__main__":
    log_init("stdout")

    logger = getLogger(logger_name + '.main')

    logger.info("Input in {0} module\n".format(__name__))

    # RunTime импортирование файла конфигурации проекта.
    project_cfg = importlib.import_module('{}.{}'.format(PROJECT_DIRECTORY_NAME, PROJECT_CONFIG_FILE[1:-3]))

    # Реализация сообщений через распределительный щит
    switchboard = Switchboard()
    switchboard.add_wire(Wire(AppModulesEnum.PHYSICS,AppModulesEnum.NEURO, DataTypeEnum.STAGE_STATUS))
    switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.VIEW, DataTypeEnum.STAGE_STATUS))
    switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.NEURO, DataTypeEnum.REINFORCEMENT))
    switchboard.add_wire(ReportWire(AppModulesEnum.PHYSICS, AppModulesEnum.NEURO, DataTypeEnum.REMANING_TESTS, DataTypeEnum.REQUESTED_TESTS))
    switchboard.add_wire(Wire(AppModulesEnum.NEURO, AppModulesEnum.PHYSICS, DataTypeEnum.JETS_COMMAND))
    # Команды на завершение вычислительных блоков приложения (по закрытия главного окна, например)
    switchboard.add_wire(Wire(AppModulesEnum.VIEW, AppModulesEnum.PHYSICS, DataTypeEnum.APP_FINISH))
    switchboard.add_wire(Wire(AppModulesEnum.VIEW, AppModulesEnum.NEURO, DataTypeEnum.APP_FINISH))

    # Дополнительные каналы для завершения приложения в случае ошибки в каком-либо модуле
    # todo реализовать передачу этих каналов в блоки приложения.
    # switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.NEURO, DataTypeEnum.APP_FINISH))
    # switchboard.add_wire(Wire(AppModulesEnum.PHYSICS, AppModulesEnum.VIEW, DataTypeEnum.APP_FINISH))
    # switchboard.add_wire(Wire(AppModulesEnum.NEURO, AppModulesEnum.PHYSICS, DataTypeEnum.APP_FINISH))

    # Блок нейросети отправит запрос на завершение приложения (например, когда закончатся все запланированные эпохи)
    switchboard.add_wire(Wire(AppModulesEnum.NEURO, AppModulesEnum.VIEW, DataTypeEnum.APP_FINISH))


    # Очередь данных в вид испытательного полигона (из нити реальности)
    # Очередь данных в вид изделия (из нити реальности)
    # Очередь данных в вид информации о процессе (из нити реальности)
    # Очерердь данных в нейросеть (из нити реальности)
    # Очередь данных с подкреплениями (из нити реальности)
    # Очередь данных с управляющими командами (из нейросети)

    # Нить модели реального мира
    # todo Абстрагировать тип нити, ибо структура вычислительных модулей может быть и не нитевой.
    # realWorldThread: PhysicsThread = PhysicsThread('realWorldThread', Socket(AppModulesEnum.PHYSICS, switchboard), InitGenerator(max_tests))
    realWorldThread: PhysicsThread = PhysicsThread('realWorldThread', Socket(AppModulesEnum.PHYSICS, switchboard), project_cfg)
    realWorldThread.start()

    # Для нейросети надо создать отдельную нить, так как tkinter может работать исключительно в главном потоке.previous_status
    # Т. е. отображение хода обучения идёт через tkinter в главной нити,
    # расчёт нейросети и физическое моделирование в отдельной нити

    # neuroNetThread: NeuronetThread = NeuronetThread('Neuron Net Thread', Socket(AppModulesEnum.NEURO,switchboard), max_tests, batch_size)
    neuroNetThread: NeuronetThread = NeuronetThread('Neuron Net Thread', Socket(AppModulesEnum.NEURO,switchboard), project_cfg)

    neuroNetThread.start()

    # Размер полигона в метрах!
    # Мостшаб изображения
    # poligon_scale = 4 / 1000  # при ширине полигона 300000 м., ширина окна - 1200 точек
    # количество метров на одну точку
    # poligonScale = 1
    # stageScale = 0.1

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
