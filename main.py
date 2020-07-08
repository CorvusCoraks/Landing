# Главный файл. Диспетчер.
from physics import Vector
from graph import FirstStage, Window
from queue import Queue
from threading import Thread
from point import Point, Transform
import cmath
import decart

# очередь для передачи информации из нити нейтросети в основную нить (нить канвы)
q = Queue()


# фунция нити нейросети
def thread_func(queue: Queue):
    """
    Метод, запускаемый в отдельной нитке для обучения нейросети.

    :param queue: очередь, для передачи даннных в модуль визуализации
    :return:
    """
    print("вход в функцию дополнительной нитки")
    # начальная ориентация объекта в системе координат канвы
    orientation = Point(0., 1.)
    for i in range(10):
        new_orientation = Point()
        # АХТУНГ!
        # В левой системе координат (система координат канвы) положительный угол поворота - по часовой стрелке!
        # Т. е., положительный угол поворота,
        # это угол поворота от положительной полуоси абцисс к положительной полуоси ординат
        # новая ориентация
        # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        new_orientation.cardanus = orientation.cardanus * cmath.rect(1., (cmath.pi / 36))
        # отправляем новое абсолютное положение в системе координат канвы и абсолютный угол (относительно положительной
        # полуоси абцисс) ориентации объекта в очередь
        q.put(Transform(Point(55, 20 + i * 10), new_orientation, "Команда №{}".format(i)))
        # запоминаем ориентацию, для использования в следующей итерации
        orientation = new_orientation


def getDataForCanvas():
    # получение данных для канвы
    # НЕ НУЖНА, в перспективе убрать

    print("in getDataFromCanvas")


# Создание отдельной нити для нейросети
th = Thread(target=thread_func, name="NeuroNetThread", args=(q,))
th.start()

# Создание окна визуализации
window = Window(getDataForCanvas, q)

th.join()