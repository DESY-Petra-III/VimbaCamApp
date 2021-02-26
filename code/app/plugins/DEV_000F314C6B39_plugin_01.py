from .base_tango import Mover

__all__ = ["get_version", "move_xy"]
__version__ = "0.0.1"
__description__ = "Sample Stage YZ"

def get_version():
    """
    Returns a version of a plugin - must be present
    """
    global __version__
    return __version__

def get_description():
    """
    Returns a short description
    """
    global __description__
    return __description__

def move_xy(*args):
    """
    Performes a movement - must be present
    """
    dx, dy = args
    print("Moving to dx:dy ({}:{})".format(dx, dy))
    # x, y, convx, convy - in frame coordinates x is horizontal, y is vertical
    m = Mover("haspp02oh1:10000/p02/motor/eh2b.42", "haspp02oh1:10000/p02/motor/eh2b.37", -1., 1., brealmove=False)
    m.run(dx=dx, dy=dy)
