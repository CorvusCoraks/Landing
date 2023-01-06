""" Общие константы приложения. """

class FinishAppException(Exception):
    pass

TestId = int

log_file_name = 'app.log'
logger_name = 'main_log'

# Время сна, сек.
SLEEP_TIME = 0.001
