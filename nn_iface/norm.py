""" Нормализация входных данных. """
from abc import ABC, abstractmethod
from typing import List
from typing import TypeVar, Dict, Optional, Tuple, Union
from point import VectorComplex
import asyncio
from app_cons import COROUTINE_SLEEP_TIME
import unittest

NeuronNetInput = TypeVar('NeuronNetInput', VectorComplex, float, int)
MinFloat, MaxFloat = float, float
# MinMaxList = TypeVar('MinMaxList', List[MinFloat, MaxFloat], List[List[MinFloat, MaxFloat], List[MinFloat, MaxFloat]])

class MinMax:
    """ Пара чисел, задающая диапазон величины. """
    def __init__(self, min: MinFloat, max: MaxFloat):
        self.__min: MinFloat = min
        self.__max: MaxFloat = max

    @property
    def min(self) -> MinFloat:
        return self.__min

    @property
    def max(self) -> MaxFloat:
        return self.__max


class MinMaxXY:
    """ Диапазон сразу двух величин. """
    def __init__(self, x: MinMax, y: MinMax):
        self.__x: MinMax = x
        self.__y: MinMax = y

    @property
    def x(self) -> Tuple[MinFloat, MaxFloat]:
        return self.__x.min, self.__x.max

    @property
    def y(self) -> Tuple[MinFloat, MaxFloat]:
        return  self.__y.min, self.__y.max


class NormalizationInterface(ABC):
    """ Интерфейс нормализации входных данных актора. """
    @abstractmethod
    def normalization(self, denormalized: List[NeuronNetInput]) -> List[NeuronNetInput]:
        ...


class OneValueNormalisationInterface(ABC):
    """ Интерфейс нормализации одиночной величины. """
    @abstractmethod
    async def norm(self, denorm: NeuronNetInput) -> NeuronNetInput:
        """ Нормализация одной величины в диапазон 0..1.

        :param denorm: Величина, диапазон которой выходит за пределы 0..1, либо сильно неравномерен.
        :return: нормализованная величина входного аргумента
        """
        ...


class MinMaxNormalization(OneValueNormalisationInterface):
    """ Нормализация, через сжатие (или растягивание) диапазона исходных данных. """
    def __init__(self, minmax: MinMax):
        self.__zero: float = minmax.min
        self.__scale: float = 1 / (minmax.max - minmax.min)

    async def norm(self, denorm: float) -> float:
        await asyncio.sleep(COROUTINE_SLEEP_TIME)
        return (denorm - self.__zero) * self.__scale


class MinMaxVectorComplex(OneValueNormalisationInterface):
    """ Нормализация вектора класса VectorComlex. """
    def __init__(self, xy: MinMaxXY):
        self.__x: MinMaxNormalization = MinMaxNormalization(MinMax(*xy.x))
        self.__y: MinMaxNormalization = MinMaxNormalization(MinMax(*xy.y))
        # x_min, x_max = xy.x
        # y_min, y_max = xy.y
        # self.__dx_scale = 1 / (x_max - x_min)
        # self.__dy_scale = 1 / (y_max - y_min)

    async def norm(self, denorm: VectorComplex) -> VectorComplex:
        # await asyncio.sleep(COROUTINE_SLEEP_TIME)
        # return VectorComplex.get_instance(denorm.x * self.__dx_scale, denorm.y * self.__dy_scale)
        return VectorComplex.get_instance(await self.__x.norm(denorm.x), await self.__y.norm(denorm.y))


class ListMinMaxNormalization(NormalizationInterface):
    def __init__(self, bounds: List[Union[MinMax, MinMaxXY]]):
        self.__bounds: List[Optional[OneValueNormalisationInterface]] = [None for a in bounds]

        for index, value in enumerate(bounds):
            if isinstance(value, MinMax):
                self.__bounds[index] = MinMaxNormalization(value)
            elif isinstance(value, MinMaxXY):
                self.__bounds[index] = MinMaxVectorComplex(value)
            else:
                assert 'Element of method list argument is unknown class (or type).'

    def normalization(self, denormalized: List[NeuronNetInput]) -> List[NeuronNetInput]:
        # result: List[Optional[NeuronNetInput]] = [None for a in denormalized]
        tasks: List = [None for a in denormalized]

        loop = asyncio.new_event_loop()
        loop.set_debug(True)
        asyncio.set_event_loop(loop)

        for index, value in enumerate(denormalized):
            tasks[index] = self.__bounds[index].norm(value)

        futures = asyncio.gather(*tasks)
        all_results = loop.run_until_complete(futures)
        loop.close()

        for index, result in enumerate(all_results):
            if isinstance(result, BaseException):
                raise result

        return all_results


class NormTest(unittest.TestCase):
    def test_minmax(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        minmax = MinMaxNormalization(MinMax(-100, 100))
        self.assertEqual(0, asyncio.run(minmax.norm(-100)))
        self.assertEqual(0.5, asyncio.run(minmax.norm(0)))
        self.assertEqual(1, asyncio.run(minmax.norm(100)))
        # self.assertEqual()
        # self.assertEqual(minmax.no)

        loop.close()

    def test_minmaxvector(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        minmax = MinMaxVectorComplex(MinMaxXY(MinMax(-100, 100), MinMax(-100, 100)))
        self.assertTrue(VectorComplex.get_instance(0, 0) == asyncio.run(minmax.norm(VectorComplex.get_instance(-100, -100))))
        self.assertTrue(VectorComplex.get_instance(0.5, 0.5) == asyncio.run(minmax.norm(VectorComplex.get_instance(0, 0))))
        self.assertTrue(VectorComplex.get_instance(1, 1) == asyncio.run(minmax.norm(VectorComplex.get_instance(100, 100))))

        loop.close()


if __name__ == "__main__":
    unittest.main()