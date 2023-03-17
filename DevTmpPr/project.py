""" Модуль конкретного проекта. """
from torch import Tensor, cuda, tensor
from torch.nn import Module, Sequential
from fl_store.store_nn import ModuleStorage
from state import State
from fl_store.store_st import StateStorage
from typing import Dict, Optional, List, Tuple, Union
from net import NetSeq
from tools import Reinforcement, Finish
from basics import TestId, TENSOR_DTYPE, EVAL, GRAVITY_ACCELERATION_ABS
from structures import RealWorldStageStatusN
from math import atan2, pi
from nn_iface.norm import ListMinMaxNormalization, MinMax, MinMaxXY
from point import VectorComplex
import tomli
from nn_iface.projects import AbstractProject, ReadConfigInterface
from cfgconst import *
from DevTmpPr.cfg_str import *
from app_cfg import PROJECT_CONFIG_FILE, PROJECT_DIRECTORY_PATH
from DevTmpPr.cfg import ACTOR_INPUT, ACTOR_HIDDEN, ACTOR_OUTPUT, ACTOR_OPTIONS
from DevTmpPr.cfg import CRITIC_INPUT, CRITIC_HIDDEN, CRITIC_OUTPUT, CRITIC_OPTIONS

# if __name__ == '__main__':



class ReadConfig(ReadConfigInterface):
    """ Чтение настроек проекта из файла .toml """
    def __init__(self, project_dir: str):
        self.__project_dir = project_dir
        self.__project_toml = self.__project_dir + PROJECT_CONFIG_FILE

    def load_config(self) -> Dict:
        # temp = getcwd()
        with open(self.__project_toml, "rb") as toml_fh:
            config_dict = tomli.load(toml_fh)

        return config_dict


class InterpretConfig():
    """ Интерпретация настроек, загруженных из файла .toml """
    def __init__(self, config: Dict):
        self._config: Dict = config
        self._actor: Dict = config[R_NEURONNET][ACTOR_BLOCK]
        self._critic: Dict = config[R_NEURONNET][CRITIC_BLOCK]
        self._storage: Dict = config[R_STORAGE_BLOCK][STORAGE_FILE_BLOCK]

        try:
            self._actor_layers = self._actor['Size']['layers']
        except KeyError:
            # Если этого ключа в словаре нет, значит ищем раздел [.Actor.Layers]
            pass
        else:
            # А если ключ есть, то раздел [.Actor.Layers] игнорируем
            self._actor_sec = []

        self._minmax_interpret(config[MINMAX_BLOCK])

    def _minmax_interpret(self, minmax: Dict):
        """ Интерпретация словаря настроек диапазонов входных данных актора. """

        # Диапазон положения изделия в СКИП.
        x_min, x_max = (self._eval(value) for value in minmax[POSITION_BLOCK][X_MINMAX_LIST])
        y_min, y_max = (self._eval(value) for value in minmax[POSITION_BLOCK][Y_MINMAX_LIST])
        self._mm_position: MinMaxXY = MinMaxXY(MinMax(x_min, x_max), MinMax(y_min, y_max))

        # Диапазон корости изделия в СКИП.
        x_min, x_max = (self._eval(value) for value in minmax['Velocity']['x'])
        y_min, y_max = (self._eval(value) for value in minmax['Velocity']['y'])
        self._mm_velocity: MinMaxXY = MinMaxXY(MinMax(x_min, x_max), MinMax(y_min, y_max))

        # Диапазон ускорения изделия в СКИП
        x_min, x_max = (self._eval(value) for value in minmax['Acceleration']['x'])
        y_min, y_max = (self._eval(value) for value in minmax['Acceleration']['y'])
        self._mm_acceleration: MinMaxXY = MinMaxXY(MinMax(x_min, x_max), MinMax(y_min, y_max))

        # Диапазон ориентации изделия
        x_min, x_max = (self._eval(value) for value in minmax['Angular']['orientation'])
        self._mm_orientation: MinMax = MinMax(x_min, x_max)

        # Диапазон угловой скорости.
        x_min, x_max = (self._eval(value) for value in minmax['Angular']['velocity'])
        self._mm_ang_velocity: MinMax = MinMax(x_min, x_max)

        # Диапазон угловго ускорения.
        x_min, x_max = (self._eval(value) for value in minmax['Angular']['acceleration'])
        self._mm_ang_acceleration: MinMax = MinMax(x_min, x_max)

    def _eval_seq(self, value: str) -> Module:
        """ Превращение строки в модуль нейросети, если это возможно.

        :param value: Модуль нейросети в виде строки.
        :return: Модуль нейросети.
        :exception TypeError:
        """
        if len(value) > len(EVAL) and value[:len(EVAL)] == EVAL:
            # Входящая строка имеет длинну больше, чем маркер строки с вычисляемым выражением
            # и в начале этой строки, собственно, стоит маркер строки с вычисляемым выражением.
            return eval(value[len(EVAL):])
        else:
            # Вычисляемого выражения в строке нет, возвращаем as is.
            raise TypeError("Input argument couldn't evaluating.")

    def _eval(self, value: Union[str, float, int]) -> Union[float, str]:
        """ Вычисление значения строкового выражения из файла настроек.

        :param value: Строка с вычисляемым выражением.
        :return: Или результат вычисления выражения, или исходная строка без изменений."""

        if isinstance(value, float):
            # Если на входе число, то ничего с ним не делаем.
            return value

        if len(value) > len(EVAL) and value[:len(EVAL)] == EVAL:
            # Входящая строка имеет длинну больше, чем маркер строки с вычисляемым выражением
            # и в начале этой строки, собственно, стоит маркер строки с вычисляемым выражением.
            return eval(value[len(EVAL):])
        else:
            # Вычисляемого выражения в строке нет, возвращаем as is.
            return value

    def _net_tiny(self, net_name: str, net: Dict) -> Tuple[int, int, int | None, int]:
        """ Разбор секции с основными параметрами нейросети. """
        for key, value in net.items():
            if not isinstance(value, int):
                raise TypeError('In {} toml-section wrong type: {}'.format(net_name, value.__class__))

        try:
            layers = net['layers']
        except KeyError:
            # Если этого ключа нет, значит нейросеть будет строится RunTime по секции [.Actor.Layers]
            layers = None

        return net['input'], net['hidden'], layers, net['output']

    def actor(self) -> Tuple[int, int, int | None, int]:
        """ Параметры актора (количество: входов, нейронов в скрытых слоях, скрытых слоёв, выходов). """

        return self._net_tiny('Actor', self._actor['Size'])

    def critic(self) -> Tuple[int, int, int | None, int]:
        """ Параметры критика (количество: входов, нейронов в скрытых слоях, скрытых слоёв, выходов). """

        return self._net_tiny('Critic', self._critic['Size'])

    def input_minmax(self) -> Tuple[MinMaxXY, MinMaxXY, MinMaxXY, MinMax, MinMax, MinMax]:
        """ Пределы входных данных актора. """
        return self._mm_position, self._mm_velocity, self._mm_acceleration, \
               self._mm_orientation, self._mm_ang_velocity, self._mm_ang_acceleration

    def get_filenames(self) -> Tuple[str, str]:
        """ Имена файлов для хранения структуры нейросети и состояния тренировки. """
        return self._storage['neuron_net'], self._storage['traning_state']


