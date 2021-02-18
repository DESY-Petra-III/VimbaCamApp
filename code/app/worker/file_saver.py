from app.common.imports import *

__all__ = ["FilesavingRunner"]

class FilesavingRunner(QtCore.QRunnable):
    """
    Simple thread saving a file
    """
    def __init__(self, filename, image, feedback=None):
        QtCore.QRunnable.__init__(self)
        self.setAutoDelete(True)

        self.filename = filename
        self.image = image
        self.feedback = feedback

    def run(self) -> None:
        try:
            if isinstance(self.image, QtGui.QImage):
                self.image.save(self.filename)
        except (IOError, OSError) as e:
            self.reportMessage("Error while saving file ({}): {}".format(self.filename, e))

    def reportMessage(self, msg):
        if self.feedback is not None:
            try:
                print(msg)
            except AttributeError:
                pass