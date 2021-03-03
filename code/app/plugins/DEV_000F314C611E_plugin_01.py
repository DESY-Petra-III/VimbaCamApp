from .common.base_tango import TangoMover

__all__ = ["get_version", "move_xy"]
__version__ = "0.0.1"
__description__ = "LH-UP Sample Stack YZ"


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
    print("\nMoving by dx:dy ({}:{})".format(dx, dy))

    # x, y, convx, convy - in frame coordinates x is horizontal, y is vertical
    corr = 1e-4 * 2.255
    m = TangoMover("haspp02oh1:10000/p02/motor/eh2a.10", "haspp02oh1:10000/p02/motor/eh2a.05", corr, corr, brealmove=True)
    m.run(dx=dx, dy=dy)
