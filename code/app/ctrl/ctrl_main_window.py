from app.common.imports import *
from app.common.keys import *

from app.config import main_config as config

from app.worker.zmq_worker import *

from app.gui.gui_colors import *
from app.gui.marker import *
from app.gui.gui_gain_exposure import *
from app.worker.file_saver import *
from app.worker.plugin_executor import *

from app.worker.allied_camera import ThreadCameraAllied
from app.worker.allied_camera_test import ThreadCameraAlliedTest


__all__ = ["CtrlMainWindow"]

class CtrlMainWindow(QtCore.QObject, Tester, MarkerMenuPlugin):
    """
    Controller responsible for the main window
    """
    signnewframe = QtCore.Signal(object)
    signcamerafeatures = QtCore.Signal(object)
    signstopacq = QtCore.Signal()
    signstatusmsg = QtCore.Signal(object)
    signcamerastate = QtCore.Signal(object)

    QUEUE_STOP_MSG = QUEUE_STOP_MSG

    PENWIDTH_FRAME = 3
    PENCOLOR_FRAME = QtGui.QColor(244, 0, 87)
    PENCOLOR_ALPHA = 200

    PENCOLOR_MARKER = QtGui.QColor(244, 0, 87)

    EXPOSURE_CONVERSION = 1000.

    CSS_APP = "app.css"

    SCALE_UPFACTOR = 1.1
    SCALE_DOWNFACTOR = 1. / SCALE_UPFACTOR

    MIN_SIZE = 50

    DEFAULT_FITVALUE = 0.9

    THREADPOOL_MAXNUM = 5

    def __init__(self, id, zmq, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        Tester.__init__(self, def_file="{}".format(self.__class__.__name__.lower()))

        # initialize the marker
        self.scene = parent.getScene()
        self.view = parent.getView()

        MarkerMenuPlugin.__init__(self, self.view, self.scene)

        # params
        self.id = id
        self.zmq = zmq

        # config
        self.config = config.get_instance()

        # first frame indicator - used to rescale the scene in such a way that the frame fits the screen
        self.bfirst_frame = False

        # queue to stop the threads
        self.qstop = queue.Queue()
        self.qstop_poll = queue.Queue()

        # queue to pass commands
        self.queue_cmd = queue.Queue()

        # need a thread to control start and stop of the camera + cleanup
        self.thread = None
        self.thread_poll = None

        self.registerSignalNewFrame()
        self.registerCameraFeatures()

        # image reference
        self.image = None
        self.image_lock = threading.Lock()

        # lock
        self.lock = threading.Lock()

        # intermediate camera info
        self.cam_exposure = None
        self.cam_exposure_lock = threading.Lock()
        self.cam_gain = None
        self.cam_gain_lock = threading.Lock()

        # view pixmap
        self.pxmap = None
        self.bkgoffset = [0, 0]

        # frame rect object
        self.framerectgroup = None
        self.framerect = None
        self.framerect_pen = None
        self.framerect_color = None

        # marker object
        self.marker = None

        # image scale variable used for rescaling
        self.image_scale = 1.

        # internal storage for values reported by a camera
        self.cam_values = {
            CAMERA_EXPOSUREMERGED: 0.,
            CAMERA_EXPOSUREMIN: 21.,
            CAMERA_EXPOSUREMAX: 10000000.,
            CAMERA_GAIN: 0.,
            CAMERA_GAINMAX: 31,
            CAMERA_GAINMIN: 0,
            CAMERA_FREQUENCY: 0.,
            CAMERA_WIDTH: 0.,
            CAMERA_HEIGHT: 0.,
            CAMERA_MODEL: "",
            CAMERA_INTERFACE: "",
            CAMERA_IP: "",
            CAMERA_CAPTURE_ALLOWED: False,
        }
        self.cam_values_lock = threading.Lock()

        # zmq control
        self.zmqserver = ZMQserver(self.zmq, qmsg=self.queue_cmd, ctrl=self)
        self.zmqserver.startZMQ()

        # test title
        self.zmqupdate_test = None

        # prepares position for an image
        self.makeImageObject()
        # prepares position for a frame
        self.makeFrameObject()
        # prepares a marker object
        self.makeMarkerObject()

        self.getStyleSheet()

        # start polling
        self.reportStateCamera(False)

        # thread pool for simple work
        self.thpool = QtCore.QThreadPool(parent=self)
        self.thpool.setMaxThreadCount(self.THREADPOOL_MAXNUM)

        # flag controlling if CTRL was pressed prior to a mouse click
        self.bviewctrl = False

        # frame or marker
        self.frame_marker_reference = None
        self.plugin_index = None

    def recordCameraGainExposure(self, gain=None, exposure=None):
        """
        Records camera gain or exposure using a threading lock for internal use
        :param gain:
        :param exposure:
        :return:
        """
        self.debug("Recording Exposure ({}); Gain ({})".format(exposure, gain))
        if gain is not None:
            with self.cam_gain_lock:
                self.cam_gain = gain

        if exposure is not None:
            with self.cam_exposure_lock:
                self.cam_exposure = exposure

    def getRecordedExposure(self):
        """
        Returns recorded intermediate exposure values
        :return:
        """
        res = None
        with self.cam_exposure_lock:
            res = self.cam_exposure
        return res

    def getRecordedGain(self):
        """
        Returns recorded intermediate exposure values
        :return:
        """
        res = None
        with self.cam_gain_lock:
            res = self.cam_gain
        return res

    def setFrameColor(self, color):
        """
        Sets the color of the cross in the middle of the field of view
        :param color:
        :return:
        """
        self.PENCOLOR_FRAME = color
        self.rescaleFramePen()

    def setMarkerColor(self, color):
        """
        Sets the color for a marker
        :param color:
        :return:
        """
        self.PENCOLOR_MARKER = color
        self.marker.setColor(color)

    def getStyleSheet(self):
        """
        Sets up a stylesheet for the application
        :return:
        """
        cssdata = ""

        css_path = os.path.join(self.config.getFolderHtml(), self.CSS_APP)

        try:
            with open(css_path, "r") as fh:
                css = fh.read()
                self.debug("Stylesheet, css file contents:\n{}".format(css))

                self.parent().setStyleSheet(css)
        except IOError:
            self.error("Stylesheet file {} is absent".format(css_path))

    def makeMarkerObject(self, bhidden=False):
        """
        Prepares a marker object
        :return:
        """
        scene = self.scene
        view = self.view
        c = self.config

        pw = c.getcfMarkerLinewidth()
        if not isinstance(pw, int):
            pw = None

        size = c.getcfMarkerSize()
        w, h = None, None
        if isinstance(size, list) or isinstance(size, tuple):
            v = size[0]
            if isinstance(v, int) or isinstance(v, float):
                w = float(v)
            v = size[1]
            if isinstance(v, int) or isinstance(v, float):
                h = float(v)

        shape = c.getcfMarkerShape()
        if not isinstance(shape, int):
            shape = None

        dx, dy = 0., 0.
        shift = self.config.getcfMarkerPosition()
        if isinstance(shift, tuple) or isinstance(shift, list) and len(shift)==2:
            tv = shift[0]
            if self.testInt(tv) or self.testFloat(tv):
                dx = tv

            tv = shift[1]
            if self.testInt(tv) or self.testFloat(tv):
                dy = tv


        self.marker = MarkerItem(feedback=self, dx=dx, dy=dy, penwidth=pw, width=w, height=h, shape=shape)

        scene.addItem(self.marker)
        view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)

        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def makeFrameObject(self, bhidden=False):
        """
        Makes a color frame object with a central mark
        :return:
        """
        c = self.config
        scene = self.scene

        if self.pxmap is not None:
            br = self.pxmap.boundingRect()

            if self.framerectgroup is None:
                self.framerectgroup = QtWidgets.QGraphicsItemGroup()
                self.framerect = QtWidgets.QGraphicsRectItem(br)

                pen = self.framerect_pen = QtGui.QPen(self.PENCOLOR_FRAME)
                pen.setWidth(self.PENWIDTH_FRAME)

                # cursor remains in the center, offset only changes
                cs_left = QtWidgets.QGraphicsLineItem(-15, 0, -5, 0)
                cs_right = QtWidgets.QGraphicsLineItem(5, 0, 15, 0)
                cs_top = QtWidgets.QGraphicsLineItem(0, 5, 0, 15)
                cs_bottom = QtWidgets.QGraphicsLineItem(0, -5, 0, -15)

                for el in (cs_top, cs_left, cs_bottom, cs_right):
                    el.setPen(pen)
                    self.framerectgroup.addToGroup(el)

                self.framerect.setPen(pen)
                self.framerectgroup.addToGroup(self.framerect)

                scene.addItem(self.framerectgroup)
            else:
                br = QtCore.QRectF(br.x()*self.image_scale, br.y()*self.image_scale,
                                   br.width()*self.image_scale, br.height()*self.image_scale)
                self.framerect.setRect(br)

    def makeImageObject(self):
        """
        Creates QGraphicsPixmapItem for image
        :return:
        """
        if self.pxmap is None:
            w, h = 200, 100
            pxmap = QtGui.QPixmap(w, h)
            pxmap.fill(QtGui.QColor(0, 230, 118))
            self.pxmap = QtWidgets.QGraphicsPixmapItem(pxmap)

            xoff, yoff = int(-w / 2), int(-h / 2)
            self.pxmap.setOffset(xoff, yoff)

            self.bkgoffset = [xoff, yoff]

            scene: QtWidgets.QGraphicsScene = self.parent().getScene()
            scene.addItem(self.pxmap)

    def cleanup(self):
        """
        Performes cleanup procedure. Stops camera thread if running.
        :return:
        """
        self.parent().hide()
        self.unregisterSignalNewFrame()

        # stops zmq server if running
        self.debug("Stopping ZMQ")
        if self.zmqserver.isRunning():
            self.zmqserver.stopZMQ()

        self.debug("Stopping main aquisition thread")
        # stops main acquisition thread if running
        if self.thread is not None and self.thread.is_alive():
            self.qstop.put(self.QUEUE_STOP_MSG)
            self.thread.join()

        self.debug("Stopping auxilary thread")
        # stops auxillary thread polling camera's  status if running
        if self.thread_poll is not None and self.thread_poll.is_alive():
            self.qstop_poll.put(self.QUEUE_STOP_MSG)
            self.thread_poll.join()

    def makeCameraFrame(self, numframes = -1):
        """
        Starts thread and
        :param numframes:
        :return:
        """
        self.debug("Making a frame {}".format(numframes))
        if self.thread is None or not self.thread.is_alive():
            self.thread = ThreadCameraAllied(self.id, self, frame_count=numframes, queue_stop=self.qstop,
                                             queue_cmd=self.queue_cmd)
            self.thread.apply_default_params()
            self.thread.start()

    def startCameraPolling(self):
        """
        Starts thread and
        :param numframes:
        :return:
        """
        self.debug("Starting camera polling")
        if self.thread is not None and self.thread.is_alive():
            self.qstop.put(self.QUEUE_STOP_MSG)
            self.thread.join()

        if self.thread_poll is None or not self.thread_poll.is_alive():
            self.thread_poll = ThreadCameraAlliedTest(self.id, self, queue_stop=self.qstop_poll)
            self.thread_poll.start()

    def registerSignalNewFrame(self):
        """
        Registers a signal processing new frame
        :return:
        """
        self.signnewframe.connect(self.processFrame)

    def unregisterSignalNewFrame(self):
        """
        Registers a signal processing new frame
        :return:
        """
        self.signnewframe.disconnect(self.processFrame)

    def reportNewFrame(self, frame):
        """
        Sends the new frame through the application signal pipeline
        :return:
        """
        tframe = copy.deepcopy(frame)
        self.signnewframe.emit(tframe)

    def processFrame(self, frame):
        """
        Processes data of a frame
        :param frame:
        :return:
        """
        self.debug("Processing a frame")

        with self.lock:
            # image processing is conducted in the thread, here we receive a prepared numpy array
            img = copy.deepcopy(frame)

            scene: QtWidgets.QGraphicsScene = self.parent().getScene()
            view: QtWidgets.QGraphicsView = self.parent().getView()

            # separate code for color and black and white
            bprocessed = False
            pxmap = None

            if isinstance(img, np.ndarray) and img.shape[2] == 1:                   # black and white
                self.debug("Frame shape {}; {};".format(img.shape, img.size))
                self.debug("First pixel {}".format(img[0, 0]))

                # convert numpy array into an image and a pixmap
                with self.image_lock:
                    self.image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                    QtGui.QImage.Format_Grayscale8)

                pxmap = QtGui.QPixmap.fromImage(self.image)
                self.pxmap.setPixmap(pxmap)

                bprocessed = True
            elif isinstance(img, np.ndarray) and img.shape[2] == 3:  # color
                self.debug("First pixel {}".format(img[0, 0]))
                self.debug("Frame shape {}; {};".format(img.shape, img.size))

                self.image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                          QtGui.QImage.Format_RGB888)

                pxmap = QtGui.QPixmap.fromImage(self.image)
                self.pxmap.setPixmap(pxmap)
                bprocessed = True

            # perform actions only if a frame was correctly prepareds
            if bprocessed:
                # test if the background offset needs to be calculated
                xoff, yoff = int(-img.shape[1]/2), int(-img.shape[0]/2)
                if self.bkgoffset[0] != xoff or self.bkgoffset[1] != yoff:

                    self.bkgoffset = [xoff, yoff]
                    self.pxmap.setOffset(xoff, yoff)
                    self.debug("New image offset: {} {}".format(xoff, yoff))

                    self.makeFrameObject()

                # if first frame - rescale the object
                if not self.bfirst_frame:
                    self.bfirst_frame = True

                    self.rescaleImageToWidget()
                self.debug("Pixmap is created")

    def rescaleImageToWidget(self):
        """
        Performs a rescale operation of the image to the view
        :return:
        """
        scene: QtWidgets.QGraphicsScene = self.scene
        view: QtWidgets.QGraphicsView = self.view

        # widget size
        viewport_rect = view.rect()
        viewport_rect = view.mapToScene(viewport_rect).boundingRect()
        view_w, view_h = viewport_rect.width(), viewport_rect.height()

        scene_rect = scene.sceneRect()
        point1 = QtCore.QPointF(scene_rect.x(), scene_rect.y())
        point2 = QtCore.QPointF(scene_rect.x() + scene_rect.width(), scene_rect.y() + scene_rect.height())

        pxmap_rect = self.pxmap.boundingRect()
        px_w, px_h = pxmap_rect.width()*self.image_scale, pxmap_rect.height()*self.image_scale

        v2px_w, v2px_h = px_w/view_w, px_h/view_h

        #self.debug("Pixmap size {}:{}\nViewport {}:{}\nRatio {}:{}".format(
        #    px_w, px_h,
        #    view_w, view_h,
        #    v2px_w, v2px_h
        #))
        if v2px_h == 0:
            v2px_h = 1.
        if v2px_w == 0:
            v2px_w = 1.

        # height is higher
        if v2px_h >= v2px_w:
            self.image_scale = self.image_scale/v2px_h * self.DEFAULT_FITVALUE
        else:
            self.image_scale = self.image_scale / v2px_w * self.DEFAULT_FITVALUE

        transform = QtGui.QTransform.fromScale(self.image_scale, self.image_scale)
        self.pxmap.setTransform(transform)

        self.reCenterView()
        self.makeFrameObject()

    def registerCameraFeatures(self):
        """
        Registers a signal with camera features update
        :return:
        """
        self.signcamerafeatures.connect(self.processCameraFeatures)

    def reportCameraFeatures(self, obj):
        """
        Sets camera features dictionary update
        :param obj:
        :return:
        """
        self.signcamerafeatures.emit(copy.deepcopy(obj))

    def processCameraFeatures(self, obj: dict):
        """
        Processes an update on the most critical camera features
        :return:
        """
        self.debug("Feature update information {}".format(obj))

        # making a copy of the values from the information retrieved from the camera
        (exposure, expmin, expmax, gain, gainmin, gainmax, frequency, width, height, ip, model, interface, bcapture) = (
                                       self.getDefaultCameraFeature(obj, CAMERA_EXPOSUREMERGED),
                                       self.getDefaultCameraFeature(obj, CAMERA_EXPOSUREMIN),
                                       self.getDefaultCameraFeature(obj, CAMERA_EXPOSUREMAX),
                                       self.getDefaultCameraFeature(obj, CAMERA_GAINMERGED),
                                       self.getDefaultCameraFeature(obj, CAMERA_GAINMIN),
                                       self.getDefaultCameraFeature(obj, CAMERA_GAINMAX),
                                       self.getDefaultCameraFeature(obj, CAMERA_FREQUENCY),
                                       self.getDefaultCameraFeature(obj, CAMERA_WIDTH),
                                       self.getDefaultCameraFeature(obj, CAMERA_HEIGHT),
                                       self.getDefaultCameraFeature(obj, CAMERA_IP),
                                       self.getDefaultCameraFeature(obj, CAMERA_MODEL),
                                       self.getDefaultCameraFeature(obj, CAMERA_INTERFACE),
                                       self.getDefaultCameraFeature(obj, CAMERA_CAPTURE_ALLOWED),
                                       )

        # nick name of the camera
        nickname = self.config.getcfCameraNickName()

        # setting window title
        block_frequency = ""
        if isinstance(frequency, float):
            block_frequency = "{:.02f} Hz".format(frequency)

        # info on gain
        block_gain = ""
        if isinstance(gain, float) or isinstance(gain, int):
            block_gain = "{}".format(int(gain))

        # info on exposure
        block_exposure = ""
        if isinstance(exposure, float):
            block_exposure = "{:.02f} ms".format(self.exposureFromDevice(exposure))

        # merging gain + exposure info
        if len(block_gain) > 0 or len(block_exposure) > 0:
            block_exposure = "Exp./Gain: {} / {}".format(block_exposure, block_gain)
            self.info("!!! {}".format(block_exposure))

        # camera info
        t = [self.id]
        if isinstance(model, str) and len(model)>0:
            t.append(model)
        if isinstance(ip, str) and len(ip) > 0:
            t.append(ip)
        block_camera = ", ".join([v for v in (model, self.id, ip) if isinstance(v, str) and len(v) > 0])

        # preparing and setting the title if necessary
        title = "; ".join([v for v in (nickname, block_camera, block_exposure, block_frequency) if isinstance(v, str) and len(v) > 0])
        trefzmq = "; ".join(
            [v for v in (nickname, block_camera, block_exposure) if isinstance(v, str) and len(v) > 0])

        # title is updated together with frequency
        if self.config.getWindowTitle().lower() != title.lower():
            self.config.setWindowTitle(title)
            self.parent().setWindowTitle(title)

        # zmq data is updated only if major values are changed
        if self.zmqupdate_test != trefzmq:
            self.zmqupdate_test = trefzmq
            self.setZMQdata()

    def getCameraData(self):
        """
        Returns camera values
        :return:
        """
        res = None
        with self.cam_values_lock:
            res = copy.deepcopy(self.cam_values)
        return res

    def setZMQdata(self):
        """
        Creates a copy of the camera data and copies it to the zmq thread
        :return:
        """
        tdata = self.getCameraData()
        self.zmqserver.setData(tdata)

    def exposureFromDevice(self, v):
        """
        Converts exposure from device units to local
        :param v:
        :return:
        """
        if v is None:
            v = 0.
        return v/self.EXPOSURE_CONVERSION

    def exposureToDevice(self, v):
        """
        Converts exposure from local units to device
        :param v:
        :return:
        """
        return v

    def getDefaultCameraFeature(self, obj: dict, key):
        """
        Returns a default value or a value from a feature dict
        :param obj:
        :return:
        """
        res = None
        with self.cam_values_lock:
            res = self.cam_values[key]
            try:
                res = obj[key]
                self.cam_values[key] = res
            except KeyError:
                pass
        return res

    def processZoomIn(self):
        """
        Processes zoom in event
        :return:
        """
        view = self.view
        sc = self.SCALE_UPFACTOR

        self.image_scale = self.image_scale * sc
        transform = QtGui.QTransform.fromScale(self.image_scale, self.image_scale)
        self.pxmap.setTransform(transform)

        self.reCenterView()
        self.makeFrameObject()

    def processZoomOut(self):
        """
        Processes zoom in event
        :return:
        """
        view = self.view
        scene = self.scene

        brect: QtCore.QRectF = view.mapFromScene(scene.sceneRect()).boundingRect()
        bw, bh = brect.width(), brect.height()
        if bw < self.MIN_SIZE or bh < self.MIN_SIZE:
            return

        sc = self.SCALE_DOWNFACTOR

        self.image_scale = self.image_scale * sc
        transform = QtGui.QTransform.fromScale(self.image_scale,self.image_scale)
        self.pxmap.setTransform(transform)

        self.reCenterView()
        self.makeFrameObject()

    def reCenterView(self):
        """
        Recenters view, in order to cope with scrollbars
        :return:
        """
        view = self.view

        vs = view.size()
        th, tw = vs.height(), vs.width()
        tr = QtCore.QRect(int(-tw / 2), int(-th / 2), tw, th)
        rect2scene = view.mapToScene(tr)

        tbr = rect2scene.boundingRect()
        tbr_x1, tbr_y1, tbr_w, tbr_h = tbr.x(), tbr.y(), tbr.width(), tbr.height()

        nr = QtCore.QRectF(-tbr_w / 2, -tbr_h / 2, tbr_w, tbr_h)

        view.setSceneRect(nr)

    def processZoomFrame(self):
        """
        Rescales the frame to fit the view
        :return:
        """
        self.rescaleImageToWidget()

    def rescaleFramePen(self):
        """
        Rescales pen
        :param scale:
        :return:
        """
        view: QtWidgets.QGraphicsView = self.view
        scene: QtWidgets.QGraphicsScene = self.scene

        # bounding rect in global coords
        brect: QtCore.QRectF = view.mapFromScene(scene.sceneRect()).boundingRect()
        bw, bh = brect.width(), brect.height()

        # linewidth in scene coordinates
        lwrect = view.mapToScene(QtCore.QRect(0, 0, 3, 3))
        lwrect = lwrect.boundingRect()

        # scene rect
        screct: QtCore.QRectF = scene.sceneRect()
        scw, sch = screct.width(), screct.height()

        color: QtGui.QColor = self.PENCOLOR_FRAME
        color.setAlpha(self.PENCOLOR_ALPHA)

        pen = QtGui.QPen(color)
        neww = float(scw) / float(bw) * float(self.PENWIDTH_FRAME)

        if neww < 1:
            neww = 2

        pen.setWidth(neww)

        for el in self.framerectgroup.childItems():
            el.setPen(pen)

    def processShowHideFrame(self, bstate: bool):
        """
        Sets the state of the frame/central cross visibility
        :param bstate:
        :return:
        """
        if bstate:
            self.framerectgroup.show()
        else:
            self.framerectgroup.hide()

    def processShowHideMarker(self, bstate: bool):
        """
        Sets the state of the frame/central cross visibility
        :param bstate:
        :return:
        """
        if bstate:
            self.marker.show()
        else:
            self.marker.hide()

    def processPlayStop(self, bstate: bool):
        """
        Starts the process of camera acquisition
        :param bstate:
        :return:
        """
        self.debug("Starting camera aquisition")
        if bstate:
            # stop the test thread
            if self.thread_poll is not None and self.thread_poll.is_alive():
                self.qstop_poll.put(self.QUEUE_STOP_MSG)
                self.thread_poll.join()

            # start aquisition
            self.makeCameraFrame()
        else:
            # stop aquisition
            if self.thread is not None and self.thread.is_alive():
                self.qstop.put(self.QUEUE_STOP_MSG)
                self.thread.join()

            # start process thread
            self.startCameraPolling()

    def reportStopAcq(self, msg=None):
        """
        Reports end of acquisition
        :return:
        """
        self.signstopacq.emit()
        if msg is not None:
            self.reportStatusMessage("Stopping acquisition: {}".format(msg))

    def registerStopAcq(self, func):
        """
        Registers an external callback for an acquisition stop
        :param func:
        :return:
        """
        self.signstopacq.connect(func)

    def registerStatusMessage(self, func):
        """
        Registers a callback for a signal showing status bar message of the main window
        :param func:
        :return:
        """
        self.signstatusmsg.connect(func)

    def reportStatusMessage(self, msg):
        """
        Reports a message to the main window statusbar
        :return:
        """
        self.signstatusmsg.emit(msg)

    def registerGainChange(self, v):
        """
        Registers a change of gain and passes it further
        :param v:
        :return:
        """
        cmd = {CAMERA_GAIN: v}
        self.debug("Setting new command ({})".format(cmd))
        self.queue_cmd.put(cmd)

    def registerExposureChange(self, v):
        """
        Registers a change of exposure and passes it further
        :param v:
        :return:
        """
        cmd = {CAMERA_EXPOSUREMERGED: v}
        self.debug("Setting new command ({})".format(cmd))
        self.queue_cmd.put(cmd)

    def registerCameraState(self, func):
        """
        Register external functions polling camera state
        :param func:
        :return:
        """
        self.signcamerastate.connect(func)

    def reportStateCamera(self, bstate):
        """
        Reports a change of camera state
        :param bstate:
        :return:
        """
        self.debug("Camera state is set to {}".format(bstate))
        self.signcamerastate.emit(bstate)

        if not bstate:
            self.startCameraPolling()

    def showGainExposureMenu(self, pos):
        """
        Starts the menu implementing gain/exposure controls
        :return:
        """
        self.debug("Probing a start of the exposure menu")

        if self.thread is None or not self.thread.is_camalive():
            self.reportStatusMessage("Please start the camera acquisition in order to change parameters")
            return
        else:
            try:
                menu = QtWidgets.QMenu(parent=self.parent())
                tgain = self.getRecordedGain()
                texposure = self.getRecordedExposure()

                self.debug("Recorded Exposure ({}); Gain ({});".format(texposure, tgain))

                if tgain is None:
                    tgain = 0
                if texposure is None:
                    texposure = 1000

                a = QtWidgets.QWidgetAction(menu)
                self.debug("Creating menu ({})".format(self.cam_values))
                w = WidgetGainExposure(self.getCameraData(), ctrl=self, parent=menu)
                w.setMinimumSize(580, 90)

                a.setDefaultWidget(w)
                menu.addAction(a)
                menu.exec_(pos)

            except AttributeError as e:
                msg = "Error: {}".format(e)
                self.error(msg)
                self.reportStatusMessage(msg)
                return


    def getZMQError(self):
        """
        Returns a boolean flag indicating an error state of the zmqserver
        :return:
        """
        res = None
        if self.zmqserver is not None:
            try:
                res = self.zmqserver.getError()
            except AttributeError:
                pass
        return res

    def processSaveFile(self):
        """
        Starts picture saving from camera
        :return:
        """
        dn = self.config.getcfCameraDirectory()
        self.debug("Testing directory for file saving is ({})".format(dn))

        if not isinstance(dn, str) or not os.path.isdir(dn):
            dn = self.config.getFolderStartup()
            self.config.setcfCameraDirname(dn)

        self.debug("Base directory for file saving is ({})".format(dn))

        timg = None
        with self.image_lock:
            if isinstance(self.image, QtGui.QImage):
                timg = self.image.copy(self.image.rect())

        if isinstance(timg, QtGui.QImage):
            tfn = QtWidgets.QFileDialog.getSaveFileName(self.parent(), "Saving Camera Image", dn, "Images (*.png)")

            self.debug("Saving file under ({})".format(tfn))
            if isinstance(tfn, tuple) and len(tfn[0]) > 0:
                tfn = tfn[0]
                tbasedir = os.path.dirname(tfn)
                self.config.setcfCameraDirname(tbasedir)

                self.debug("Starting file saving runner thread")
                runner = FilesavingRunner(tfn, timg, feedback=self)
                self.thpool.start(runner)

                self.reportStatusMessage("Saving file as ({})".format(tfn))
            else:
                self.reportStatusMessage("File saving canceled")
        else:
            self.reportStatusMessage("Error: no image to save")

    def processReference(self, v):
        """
        Sets a reference to a value
        """
        self.frame_marker_reference = v

    def processMarkerReference(self):
        """
        Sets the calculation reference to marker
        """
        k = MARKER_REFERENCE
        self.debug("Plugin reference is {}".format(k))
        self.processReference(k)

    def processFrameReference(self):
        """
        Sets the calculation reference to frame
        """
        k = FRAME_REFERENCE
        self.debug("Plugin reference is {}".format(k))
        self.processReference(k)

    def processPluginIndex(self, v):
        """
        Sets the plugin index to a value
        """
        self.info("Plugin index is {}".format(v))
        self.plugin_index = v

    def processViewCtrlEvent(self, v: bool):
        """
        Keeps track of CTRL key pressed - used for click events handling inside the viewport
        """
        self.debug("Ctrl state ({})".format(v))
        self.bviewctrl = v

    def processShowMarkerMenu(self):
        """
        Processes the show marker menu
        """
        self.debug("Pressed show marker")
        ev = QtGui.QCursor.pos()
        self.processMarkerMenu([ev, None])

    def processPluginMove(self, ev: QtWidgets.QGraphicsSceneMouseEvent):
        """
        Calculates a move with respect to the field of view
        """
        if self.plugin_index is not None and self.frame_marker_reference is not None:
            self.info(ev.scenePos())

            # understand the offset
            dx, dy = None, None

            # need to recalculate to frame rectangle size
            self.info("Bounding rect {}; pixmap {};".format(self.framerect.boundingRect(), self.pxmap.boundingRect()))

            if self.frame_marker_reference == FRAME_REFERENCE:
                dx, dy = ev.scenePos().x(), ev.scenePos().y()
            elif self.frame_marker_reference == MARKER_REFERENCE:
                dx, dy = ev.scenePos().x(), ev.scenePos().y()
                dx = dx - self.marker.x
                dy = dy - self.marker.y

            # do useful work if parameters are correct
            if not None in (dx, dy):
                self.debug("Preexecuting with dx {}, dy {}".format(dx, dy))

                dx = dx / self.framerect.boundingRect().width() * self.pxmap.boundingRect().width()
                dy = dy / self.framerect.boundingRect().height() * self.pxmap.boundingRect().height()

                self.debug("Executing with dx {}, dy {}".format(dx, dy))

                plugin = self.config.getPlugins()[self.plugin_index]
                self.debug("Executing a plugin ({}) with dx {}, dy {}".format(plugin, dx, dy))
                try:
                    r = PluginExecutorRunnable(plugin.move_xy, dx, dy)
                    self.thpool.start(r)
                except (AttributeError, KeyError) as e:
                    self.error("Error during plugin start ({}:{})".format(plugin, e))
        else:
            self.reportStatusMessage("Sorry, no plugin installed")
