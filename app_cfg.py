""" Файл настроек приложения. """

# Файлы рабочего проекта
PROJECT_DIRECTORY_PATH = './DevTmpPr'
PROJECT_DIRECTORY_NAME = PROJECT_DIRECTORY_PATH[2:]
PROJECT_PY_FILE = '/project.py'
# PROJECT_PY_NAME = PROJECT_PY_FILE[1:8]
# PROJECT_CONFIG_FILE = '/project.toml'
PROJECT_MAIN_CLASS = 'ProjectMainClass'
PROJECT_CONFIG_FILE = '/cfg.py'
PROJECT_CONFIG_NAME = PROJECT_CONFIG_FILE[1:-3]

# Промежуточное сохранения состояний каждые ... батчей
BATCH_PER_SAVING: int = 1
# Промежуточное сохранение состояний каждые ... эпох
EPOCH_PER_SAVING: int = 1