#from .elements import (Pool, Flow, Parameter, Equation, Step, Impulse, Process) # should get rid of this as it's not needed, everything should come from self
from .model import Model
from .manager import RunManager

# Plotter pulls in matplotlib, which DCP worker sandboxes don't have and don't
# need (workers only ever touch Model/RunManager). Importing it lazily means
# `import pycomod` stays cheap and safe on a worker - matplotlib is only
# imported, and can only fail, the moment client-side code actually does
# `pycomod.Plotter(...)`.
def __getattr__(name):
    if name == 'Plotter':
        from .plotter import Plotter
        return Plotter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
