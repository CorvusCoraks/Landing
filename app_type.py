""" Классы и типы уровня приложения. """
from typing import Dict, Optional, Any
from torch import dtype, float32, int64

# Тип словаря хранилища состояния окружающей среды
EnvDictType = Dict[str, Optional[Any]]

# Идентификатор теста (испытания)
TestId = int

# Число с плавающей точкой от 0 (включительно) до 1 (включительно)
ZeroOne = float

# Число: либо 0, либо 1
Bit = int

TENSOR_DTYPE: dtype = float32
TENSOR_INDEX_DTYPE: dtype = int64

# Оценка функции ценности
Q_est_value = ZeroOne
