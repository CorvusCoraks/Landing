""" Главный файл. Диспетчер. Здесь создаются нити для параллельного исполнения """

# from physics import Vector
from graph import FirstStage, Window, PoligonWindow
from queue import Queue
from threading import Thread
from point import Transform, VectorComplex
import cmath
from physics import BigMap
import decart
from training import start_nb

# Частота кадров
frameRate = 1000

# очередь для передачи информации из нити нейтросети в основную нить (нить канвы)
q = Queue()

qPoligon = Queue()


# фунция нити нейросети
def thread_func(queue: Queue):
    """
    Метод, запускаемый в отдельной нитке для обучения нейросети.

    :param queue: очередь, для передачи даннных в модуль визуализации
    :return:
    """
    print("вход в функцию дополнительной нитки")
    #
    # запуск метода обучения сети
    # start_nb(frameRate)
    # получить новое положение и ориентацию объекта
    #
    # преобразовать положение и ориентацию объекта из системы координат пространства в систему координат канвы
    #
    # отправить новое положение и ориентацию (в системе координат канвы) в нить вывода
    # queue.put(Transform(Point(), Point(), ''))
    #
    # Блок имитационных данных для отображения
    # начальная ориентация объекта в системе координат канвы
    # orientation = Point(0., 1.)
    orientation = VectorComplex.getInstance(0., 1.)
    for i in range(10):
        # new_orientation = Point()
        new_orientation = VectorComplex.getInstance()
        # АХТУНГ!
        # В левой системе координат (система координат канвы) положительный угол поворота - по часовой стрелке!
        # Т. е., положительный угол поворота,
        # это угол поворота от положительной полуоси абцисс к положительной полуоси ординат
        # новая ориентация
        # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        new_orientation.cardanus = orientation.cardanus * cmath.rect(1., (cmath.pi / 36))
        # отправляем новое абсолютное положение в системе координат канвы и абсолютный угол (относительно положительной
        # полуоси абцисс) ориентации объекта в очередь
        # queue.put(Transform(Point(55, 20 + i * 10), new_orientation, "Команда №{}".format(i)))
        queue.put(Transform(VectorComplex.getInstance(55, 20 + i * 10), new_orientation, "Команда №{}".format(i)))
        # запоминаем ориентацию, для использования в следующей итерации
        orientation = new_orientation


# def getDataForCanvas():
#     # получение данных для канвы
#     # НЕ НУЖНА, в перспективе убрать
#
#     print("in getDataFromCanvas")

# Для нейросети надо создать отдельную нить, так как tkinter может работать исключительно в главном потоке.
# Т. е. отображение хода обучения идёт через tkinter в главной нити,
# расчёт нейросети и физическое моделирование в отдельной нити
# todo возможно, физическое моделирование тоже перенестти в отдельную нить (т. к. эти вычисления относительно просты)
# Создание отдельной нити для нейросети
th = Thread(target=thread_func, name="NeuroNetThread", args=(q,))
th.start()

# Ориентировочный срез полигона 300х100 км.
# Размер полигона в метрах!
# Мостшаб изображения (в километрах)
poligonScale = 4 / 1000
# Создание окна (визуально показывает ситуацию) испытательного полигона. Главная, текущая нить.
poligonWindow = PoligonWindow(frameRate, q, BigMap.width * poligonScale, BigMap.height * poligonScale, poligonScale)

# Создание окна визуализации
# window = Window(frameRate, q)



th.join()