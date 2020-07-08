from physics import Vector
from graph import FirstStage, Window
from queue import Queue
from threading import Thread
from point import Point, Transform
import cmath
import decart
from tkinter import Tk, Canvas, colorchooser

# def callback4Tk(tk: Tk):
#     print("In callback function")
#     tk.after(1000, callback4Tk, tk)
#     print("End callbackTk")

# gloabal_decart = decart.from_stage_to_global([2, 1], [1, 3], - cmath.pi / 6)
gloabal_decart = decart.from_local_to_global([2, 1], [1, 3], - cmath.pi / 6)
canvas_decart = decart.from_local_to_global(gloabal_decart, [2, 5], 0., False)

vector = Vector(1, 3)
#vector = Vector()

print(vector)
print(vector.x())
print(vector.tensor_view())

# объект для передачи информации между нитями
q = Queue()


# фунция нити нейросети
def thread_func(queue: Queue):
    print("вход в функцию дополнительной нитки")
    orientation = Point(0., 1.)
    # __, phi = cmath.polar(orientation.cardanus)
    # print("Начальный угол: {}".format(phi))
    for i in range(10):
        # q.put("Объект из нити: {}".format(i))
        new_orientation = Point()
        # АХТУНГ!
        # В левой системе координат (система координат канвы) положительный угол поворота - по часовой стрелке!
        # Т. е., положительный угол поворота,
        # это угол поворота от положительной полуоси абцисс к положительной полуоси ординат
        new_orientation.cardanus = orientation.cardanus * cmath.rect(1., (cmath.pi / 36))

        # q.put(Transform(Point(0, 10), - (cmath.pi / 12)))
        # __, phi = cmath.polar(new_orientation.cardanus / orientation.cardanus)
        # print("Угол в функции нитки: {}".format(phi))
        q.put(Transform(Point(55, 20 + i * 10), new_orientation, "Команда №{}".format(i)))

        orientation = new_orientation


th = Thread(target=thread_func, name="NeuroNetThread", args=(q,))
# th.daemon = True
th.start()

def getDataForCanvas():
    # получение данных для канвы

    print("in getDataFromCanvas")

# вызов окна
# window = Window(windowAsk)
window = Window(getDataForCanvas, q)
# stage = FirstStage()

# stage.drow([100, 100], window.canvas())
# createWindow()

th.join()