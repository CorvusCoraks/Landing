""" Общие константы приложения. """

from torch import float32, uint8, dtype, int64


class FinishAppException(Exception):
    pass


TestId = int

# 0..1
ZeroOne = float
# Тип имеющий только два значения: 0 или 1. Потомок int
Bit = int

log_file_name: str = 'app.log'
logger_name: str = 'main_log'

# Маркер вычисляемой строки в файле настроек проекта.
# todo удалить после удаления текстовых файлов настроек
EVAL = 'eval:'

# Время сна, сек.
SLEEP_TIME: float = 0.001
COROUTINE_SLEEP_TIME: float = 0.001

TENSOR_DTYPE: dtype = float32
TENSOR_INDEX_DTYPE: dtype = int64

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

QUEUE_OBJECT_TYPE_ERROR = "From queue object class ({}) doesn't match expected class {}."

# todo удалить
Q_EST_NEXT = 'q_est_next'
# todo удалить
INDEX_IN_TEST = 'index'
# Possible two values see above.
# todo удалить
Dict_key = str

# Types for typing hints
# Оценка функции ценности
Q_est_value = ZeroOne
# Индекс максимальной оценки функции ценности в списке ВСЕХ оценок для данного испытания.
# todo удалить
Index_value = int


