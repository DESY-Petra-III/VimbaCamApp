from app.common.imports import *
from app.gui.UI.splash_screen import *

class AppSplashScreen(QtWidgets.QSplashScreen, Ui_SplashScreen):
    def __init__(self, pixmap=None):
        QtWidgets.QSplashScreen.__init__(self)

        if pixmap is None:
            pixmap = QtGui.QPixmap(":/bkg_image/splash_screen_02.png")

        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.setPixmap(pixmap)

        Ui_SplashScreen.__init__(self)
        self.setupUi(self)

        self._cnt = 3

        self.setWindowFlags( self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

    def addDummyMessage(self):
        """
        Adding a dummy message
        :return:
        """
        self.label.setText("Starting up.. {}".format(self._cnt))
        self._cnt = self._cnt - 1


