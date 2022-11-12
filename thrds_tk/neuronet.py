from ifc_flow.i_flow import INeuronet
from thrds_tk.threads import AYarn


class NeuronetThread(INeuronet, AYarn):
    """ Нить нейросети. """
    def initialization(self) -> None:
        pass

    def run(self) -> None:
        pass

    def _yarn_run(self, *args, **kwargs) -> None:
        pass


