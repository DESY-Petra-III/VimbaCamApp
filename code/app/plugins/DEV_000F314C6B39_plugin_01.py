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

def move_xy(dx=None, dy=None):
    """
    Performes a movement - must be present
    """
    pass