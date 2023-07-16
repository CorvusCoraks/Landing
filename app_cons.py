""" Общие константы уровня приложения. """

from app_type import TestId

log_file_name: str = 'app.log'
logger_name: str = 'main_log'

# Идентификатор первого теста предназначенного для отображения.
START_TESTID_FOR_VIEW: TestId = 0
# Когда этот тест завершится, право отображения передаётся следующему ближайшему тесту, предназначенному для испытаний.

# Время сна, сек.
SLEEP_TIME: float = 0.001
COROUTINE_SLEEP_TIME: float = 0.001

GRAVITY_ACCELERATION_ABS = 9.8067

# Масштаб временной отметки
# 10 - 0.1 сек.
# 100 - 0,01 сек.
# Т. е., чтобы получить время в секундах, умножаем временную отметку на этот масштаб.
TIME_STAMP_SCALE = 10

# Имя раздела (в хранилище) содержащее нейросеть актора
ACTOR_CHAPTER = 'actor'
# Имя раздела (в хранилище) содержащее нейросеть критика
CRITIC_CHAPTER = 'critic'

CUDA0 = 'cuda:0'
CPU = 'cpu'

QUEUE_OBJECT_TYPE_ERROR = "From queue object class ({}) doesn't match expected class {}."

# Сообщение по умолчанию при штатном завершении работы приложения.
DEFAULT_REPORT = "{}\nDefault report: traning finished.\n{}".format('-'*10,'-'*10)

# Константы хранилища состояний окружающей среды
STATES_IN_WORK: str = 'states_in_work'
INITIAL_STATES: str = 'initial_states'
TESTS_LEFT: str = 'tests_left'