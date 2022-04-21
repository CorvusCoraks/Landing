class StageControlCommands:
    """
    Команда на работу двигателей в определённый момент времени на определённый срок
    """
    def __init__(self, timeStamp: int, duration: int,
                 topLeft=False, topRight=False,
                 downLeft=False, downRight=False,
                 main=False):
        timeStamp = timeStamp
        duration = duration
        topLeft = topLeft
        topRight = topRight
        downLeft = downLeft
        downRight = downRight
        main = main