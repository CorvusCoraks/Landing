
# Разные утилиты


class Reinforcement():
    """
    Класс подкрепления.

    """
    # Подкрепление > 0 только в случае успешной посадки.
    # Подкрепление = 1 только в случае посадки в центр площадки. Чем ближе к центру, тем больше подкрепление.
    # Во всех остальных случаях - 0
    def getReinforcement(self):
        return 0