from app.common.imports import *

__all__ = ["PluginExecutorRunnable"]

class PluginExecutorRunnable(QtCore.QRunnable):
    """
    Class executing plugins, parameters passed directly
    """
    def __init__(self, func, *args):
        QtCore.QRunnable.__init__(self)
        self.setAutoDelete(True)

        self.func = func
        self.params = args

    def run(self):
        """
        Executes a plugin  function with parameters
        The plugin should be well debugged
        """
        try:
            self.func(*self.params)
        except Exception as e:
            print("Error: {}".format(e))