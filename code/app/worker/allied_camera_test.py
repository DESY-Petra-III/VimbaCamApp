from app.common.imports import *
from app.common.keys import *

from vimba import Vimba, Camera, Frame, FrameStatus, VimbaCameraError, VimbaTimeout, VimbaFeatureError, intersect_pixel_formats, OPENCV_PIXEL_FORMATS, COLOR_PIXEL_FORMATS, MONO_PIXEL_FORMATS, feature, AccessMode

__all__ = ["ThreadCameraAlliedTest", "Frame"]

class ThreadCameraAlliedTest(threading.Thread, Tester):

    CAMERA_MAX = 10000000  # in us
    CAMERA_MIN = 21  # in us

    ACCESS_MODE_FULL = 1
    ACCESS_MODE_READ = 2
    ACCESS_MODE_CONFIG = 4

    def __init__(self, id: str, obj_feedback: QtCore.QObject, queue_stop: queue.Queue,
                 sleep_delay=0.5):
        """
        Class constructor of a class polling a camera and producing values for necessary parameters
        :param id: str() - camera ID
        :param obj_feedback: QObject() - controller recieving updates
        :param queue_stop: queue.Queue() - queue to stop working thread
        :param sleep_delay: float() - delay to sleep inbetween tests for the message to stop the proccess
        """
        threading.Thread.__init__(self)
        Tester.__init__(self, def_file="{}-{}".format(self.__class__.__name__, threading.current_thread().name))

        self.debug("Starting thread {}".format(id))

        self.camid = id

        self.feedback = obj_feedback
        self.qstop = queue_stop

        self.sleep_delay = sleep_delay

        # dictionary with values saved on an update
        self.cam_exposure_feature = None

        # camera state
        self.camera_state = None

        self.camdict = {
            CAMERA_EXPOSUREMERGED: None,
            CAMERA_GAIN: None,
            CAMERA_GAIN_MODE: None,
            CAMERA_EXPOSURE_MODE: None,
            CAMERA_GAINMAX: None,
            CAMERA_GAINMIN: None,
            CAMERA_MODEL: None,
            CAMERA_IP: None,
            CAMERA_INTERFACE: None,
        }

        self.exposure = None
        self.gain = None

    def get_camera(self, v, camera_id) -> None:
        """
        Returns a camera instance
        :param camera_id:
        :return:
        """
        res = None
        if camera_id:
            try:
                res = v.get_camera_by_id(camera_id)
                res.set_access_mode(AccessMode.Read)
                return res

            except VimbaCameraError:
                tmsg = 'Failed to access Camera \'{}\'. Abort.'.format(camera_id)
                self.handle_error(tmsg)
                return res

        else:
            cams = v.get_all_cameras()
            if not cams:
                tmsg = 'No Cameras accessible. Abort.'
                self.handle_error(tmsg)

            return res

    def handle_error(self, msg):
        """
        Passes an error message to the feedback object - error means camera does not work
        :param msg:
        :return:
        """
        self.error(msg)

    def get_feature_info(self, v, cam: Camera):
        """
        Receives and reports information on gain, exposure and etc at a certain delay
        :return:
        """
        feature_list = (CAMERA_EXPOSUREABS, CAMERA_EXPOSURE_MODE,
                        CAMERA_GAIN, CAMERA_GAIN_MODE,
                        CAMERA_GAINMAX, CAMERA_GAINMIN,
                        CAMERA_EXPOSURE,
                        CAMERA_WIDTH, CAMERA_HEIGHT)

        modes = cam.get_permitted_access_modes()
        bcapture = False
        if self.ACCESS_MODE_FULL in modes:
            bcapture = True

        ip = ""
        try:
            ip = cam.get_feature_by_name(CAMERA_CURRENTIP)
            if isinstance(ip.get(), int):
                ip = ipaddress.IPv4Address(ip.get()).reverse_pointer.replace(".in-addr.arpa", "")
        except VimbaFeatureError:
            pass

        features = {CAMERA_EXPOSUREMAX: self.CAMERA_MAX, CAMERA_EXPOSUREMIN: self.CAMERA_MIN,
                    CAMERA_MODEL: cam.get_model(), CAMERA_INTERFACE: cam.get_interface_id(), CAMERA_IP: ip,
                    CAMERA_CAPTURE_ALLOWED: bcapture}

        for f in feature_list:
            try:
                tf = cam.get_feature_by_name(f)
            except VimbaFeatureError:
                self.error("Feature {} is not available".format(f))
                continue

            value = None
            try:
                value = tf.get()
                self.debug("Feature {} value {} type {}".format(tf.get_name(), value, type(value)))

                if isinstance(value, feature.EnumEntry):
                    value = str(value)
            except (AttributeError, VimbaFeatureError):
                pass

            if f == CAMERA_EXPOSURE or f == CAMERA_EXPOSUREABS:
                f = CAMERA_EXPOSUREMERGED
                features.setdefault(f, value)
                self.exposure = value

                # save the name of the camera exposure header
                if self._test_cam_exposure_feature():
                    self.cam_exposure_feature = f
            else:
                if f == CAMERA_GAIN:
                    self.gain = value
                features.setdefault(f, value)

        try:
            self.feedback.processCameraFeatures(copy.deepcopy(features))
        except AttributeError:
            pass

    def _test_cam_exposure_feature(self):
        res = False
        if self.cam_exposure_feature is not None:
            res = True
        return res

    def run(self):
        """
        Processes useful work load
        :return:
        """
        with Vimba.get_instance() as v:
            while True:
                ts = time.time()
                try:
                    # test to stop - only when application finishes
                    try:
                        self.qstop.get(block=False)
                        self.qstop.task_done()
                        return
                    except queue.Empty:
                        pass

                    # polling camera's info
                    with self.get_camera(v, self.camid) as cam:
                        if cam is None:
                            # handle an issue of camera accessibility
                            self.handle_error("Camera is not available")
                            raise ValueError

                        self.debug("Camera {} exists".format(self.camid))

                        # start data collection in async way
                        try:
                            self.get_feature_info(v, cam)
                            self.reportCameraState(True)
                        except VimbaCameraError as e:
                            # disconnection issue
                            msg = "Camera error: {}".format(e)
                            self.handle_error(msg)
                            raise ValueError

                    # test to quit
                    try:
                        self.qstop.get(block=False)
                        self.qstop.task_done()
                        return
                    except queue.Empty:
                        pass

                except (AttributeError, ValueError):
                    # handle an issue of camera accessibility
                    self.handle_error("Camera is not available")
                    # report absence of camera
                    self.reportCameraState(False)

                dt = time.time() - ts
                dtsd = self.sleep_delay - dt

                self.debug("Cycle was processed within ({:0.3f} s), sleeping for ({:0.3f})".format(dt, dtsd))

                if dtsd > 0:
                    time.sleep(dtsd)

    def reportCameraState(self, bstate):
        """
        Function responsible for reporting camera's state
        :param bstate:
        :return:
        """
        try:
            if bstate != self.camera_state:
                self.camera_state = bstate
                self.feedback.reportStateCamera(bstate)
        except AttributeError:
            pass

# typical value from a GiGEcamera
"""
var = {'ExposureMax': 10000000, 'ExposureMin': 21, 'CAMERA_MODEL': 'Manta_G-046C (E0020005)',
       'CAMERA_INTERFACE': 'enp1s0', 'CAMERA_IP': '131.169.45.161', 'CAMERA_CAPTURE_ALLOWED': True,
       'Exposure': 141491.0, 'ExposureAuto': 'Off', 'Gain': 21.0, 'GainAuto': 'Off', 'GainAutoMax': 31.0,
       'GainAutoMin': 0.0, 'SensorWidth': 780, 'SensorHeight': 580}
"""