""" Главный запускаемый файл приложения, при проектировании структуры приложения через интерфейсы. """
# Пока ещё не работающий вариант.
# Приложение пока работает через main.py
from ifc_flow.i_disp import IFlowDispatcher
from thrds_tk.dispatch import ThreadsDispatcher


if __name__ == "__main__":
    app_dispatcher: IFlowDispatcher = ThreadsDispatcher()
    app_dispatcher.initialization()
    app_dispatcher.run()