from ifc_flow.i_flow import IPhysics
from thrds_tk.threads import AYarn


class PhysicsThread(IPhysics, AYarn):
    """ Нить физической модели. """

    def initialization(self) -> None:
        pass

    def run(self) -> None:
        pass

    def _yarn_run(self, *args, **kwargs) -> None:
        pass

