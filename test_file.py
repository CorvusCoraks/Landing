# from decart import complexChangeSystemCoordinates2
from point import VectorComplex
from torch import tensor
from math import pi
import physics
from abc import ABC
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST

# result = complexChangeSystemCoordinates2(VectorComplex(tensor([[2., 1.]])), VectorComplex(tensor([[0., -1.]])), pi/4, isDiffType=True)
# print(result.decart)

# Если изменение идёт с правой на левую, то положительный поворот пр часовой стрелки
# Если изменение идёт с левой на левую, то положительный поворот по часовой стрелки
# Если изменение идёт с левой на правую, то положительный поворот против часовой стрелке
# Если изменение идёт с правой на правую, то положительный поворот против часовой стрелке
# Это всё проверено опытным путём....


root = Tk()
root.title("Stage view")
canvas = Canvas(root, width=100, height=100)
id = canvas.create_oval(20, 20, 50, 50, fill="red")
id.pack_forget()
canvas.pack()
root.mainloop()
