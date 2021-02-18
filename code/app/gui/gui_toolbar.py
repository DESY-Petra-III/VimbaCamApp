from app.common.imports import *
from app.gui.UI.ui_toolbar import Ui_Form

from app.config import main_config as config

from app.gui.gui_colors import *
from app.gui.gui_gain_exposure import *

__all__ = ["CameraToolbarWidget"]

class CameraToolbarWidget(QtWidgets.QWidget, Tester, Ui_Form):
    """
    Class implementing the most important widget on a toolbar
    """
    STYLE_COLORCROSS = """
    background-color: rgb({}, {}, {});
    /*border: 3px solid gray;*/
    border-radius: 5px;
    """
    STYLE_COLOR = "background-color: rgb({}, {}, {});"

    PROPERTY_DATA = "data"

    DEFAULT_FRAME_COLOR_INDEX = 222
    DEFAULT_MARKER_COLOR_INDEX = 222
    
    TEST_ZMQ_DELAY = 1000.

    def __init__(self, ctrl: QtCore.QObject = None, parent=None):
        """
        Constructor procedure
        :param ctrl: QObject
        """

        QtWidgets.QWidget.__init__(self, parent=parent)
        Tester.__init__(self, def_file="{}".format(self.__class__.__name__.lower()))

        Ui_Form.setupUi(self, self)

        self.ctrl = ctrl
        self.config = config.get_instance()

        # color object
        self.colors = ColorTable(parent=self)


        self.color_frame = None
        self.color_marker = None

        self._zmqtimer = None

        # test for zmq state change
        self._zmqtext = None

        self.settingsFromConfig()
        self.initEvents()

        self.initColorFrame()
        self.initColorMarker()

    def settingsFromConfig(self):
        """
        Prepare settings from config file
        :return:
        """
        cf = self.config.getcfFrameColorIndex()
        if not isinstance(cf, int):
            self.color_frame = self.DEFAULT_FRAME_COLOR_INDEX
        else:
            self.color_frame = cf

        cf = self.config.getcfMarkerColorIndex()
        if not isinstance(cf, int):
            self.color_marker = self.DEFAULT_MARKER_COLOR_INDEX
        else:
            self.color_marker = cf

        self.debug("Configuration color index (frame: {}) (marker: {})".format(self.color_frame, self.color_marker))

    def setController(self, ctrl):
        """
        Sets the controller
        :param ctrl:
        :return:
        """
        self.ctrl = ctrl

        cf = self.colors[self.color_frame]
        cm = self.colors[self.color_marker]

        self.setColorFrameStyle(cf)
        self.setColorMarkerStyle(cm)

        if self.ctrl is not None:
            try:
                self.ctrl.registerCameraState(self.processCameraState)
                self.ctrl.registerStopAcq(self.processStopAcq)
                self.ctrl.processShowHideFrame(self.cb_frame.checkState())
                self.ctrl.processShowHideMarker(self.cb_marker.checkState())

                self.startZMQcheck()
            except AttributeError:
                pass

    def initEvents(self):
        """
        Initializes the button events
        :return:
        """
        self.btn_zoomin.clicked.connect(self.processZoomIn)
        self.btn_zoomout.clicked.connect(self.processZoomOut)
        self.btn_zoomframe.clicked.connect(self.processZoomFrame)
        self.btn_playstop.toggled.connect(self.processPlayStop)
        self.btn_savefile.clicked.connect(self.processSaveFile)

        # visibility of objects
        self.cb_frame.toggled.connect(self.processShowHideFrame)
        self.cb_marker.toggled.connect(self.processShowHideMarker)

        # events controlling color of the frame and the marker
        self.w_colorframe.mousePressEvent = self.colorFrameMousePress
        self.w_colormarker.mousePressEvent = self.colorMarkerMousePress

        tcb_frame = bool(self.config.getcfFrameDisplay())
        tcb_marker = bool(self.config.getcfMarkerDisplay())

        self.debug("Configuration display (frame: {}) (marker: {})".format(tcb_frame, tcb_marker))

        self.cb_frame.setChecked(tcb_frame)
        self.cb_marker.setChecked(tcb_marker)

        self.lbl_gain.mouseReleaseEvent = self.processExposureGain
        self.lbl_exposure.mouseReleaseEvent = self.processExposureGain

    def initColorFrame(self):
        """
        Initializes widget for color choosing
        :return:
        """
        color: QtGui.QColor = self.colors[self.color_frame]
        self.setColorFrameStyle(color)

    def initColorMarker(self):
        """
        Initializes widget for color choosing
        :return:
        """
        color: QtGui.QColor = self.colors[self.color_marker]
        self.setColorMarkerStyle(color)

    def setColorFrameStyle(self, color):
        """
        Sets the style of the widget showing color of the color cross
        :return:
        """
        style = self.STYLE_COLORCROSS.format(color.red(), color.green(), color.blue())
        self.w_colorframe.setStyleSheet(style)

        if self.ctrl is not None:
            try:
                self.ctrl.setFrameColor(color)
            except AttributeError:
                pass

    def setColorMarkerStyle(self, color):
        """
        Sets the style of the widget showing color of the color cross
        :return:
        """
        style = self.STYLE_COLORCROSS.format(color.red(), color.green(), color.blue())
        self.w_colormarker.setStyleSheet(style)

        if self.ctrl is not None:
            try:
                self.ctrl.setMarkerColor(color)
            except AttributeError:
                pass

    def processZoomIn(self):
        """
        Processes zoom in action
        :return:
        """
        try:
            if self.ctrl is not None:
                self.ctrl.processZoomIn()
        except AttributeError:
            pass

    def processZoomOut(self):
        """
        Processes zoom out action
        :return:
        """
        try:
            if self.ctrl is not None:
                self.ctrl.processZoomOut()
        except AttributeError:
            pass

    def processZoomFrame(self):
        """
        Processes zoom frame action
        :return:
        """
        try:
            if self.ctrl is not None:
                self.ctrl.processZoomFrame()
        except AttributeError:
            pass

    def processPlayStop(self, bstate: bool):
        """
        Processes play/stop action
        :return:
        """
        try:
            if self.ctrl is not None:
                self.ctrl.processPlayStop(bstate)
        except AttributeError:
            pass

        # disable the exposure/gain control
        if bstate:
            self.lbl_exposure.setEnabled(True)
            self.lbl_gain.setEnabled(True)
        else:
            self.lbl_exposure.setEnabled(False)
            self.lbl_gain.setEnabled(False)

    def processShowHideFrame(self, bstate):
        """
        Processes show/hide frame action
        :return:
        """
        c = self.config
        try:
            if self.ctrl is not None:
                self.ctrl.processShowHideFrame(bstate)
                c.setcfFrameDisplay(int(bstate))
        except AttributeError:
            pass

    def processShowHideMarker(self, bstate):
        """
        Processes show/hide frame action
        :return:
        """
        c = self.config
        try:
            if self.ctrl is not None:
                self.ctrl.processShowHideMarker(bstate)
                c.setcfMarkerDisplay(int(bstate))
        except AttributeError:
            pass

    def colorFrameMousePress(self, ev: QtGui.QMouseEvent):
        """
        Processes mouse press events showing color cross menu
        :param ev:
        :return:
        """
        if ev.button() == QtCore.Qt.RightButton:
            menu = QtWidgets.QMenu(parent=self)

            twdgts = []
            for i in range(len(self.colors)):
                c = self.colors[i]
                w = QtWidgets.QWidget()
                twdgts.append(w)

                w.setMinimumHeight(30)
                w.setMinimumWidth(100)

                s = self.STYLE_COLOR.format(c.red(), c.green(), c.blue())
                w.setStyleSheet(s)

                w.setCursor(QtCore.Qt.PointingHandCursor)
                w.setToolTip("Index: {}; Color: rgb({}, {}, {})".format(i, c.red(), c.green(), c.blue()))

                a = QtWidgets.QWidgetAction(menu)
                a.setDefaultWidget(w)
                a.setProperty(self.PROPERTY_DATA, i)

                menu.addAction(a)

            wa = menu.exec_(ev.globalPos())

            while( len(twdgts) > 0 ):
                w = twdgts.pop(0)
                w.deleteLater()

            if isinstance(wa, QtWidgets.QWidgetAction):
                self.color_frame = wa.property(self.PROPERTY_DATA)
                c = self.colors[self.color_frame]
                self.setColorFrameStyle(c)
                self.config.setcfFrameColorIndex(self.color_frame)

            ev.accept()
        else:
            ev.ignore()

    def colorMarkerMousePress(self, ev: QtGui.QMouseEvent):
        """
        Processes mouse press events showing color cross menu
        :param ev:
        :return:
        """
        if ev.button() == QtCore.Qt.RightButton:
            menu = QtWidgets.QMenu(parent=self)

            for i in range(len(self.colors)):
                c = self.colors[i]
                w = QtWidgets.QWidget()

                w.setMinimumHeight(30)
                w.setMinimumWidth(100)

                s = self.STYLE_COLOR.format(c.red(), c.green(), c.blue())
                w.setStyleSheet(s)

                w.setCursor(QtCore.Qt.PointingHandCursor)
                w.setToolTip("Index: {}; Color: rgb({}, {}, {})".format(i, c.red(), c.green(), c.blue()))

                a = QtWidgets.QWidgetAction(menu)
                a.setDefaultWidget(w)
                a.setProperty(self.PROPERTY_DATA, i)

                menu.addAction(a)

            wa = menu.exec_(ev.globalPos())

            if isinstance(wa, QtWidgets.QWidgetAction):
                self.color_marker = wa.property(self.PROPERTY_DATA)
                c = self.colors[self.color_marker]
                self.setColorMarkerStyle(c)
                self.config.setcfMarkerColorIndex(self.color_marker)

            ev.accept()
        else:
            ev.ignore()

    def processStopAcq(self):
        """
        Processes the signal stoping acquisition
        :return:
        """
        self.btn_playstop.blockSignals(True)
        self.btn_playstop.setChecked(False)
        self.btn_playstop.blockSignals(False)

    def processExposureGain(self, ev):
        """
        Shows the menu with gain/exposure controls on a mouse right button click
        :param ev:
        :return:
        """
        if ev.button() == QtCore.Qt.RightButton:
            if self.ctrl is not None:
                try:
                    if self.testExposureGainEnabled():
                        self.ctrl.showGainExposureMenu(ev.globalPos())
                except AttributeError:
                    pass

    def testExposureGainEnabled(self):
        """
        Performs a test if we can show menu with gain exposure
        :return:
        """
        res = True
        if False in (self.lbl_gain.isEnabled(), self.lbl_exposure.isEnabled()):
            res = False
        return res

    def processCameraState(self, bstate):
        """
        Processes changes of camera state - enabling or disabling certain things
        :return:
        """
        if bstate:
            self.btn_playstop.blockSignals(True)
            self.btn_playstop.setEnabled(True)
            self.lbl_exposure.setEnabled(False)
            self.lbl_gain.setEnabled(False)
            self.btn_playstop.setChecked(False)
            self.btn_playstop.blockSignals(False)
        else:
            self.btn_playstop.blockSignals(True)
            self.btn_playstop.setEnabled(False)
            self.btn_playstop.setChecked(False)

            self.lbl_exposure.setEnabled(False)
            self.lbl_gain.setEnabled(False)

            self.btn_playstop.blockSignals(False)

    def startZMQcheck(self):
        """
        Starts the ZMQ check adjusting the state
        :return:
        """
        self._zmqtimer = QtCore.QTimer()
        self._zmqtimer.setInterval(self.TEST_ZMQ_DELAY)
        self._zmqtimer.timeout.connect(self.checkZMQ)
        self._zmqtimer.start()

    def checkZMQ(self):
        """
        Performes a test using values reported by the controller class
        :return:
        """
        res = None
        if self.ctrl is not None:
            try:
                res = not self.ctrl.getZMQError()
                if isinstance(res, bool):
                    tstyle = ""
                    tmsg = "ZMQ"
                    if res:
                        tmsg += " online"
                        tstyle = "background-color: #50C763; font: bold; color: #000; padding: 3px 10px 3px 10px;"
                    else:
                        tmsg += " offline"
                        tstyle = "background-color: #C75071; font: bold; color: #000; padding: 3px;"


                    if self.lbl_zmq.text() != tmsg:
                        self.lbl_zmq.setStyleSheet(tstyle)
                        self.lbl_zmq.setText(tmsg)

                        if self._zmqtext is None:
                            self.lbl_zmq.setToolTip("ZMQ parameters: {}".format(self.ctrl.zmq))
                        self._zmqtext = tmsg
            except AttributeError:
                pass
        return res

    def processSaveFile(self):
        """
        Processes file saving
        :return:
        """
        if self.ctrl is not None:
            try:
                self.ctrl.processSaveFile()
            except AttributeError:
                pass

    def closeEvent(self, ev):
        """
        Performes cleanup of close event
        :param ev:
        :return:
        """
        if isinstance(self._zmqtimer, QtCore.QTimer) and self._zmqtimer.isActive():
            self._zmqtimer.stop()
