""" Общие константы приложения. """
from torch import float32, dtype

class FinishAppException(Exception):
    pass

TestId = int

log_file_name: str = 'app.log'
logger_name: str = 'main_log'

# Время сна, сек.
SLEEP_TIME: float = 0.001

TENSOR_DTYPE: dtype = float32
