# from decart import complexChangeSystemCoordinates2
import shelve
# from structures import PrimitiveStageData
from typing import TypeVar

# result = complexChangeSystemCoordinates2(VectorComplex(tensor([[2., 1.]])), VectorComplex(tensor([[0., -1.]])), pi/4, isDiffType=True)
# print(result.decart)





# Если изменение идёт с правой на левую, то положительный поворот пр часовой стрелки
# Если изменение идёт с левой на левую, то положительный поворот по часовой стрелки
# Если изменение идёт с левой на правую, то положительный поворот против часовой стрелке
# Если изменение идёт с правой на правую, то положительный поворот против часовой стрелке
# Это всё проверено опытным путём....


# infin = VectorComplex.get_instance(float("inf"), float("inf"))
# infin = VectorComplex.get_instance(0., 1.)
# print(abs(infin))
# print(float("inf"))
# a = float("inf")

# x = tensor([[1., -1.], [1., 1.]], requires_grad=True).clone().detach()
# out = x.pow(2).sum()
# out.backward()
# print(x.grad)
# x.grad = tensor([[1., -1.], [1., 1.]])
# print(x.grad)

if __name__ == '__main__':
    foo = {'a': 'ee', 'b': 'ff'}
    bar = {'c': 'gg', 'd': 'hh'}
    keys = set(foo.keys())
    print(keys)
    print(foo)
    print(bar)
    foo.update(bar)
    print(foo)
