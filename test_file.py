# from decart import complexChangeSystemCoordinates2
import shelve
from structures import PrimitiveStageData

# result = complexChangeSystemCoordinates2(VectorComplex(tensor([[2., 1.]])), VectorComplex(tensor([[0., -1.]])), pi/4, isDiffType=True)
# print(result.decart)

# Если изменение идёт с правой на левую, то положительный поворот пр часовой стрелки
# Если изменение идёт с левой на левую, то положительный поворот по часовой стрелки
# Если изменение идёт с левой на правую, то положительный поворот против часовой стрелке
# Если изменение идёт с правой на правую, то положительный поворот против часовой стрелке
# Это всё проверено опытным путём....

# with shelve.open('test') as test_file:
#     print(test_file)

obj1 = object()
print(obj1)
obj2 = object()
print(obj2, '\n')
obj_none = None

print(obj1 or obj2)
print(obj_none or obj2)
print(obj1 or obj_none)
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
