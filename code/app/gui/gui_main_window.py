from app.common.imports import *

from  app.ctrl import *

from .gui_toolbar import *

class MainWindow(QtWidgets.QMainWindow, Tester):
    DELAY_TIMER = 0

    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 800

    TOOLBAR_DUMMY = 35

    DEFAULT_STATUSMSG_TIMEOUT = 5000

    def __init__(self, id, zmq, parent=None):
        QtWidgets.QMainWindow.__init__(self,parent=parent)
        Tester.__init__(self, def_file="{}".format(self.__class__.__name__.lower()))

        # params
        self.zmq = zmq
        self.id = id

        self.prepUi()

        # toobar
        self.toolbarw = None
        self.toobar = None

        self.prepToolbar()
        self.prepStatusBar()

        self._tid = self.startTimer(self.DELAY_TIMER)

    def prepUi(self):
        """
        Prepares initial interface
        :return:
        """
        self.setWindowTitle("Camera: {}".format(self.id))
        self.resize(self.DEFAULT_HEIGHT, self.DEFAULT_WIDTH)

        self.readConfiguration()

        self.view = QtWidgets.QGraphicsView()
        self.view.setAlignment(QtCore.Qt.AlignCenter)
        self.view.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)

        self.scene = QtWidgets.QGraphicsScene(parent=self.view)

        # make a layout
        self.cwidget = QtWidgets.QWidget(parent=self)
        self.twidget = QtWidgets.QWidget(parent=self.cwidget)
        self.twidget.setMinimumHeight(self.TOOLBAR_DUMMY)
        self.twidget.setMaximumHeight(self.TOOLBAR_DUMMY)

        self.cwidget.setLayout(QtWidgets.QVBoxLayout())
        l: QtWidgets.QVBoxLayout = self.cwidget.layout()
        l.addWidget(self.twidget)
        l.addWidget(self.view)

        self.view.setScene(self.scene)

        self.setCentralWidget(self.cwidget)

    def prepToolbar(self):
        """
        Prepares the toolbar widget
        :return:
        """
        self.toolbarw = CameraToolbarWidget()

        self.toobar = QtWidgets.QToolBar(self)
        self.toobar.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed))

        self.toobar.addWidget(self.toolbarw)
        self.toobar.setFixedHeight(50)
        self._resizeToolBar()

    def prepStatusBar(self):
        """
        Prepares status bar of the main window
        :return:
        """
        self.status_bar = QtWidgets.QStatusBar(parent=self)
        self.setStatusBar(self.status_bar)

    def reportStatusBarMessage(self, msg):
        """
        Reports status bar message
        :return:
        """
        self.status_bar.showMessage(msg, self.DEFAULT_STATUSMSG_TIMEOUT)

    def getScene(self):
        """
        Returns QGraphicScene handle
        :return:
        """
        return self.scene

    def getView(self):
        """
        Returns QGraphicsView handle
        :return:
        """
        return self.view

    def timerEvent(self, a0: 'QTimerEvent') -> None:
        """
        Timer event making sure that the windows is shown only after eventloop setup
        :param a0:
        :return:
        """
        self.killTimer(self._tid)

        # controller
        self.ctrl = CtrlMainWindow(self.id, self.zmq, parent=self)
        self.ctrl.registerStatusMessage(self.reportStatusBarMessage)
        self.toolbarw.setController(self.ctrl)

        self.view.wheelEvent = self.processViewWheelEvent
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.show()

    def processViewWheelEvent(self, ev: QtGui.QWheelEvent):
        """
        Processes mouse wheel event tied to the controller zoom action
        :param ev:
        :return:
        """
        delta = ev.angleDelta().y()

        if self.ctrl != None:
            if delta < 0:
                self.ctrl.processZoomIn()
            else:
                self.ctrl.processZoomOut()

    def readConfiguration(self):
        pass

    def writeConfiguration(self):
        pass

    def closeEvent(self, *args, **kwargs):
        """
        Closing of the window results in application exit
        :param args:
        :param kwargs:
        :return:
        """
        try:
            self.ctrl.cleanup()
        except AttributeError:
            pass

    def resizeEvent(self, ev: QtGui.QResizeEvent):
        """
        Make sure the toolbar takes the same size as the window
        :param args:
        :param kwargs:
        :return:
        """
        try:
            self._resizeToolBar()
        except AttributeError:
            pass

        QtWidgets.QMainWindow.resizeEvent(self, ev)

    def _resizeToolBar(self):
        self.toobar.resize(QtCore.QSize(self.size().width(), self.toolbarw.size().height()))


    def makeFrameObject(self, bhidden=False):
        """
        Dummy view used for tests - QGraphicsView has an issue with css padding
        :return:
        """
        scene = self.scene
        self.bkgpxmap = None
        self.framerectgroup = None

        PENWIDTH_FRAME = 3
        PENCOLOR_FRAME = QtGui.QColor(255, 0, 0, 200)

        if self.bkgpxmap is None:
            w, h = 600, 400
            pxmap = QtGui.QPixmap(w, h)
            pxmap.fill(QtGui.QColor(200, 255, 255))
            self.bkgpxmap = QtWidgets.QGraphicsPixmapItem(pxmap)

            xoff, yoff = int(-w / 2), int(-h / 2)
            self.bkgpxmap.setOffset(xoff, yoff)

            self.bkgoffset = [xoff, yoff]

            scene.addItem(self.bkgpxmap)

        if self.bkgpxmap is not None:
            br = self.bkgpxmap.boundingRect()

            if self.framerectgroup is None:
                self.framerectgroup = QtWidgets.QGraphicsItemGroup()
                self.framerect = QtWidgets.QGraphicsRectItem(br)

                pen = self.framerect_pen = QtGui.QPen(PENCOLOR_FRAME)
                pen.setWidth(PENWIDTH_FRAME)

                # cursor remains in the center, offset only changes
                cs_left = QtWidgets.QGraphicsLineItem(-15, 0, -5, 0)
                cs_right = QtWidgets.QGraphicsLineItem(5, 0, 15, 0)
                cs_top = QtWidgets.QGraphicsLineItem(0, 5, 0, 15)
                cs_bottom = QtWidgets.QGraphicsLineItem(0, -5, 0, -15)

                for el in (cs_top, cs_left, cs_bottom, cs_right):
                    el.setPen(pen)
                    self.framerectgroup.addToGroup(el)

                # self.framerect.setPen(pen)
                # self.framerectgroup.addToGroup(self.framerect)

                scene.addItem(self.framerectgroup)

                self.debug("Added rect")
            else:
                self.framerect.setRect(br)