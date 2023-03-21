""" Общие константы приложения. """

from torch import float32, dtype


class FinishAppException(Exception):
    pass


TestId = int

# 0..1
ZeroOne = float

log_file_name: str = 'app.log'
logger_name: str = 'main_log'

# Маркер вычисляемой строки в файле настроек проекта.
# todo удалить после удаления текстовых файлов настроек
EVAL = 'eval:'

# Время сна, сек.
SLEEP_TIME: float = 0.001
COROUTINE_SLEEP_TIME: float = 0.001

TENSOR_DTYPE: dtype = float32

GRAVITY_ACCELERATION_ABS = 9.8067

# Масштаб временной отметки
# 10 - 0.1 сек.
# 100 - 0,01 сек.
# Т. е., чтобы получить время в секундах, умножаем временную отметку на этот масштаб.
TIME_STAMP_SCALE = 10

# PROJECT_TOML_FILENAME = "\project.toml"

# Имя раздела (в хранилище) содержащее нейросеть актора
ACTOR_CHAPTER = 'actor'
# Имя раздела (в хранилище) содержащее нейросеть критика
CRITIC_CHAPTER = 'critic'

CUDA0 = 'cuda:0'
CPU = 'cpu'