class ProjectMainClass(AbstractProject):
    """ Конкретный проект испытываемой системы управления. Конкретизирующие настроечные параметры тут. """
    def __init__(self):
        super().__init__()
        # self.__model_name: str = "first"
        # self.__project_dir: str = PROJECT_DIRECTORY_PATH

        # nn_fn: str = PROJECT_DIRECTORY_PATH +

        # config_dict: Dict = ReadConfig('.\DevTmpPr').load_config()
        self._config: InterpretConfig = InterpretConfig(ReadConfig(PROJECT_DIRECTORY_PATH).load_config())

        nn_filename, state_filename = self._config.get_filenames()
        nn_filename, state_filename = PROJECT_DIRECTORY_PATH + nn_filename, PROJECT_DIRECTORY_PATH + state_filename

        # Хранилища для модуля НС
        # self._load_storage_model = ModuleStorage(self.__model_name)
        self._load_storage_model = ModuleStorage(nn_filename)
        self._save_storage_model = self._load_storage_model
        # Хранилище для состояния процесса обучения.
        # self._load_storage_training_state = StateStorage(self.__model_name)
        self._load_storage_training_state = StateStorage(state_filename)
        self._save_storage_training_state = self._load_storage_training_state
        # Хранилище для состояния НС
        self._load_storage_model_state = self._load_storage_training_state
        self._save_storage_model_state = self._load_storage_training_state

        self._training_state = State()

        # В хранилище состояния процесса сохраняться не будет.
        self._device = "cuda:0" if cuda.is_available() else "cpu"

        self._reinforcement = Reinforcement()

        self._finish = Finish()

        self.__normaliaztion: ListMinMaxNormalization = ListMinMaxNormalization(list(self._config.input_minmax()))

        # self.__normaliaztion: ListMinMaxNormalization = ListMinMaxNormalization([
        #     MinMaxXY(MinMax(-100., 100.), MinMax(-10., 500.)),  # дистанция
        #     MinMaxXY(MinMax(-100., 100.), MinMax(-100., 100.)), # линейная скорость
        #     MinMaxXY(MinMax(-10 * GRAVITY_ACCELERATION_ABS, 10 * GRAVITY_ACCELERATION_ABS),
        #              MinMax(-10 * GRAVITY_ACCELERATION_ABS, 10 * GRAVITY_ACCELERATION_ABS)),    # лин. ускорение
        #     MinMax(-pi, +pi),   # ориентация (угол от вертикали в СКИП)
        #     MinMax(-pi/18, +pi/18),   # угловая скорость
        #     MinMax(-pi/180, +pi/180)])   # угловое ускорение
        #     # MinMax(0, 6000)])   # time_stamp

    def load_nn(self) -> None:
        try:
            super().load_nn()
        except FileNotFoundError:
            # Создание нейросетей.
            #
            # Актор.
            # # количество входов
            # ac_input = 9
            # # количество нейронов в скрытом слое
            # ac_hidden = ac_input
            # # количество выходов
            # ac_output = 5
            # # количество скрытых слоёв
            # ac_layers = 1
            # self._actor = Net(ac_input, ac_hidden, ac_output, ac_layers, True)

            # self._actor: Net = Net(*self._config.actor(),True)
            # todo Временная заглушка
            # self._actor: Module = NetSeq(Sequential(Sigmoid()),
            #                              Sequential(Linear(9, 9, bias=False), Sigmoid()),
            #                              Sequential(Linear(9, 5, bias=False), Sigmoid()),
            #                              initWeights=True)
            inp: Sequential = Sequential(*ACTOR_INPUT)
            hid: Sequential = Sequential(*ACTOR_HIDDEN)
            out: Sequential = Sequential(*ACTOR_OUTPUT)
            self._actor: Module = NetSeq(inp, hid, out, **ACTOR_OPTIONS)

            #
            # Критик.
            # размерность ac_input уже включает в себя размерность входных данных плюс один вход на подкрепление
            # Но в данном случае, на вход критика уже подаётся подкрепление ставшее результатом данного шага,
            # а не предыдущего.
            # вход критика = выход актора + вход актора
            # cr_input = ac_output + ac_input
            # cr_hidden = cr_input
            # cr_output = 1
            # cr_layers = 1
            # self._critic = Net(cr_input, cr_hidden, cr_output, cr_layers, True)

            # self._critic = Net(*self._config.critic(), True)
            # todo временная заглушка
            # self._critic: Module = NetSeq(Sequential(Sigmoid()),
            #                               Sequential(Linear(14, 14, bias=False), Sigmoid()),
            #                               Sequential(Linear(14, 1, bias=False), Sigmoid()),
            #                               initWeights=True)
            inp: Sequential = Sequential(*CRITIC_INPUT)
            hid: Sequential = Sequential(*CRITIC_HIDDEN)
            out: Sequential = Sequential(*CRITIC_OUTPUT)
            self._critic: Module = NetSeq(inp, hid, out, **CRITIC_OPTIONS)

    def load_state(self) -> None:
        try:
            # # загружаем состояние из хранилища
            super().load_state()
        except FileNotFoundError:
            # Задание начальных состояний для параметров испытаний.
            self._training_state.batch_size = 1
            self._training_state.epoch_start = 0
            self._training_state.epoch_current = 0
            self._training_state.epoch_stop = 2
            self._training_state.prev_q_max = 0

    def actor_input_preparation(self, raw_batch: Dict[TestId, RealWorldStageStatusN]) -> Tensor:
        """

        :param raw_batch: raw steak (сырое мясо) - словарь неподготовленных исходных данных
        :return: входной тензор актора.
        """
        # Список-заготовка (rare steak, стейк с кровью) входных данных, список списков,
        # элемент которого является состоянием изделия.
        rare_list: List[List[Optional[float]]] =[[] for a in range(len(raw_batch))]
        # Список-заготовка идентификаторов испытаний (Необходим в будущем для состыковки результатов с идентификаторами)
        test_id_list: List[TestId] = [0 for a in range(len(raw_batch))]

        for index, (key, value) in enumerate(raw_batch.items()):
            # Из словаря данных для батча извлекаем параметры состояний для каждого испытания.

            # Ориентация изделия (угол отклонения в радианах от оси OY в СКЦМ)
            orientation_rad: float = 0 if value.orientation.x == 0 else atan2(-value.orientation.x, value.orientation.y)

            # Проверка знака угла для правой и левой координатной полуплоскости
            # В правой полуплоскости знак угла отрицательный, в левой - положительный (отсчёт от оси OY СКЦМ)
            assert (value.orientation.x > 0 and orientation_rad < 0) \
                   or (value.orientation.x < 0 and orientation_rad > 0) \
                   or (value.orientation.x == 0 and orientation_rad == 0), \
                "Signs mismatch for angle and vector orientation"

            rare_list[index] = self.__normaliaztion.normalization([value.position, value.velocity, value.acceleration,
                                                             orientation_rad,
                                                             value.angular_velocity, value.angular_acceleration])

            test_id_list[index] = key

            rare_float_list: List[float] = []
            for i, state_element in enumerate(rare_list[index]):
                if isinstance(state_element, VectorComplex):
                    rare_float_list.extend([state_element.x, state_element.y])
                elif isinstance(state_element, float):
                    rare_float_list.append(state_element)
                else:
                    raise TypeError('Wrong type object {} in list'.format(type(state_element)))
                # rare_float_list



        # Входной тензор.
        input: Tensor = tensor([rare_float_list], dtype=TENSOR_DTYPE, requires_grad=True)

        return input
