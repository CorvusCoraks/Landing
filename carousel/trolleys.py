""" Реализации конкретных 'вагонеток' для каруселей из реальных данных. """
from carousel.atrolley import ATrolley, TestId
from structures import RealWorldStageStatusN, StageControlCommands, QueueContent, T
from typing import TypeVar, Tuple




class AnyTrolley(ATrolley):
    def __init__(self, cargo_default: T):
        # QueueContent.__init__(self)
        ATrolley.__init__(self)
        # self._cargo_type = cargo_type
        self._cargo = cargo_default

    def unload(self, to_object: T) -> Tuple[TestId, bool]:
        self._cargo.data_copy(to_object)
        self._is_loaded = False
        return self._test_id, self._is_initial

    def load(self, test_id: TestId, from_object: T, initial=False) -> None:
        # ATrolley.load(self, test_id, from_object)
        self._test_id = test_id
        self.is_initial = initial
        from_object.data_copy(self._cargo)
        self._is_loaded = True


# class RealWorldTrolleyN(AnyTrolley):
#     def __init__(self, cargo_default: RealWorldStageStatusN):
#         AnyTrolley.__init__(self, cargo_default)
#
#
# class CommandTrolleyN(AnyTrolley):
#     def __init__(self, cargo_default: StageControlCommands):
#         AnyTrolley.__init__(self, cargo_default)

# if __name__ == '__main__':
#     rw_trolley = RealWorldTrolleyN(RealWorldStageStatusN(time_stamp=0))


# class RealWorldTrolley(ATrolley, RealWorldStageStatusN):
#     """ 'Вагонетка' с объектом состояния в реальном мире. """
#     def __init__(self):
#         RealWorldStageStatusN.__init__(self)
#         ATrolley.__init__(self)
#
#     def unload(self, to_object: RealWorldStageStatusN):
#         self.data_copy(to_object)
#         self._is_loaded = False
#
#     def load(self, test_id: int, from_object: RealWorldStageStatusN):
#         # ATrolley.load(self, test_id, from_object)
#         self._test_id = test_id
#         from_object.data_copy(self)
#         self._is_loaded = True
#
#
# class CommandTrolley(ATrolley, StageControlCommands):
#     def __init__(self):
#         StageControlCommands.__init__(self, -1)
#         Trolley.__init__(self)

    # def unload(self, to_object: StageControlCommands):
    #     self.data_copy(to_object)
    #     self._is_loaded = False
    #
    # def load(self, test_id: int, from_object: StageControlCommands):
    #     # ATrolley.load(self, test_id, from_object)
    #     self._test_id = test_id
    #     from_object.data_copy(self)
    #     self._is_loaded = True
