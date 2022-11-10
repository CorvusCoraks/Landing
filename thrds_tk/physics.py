from ifc_flow.i_flow import IPhysics
from threading import Thread


class PhysicsThread(IPhysics, Thread):
    def initialization(self):
        pass

    def run(self):
        pass
