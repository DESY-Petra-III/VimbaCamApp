from app.common.imports import *
from app.common.keys import *

import gc

from vimba import Vimba, Camera, Frame, FrameStatus, VimbaCameraError, VimbaTimeout, VimbaFeatureError, intersect_pixel_formats, OPENCV_PIXEL_FORMATS, COLOR_PIXEL_FORMATS, MONO_PIXEL_FORMATS, feature, AccessMode, PixelFormat

__all__ = ["ThreadCameraAllied", "Frame"]

def frame_handler(cam: Camera, frame: Frame):
    """
    Callback function handles frames and passes them into the feedback object if necessary
    :return:
    """
    print("Camera {}; Frame {}".format(cam.get_id(), frame))

    cam.queue_frame(frame)

class ThreadCameraAllied(threading.Thread, Tester):

    QUEUE_STOP_MSG = QUEUE_STOP_MSG

    WAIT_STEPS = 5

    SYNC_FRAMERATE = 10     # SYNC_SLEEP/SYNC_FRAMERATE - max delay
    SYNC_SLEEP = 1.         # seconds
    SYNC_FRAMETIMEOUT = 2.  # seconds

    CAMERA_FEATURE_UPDATE = 1. # delay between reported camera feature updates

    CAMERA_MAX = 10000000 # in ms
    CAMERA_MIN = 21  # in ms

    def __init__(self, id: str, obj_feedback: QtCore.QObject, queue_stop: queue.Queue,
                 frame_count=-1, sleep_delay=0.5,
                 basync=False, queue_cmd=None):
        """
        Class constructor
        :param id: str() - camera ID
        :param obj_feedback: QObject() - controller
        :param queue_stop: queue.Queue() - queue to stop working thread
        :param frame_count: int() - maximum frame count, <=0 - infinity, >=0 - maximal
        :param sleep_delay: float() - delay to sleep inbetween tests for the message to stop the proccess
        :param sleep_delay: float() - delay to sleep inbetween tests for the message to stop the proccess
        :param queue_cmd: queue.Queue () - queue to pass commands - changing acquisition, gain, etc.
        """
        threading.Thread.__init__(self)
        Tester.__init__(self, def_file="{}-{}".format(self.__class__.__name__, threading.current_thread().name))

        self.debug("Starting thread {}".format(id))

        self.camid = id

        self.qlocalstop = queue.Queue()

        self.feedback = obj_feedback
        self.qstop = queue_stop

        self.sleep_delay = sleep_delay

        self.frame_count = frame_count
        self.count = 0

        # queue for commands
        self.qcommands = queue_cmd

        # flag controls type of data collection True: asynchronous; False: synchronous
        self.basync = basync

        # camera exposure feature name
        self.cam_exposure_feature = None
        self.cam_gain_feature = None

        # frame rate
        self.frame_rate_real = 0.

        # feature update time
        self.ts_features = 0

        # dictionary with saved commands
        self.cmddict = {
            CAMERA_EXPOSUREMERGED: None,
            CAMERA_GAIN: None,
            CAMERA_GAIN_MODE: None,
            CAMERA_EXPOSURE_MODE: None
        }

        self.cam_alive = False
        self.cam_alive_lock = threading.Lock()

        self.exposure = None
        self.gain = None

        self.camera_state = True

        self.pixel_format = None

    def is_camalive(self):
        """
        Returns an indicator if the camera is alive or not
        :return:
        """
        res = None
        with self.cam_alive_lock:
            res = self.cam_alive
        return res

    def _test_queue_commands(self):
        res = False
        if isinstance(self.qcommands, queue.Queue):
            res = True
        return res

    def _test_cam_exposure_feature(self):
        res = False
        if self.cam_exposure_feature is not None:
            res = True
        return res

    def _test_cam_gain_feature(self):
        res = False
        if self.cam_gain_feature is not None:
            res = True
        return res

    def apply_default_params(self):
        if isinstance(self.qcommands, queue.Queue):
            self.qcommands.put({CAMERA_GAIN_MODE: 'Off'})
            self.qcommands.put({CAMERA_EXPOSURE_MODE: 'Off'})

    def get_camera(self, camera_id) -> None:
        """
        Returns a camera instance
        :param camera_id:
        :return:
        """
        res = None

        with Vimba.get_instance() as vimba:
            if camera_id:
                try:
                    res = vimba.get_camera_by_id(camera_id)
                    res.set_access_mode(AccessMode.Full)
                    return vimba.get_camera_by_id(camera_id)

                except VimbaCameraError:
                    tmsg = 'Failed to access Camera \'{}\'. Abort.'.format(camera_id)
                    self.handle_error(tmsg)
                    return res

            else:
                cams = vimba.get_all_cameras()
                if not cams:
                    tmsg = 'No Cameras accessible. Abort.'
                    self.handle_error(tmsg)

                return res

    @profile
    def setup_camera(self, cam: Camera):
        res = True

        with cam:
            # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
            try:
                cam.GVSPAdjustPacketSize.run()

                while not cam.GVSPAdjustPacketSize.is_done():
                    pass

            except (AttributeError, VimbaFeatureError):
                pass
            finally:
                # Query available, open_cv compatible pixel formats
                # prefer color formats over monochrome formats
                cam_fmts = cam.get_pixel_formats()


                cv_fmts = intersect_pixel_formats(cam_fmts, OPENCV_PIXEL_FORMATS)
                self.debug("Camera pixel formats: ({})".format(cam_fmts))

                color_fmts = intersect_pixel_formats(cv_fmts, COLOR_PIXEL_FORMATS)

                if color_fmts:
                    self.debug("Found color pixel formats")
                    cam.set_pixel_format(color_fmts[0])
                    self.pixel_format = color_fmts[0]
                else:
                    # either there is a monochrome format, or there is a possibility for PixelFormat.BayerRG8, which can be converted

                    if PixelFormat.BayerRG8 in cam_fmts:
                        self.debug("Found PixelFormat.BayerRG8 pixel formats")
                        self.pixel_format = PixelFormat.BayerRG8
                    else:
                        mono_fmts = intersect_pixel_formats(cv_fmts, MONO_PIXEL_FORMATS)

                        if mono_fmts:
                            self.debug("Found monocolor pixel formats")
                            cam.set_pixel_format(mono_fmts[0])
                            self.pixel_format = mono_fmts[0]
                        else:
                            res = False
                            self.handle_error('Camera does not support a OpenCV compatible format natively. Abort.')
        return res

    def run(self):
        """
        Main loop of the thread working asynchronously
        :return:
        """
        with Vimba.get_instance():
            try:
                with self.get_camera(self.camid) as cam:

                    self.cam_alive = True

                    if cam is None:
                        # handle an issue of camera accessibility
                        self.handle_error("Camera is not available 01")
                        return

                    if not self.setup_camera(cam):
                        self.handle_error("Camera does not support known pixel formats")
                        return

                    self.debug("Camera {} exists".format(self.camid))

                    # start data collection in async way
                    try:
                        if self.basync:
                            self.work_async(cam)
                        else:
                            self.work_sync(cam)
                    except VimbaCameraError as e:
                        # disconnection issue
                        msg = "Camera error: {}".format(e)
                        self.handle_error(msg)

            except AttributeError as e:
                # handle an issue of camera accessibility
                self.handle_error("Camera is not available 02: {}".format(e))
                return
            except VimbaCameraError:
                self.handle_error("Issue with reading the camera. Is VimbaViewer is running?")

    def handle_error(self, msg):
        """
        Passes an error message to the feedback object - error means camera does not work
        :param msg:
        :return:
        """
        self.error(msg)
        if self.feedback is not None:
            try:
                self.feedback.reportStopAcq(msg=msg)
            except AttributeError as e:
                self.debug("Error while handling error: {}".format(e))
        self.setCamAlive(False)

    def setCamAlive(self, v):
        """
        Sets the cam alive state
        :return:
        """
        with self.cam_alive_lock:
            self.cam_alive = v

    def work_sync(self, cam: Camera):
        """
        Sets a work in synchronous way
        :return:
        """
        self.debug("Processing data synchronously")
        max_delay = float(self.SYNC_SLEEP)/float(self.SYNC_FRAMERATE)

        told_feature_request = 0

        while True:
            tstart = time.time()

            # make a test
            self.setCamAlive(True)

            try:
                self.qstop.get(block=False)
                self.qstop.task_done()
                return
            except queue.Empty:
                pass

            # updates information on features
            try:

                # pass commands if necessary before reading out
                if self._test_queue_commands() or self.cam_exposure_feature is not None:
                    bempty = False
                    bdata = False
                    self.debug("Applying external commands")
                    # collect all changes in one go - overwrite the oldest ones
                    while not bempty:
                        try:
                            cmd = self.qcommands.get(block=False)
                            # parse commands
                            if isinstance(cmd, dict) and len(cmd.keys()) > 0:
                                for (k, v) in cmd.items():
                                    if k in self.cmddict.keys():
                                        self.cmddict[k] = v
                                        bdata = True

                            self.qcommands.task_done()
                        except queue.Empty:
                            bempty = True

                    # apply values

                    if bdata:
                        self.debug("Applying external commands ({}, {}, {})".format(self.cmddict, self.cam_exposure_feature, CAMERA_EXPOSUREMERGED))

                        for k in self.cmddict.keys():
                            v = self.cmddict[k]

                            if v is not None:
                                if k == CAMERA_EXPOSUREMERGED and self._test_cam_exposure_feature():
                                    if self.cam_exposure_feature == CAMERA_EXPOSUREABS:
                                        self.debug("Setting ({} -> {})".format(k, v))
                                        cam.ExposureTimeAbs.set(v)
                                    elif self.cam_exposure_feature == CAMERA_EXPOSURE:
                                        self.debug("Setting ({} -> {})".format(k, v))
                                        cam.ExposureTime.set(v)
                                elif k == CAMERA_GAINMERGED and self._test_cam_gain_feature():
                                    if self.cam_gain_feature == CAMERA_GAIN_RAW:
                                        self.debug("Setting ({} -> {})".format(k, v))
                                        cam.GainRaw.set(v)
                                    elif self.cam_gain_feature == CAMERA_GAIN:
                                        self.debug("Setting ({} -> {})".format(k, v))
                                        cam.Gain.set(v)
                                elif k == CAMERA_GAIN_MODE:
                                    self.debug("Setting ({} -> {})".format(k, v))
                                    cam.GainAuto.set(v)
                                elif k == CAMERA_EXPOSURE_MODE:
                                    self.debug("Setting ({} -> {})".format(k, v))
                                    cam.ExposureAuto.set(v)

                                self.cmddict[k] = None

                # retrieve features
                tgetfeature = time.time()
                self.get_feature_info(cam)
                tgetfeature = time.time() - tgetfeature

                # retrieve frame
                tgetframe = time.time()
                for frame in cam.get_frame_generator(limit=1, timeout_ms=int(self.SYNC_FRAMETIMEOUT*1000)):
                    try:
                        self.debug("Obtained frame {}".format(frame))
                        if frame.get_status() == FrameStatus.Complete:
                            img = None

                            if self.pixel_format == PixelFormat.BayerRG8:
                                img = frame.as_numpy_ndarray()
                                img = cv2.cvtColor(img, cv2.COLOR_BayerBG2RGB)
                            else:
                                img = frame.as_opencv_image()
                            self.feedback.reportNewFrame(img)
                            pass
                    except (RuntimeError, AttributeError):
                        pass
                # collect garbage - frames are large
                gc.collect()

                tgetframe = time.time()-tgetframe

                self.debug("Get features ({}s); Get Frame ({}s)".format(tgetfeature, tgetframe))
            except (VimbaTimeout, VimbaFeatureError) as e:
                msg = "Vimba Timeout message {}".format(e)
                self.error(msg)
                self.handle_error(msg)
                continue

            tstop = time.time()

            td = (tstop - tstart)

            self.frame_rate_real = float(1.) / float(td)
            self.debug("Frame rate is ({:2.2f} Hz)".format(self.frame_rate_real))

            if self.frame_count > 0:
                self.count += 1

                if self.count >= self.frame_count:
                    return

            if td > max_delay:
                self.debug("Real delay ({} s) is larger than the maximum delay ({} s)".format(td, max_delay))
                continue

            # sleep only if necessary
            if max_delay-td > 0:
                time.sleep(max_delay-td)

    def work_async(self, cam: Camera):
        """
        Sets an asyncronous data collection
        :param cam:
        :return:
        """

        self.debug("Processing data asynchronously")

        try:
            # Start Streaming with a custom a buffer of 10 Frames (defaults to 5)
            self.debug("Starting streaming")
            cam.start_streaming(handler=self.frame_handler, buffer_count=5)

            delay = float(self.sleep_delay) / float(self.WAIT_STEPS)
            while True:
                # updates information on features
                self.get_feature_info(cam)

                for i in range(self.WAIT_STEPS):
                    try:
                        self.qstop.get(block=False)
                        self.qstop.task_done()

                        self.debug("Exiting loop due to a global event")
                        raise ValueError
                    except queue.Empty:
                        pass

                    try:
                        self.qlocalstop.get(block=False)
                        self.qlocalstop.task_done()

                        self.debug("Exiting loop due to a local event")
                        raise ValueError
                    except queue.Empty:
                        pass

                    time.sleep(delay)

                self.debug("Tick-tack")

        except ValueError:
            self.debug("Value error")
        finally:
            self.debug("Stop streaming")

            try:
                cam.stop_streaming()
            except VimbaCameraError as e:
                self.error("Issue with a camera?\n{}".format(e))

    def get_feature_info(self, cam: Camera):
        """
        Receives and reports information on gain, exposure and etc at a certain delay
        :return:
        """
        if time.time()-self.ts_features > self.CAMERA_FEATURE_UPDATE:
            feature_list = (CAMERA_EXPOSUREABS, CAMERA_EXPOSURE_MODE,
                            CAMERA_GAIN, CAMERA_GAIN_RAW, CAMERA_GAIN_MODE,
                            CAMERA_GAINMAX, CAMERA_GAINMIN,
                            CAMERA_EXPOSURE,
                            CAMERA_WIDTH, CAMERA_HEIGHT)

            features = {CAMERA_EXPOSUREMAX: self.CAMERA_MAX, CAMERA_EXPOSUREMIN: self.CAMERA_MIN,
                        CAMERA_FREQUENCY: self.frame_rate_real}

            for f in feature_list:
                try:
                    tf = cam.get_feature_by_name(f)
                except VimbaFeatureError:
                    self.debug("Feature {} is not available".format(f))
                    continue

                value = None
                try:
                    value = tf.get()
                    self.debug("Feature {} value {} type {}".format(tf.get_name(), value, type(value)))

                    if isinstance(value, feature.EnumEntry):
                        value = str(value)
                except (AttributeError, VimbaFeatureError):
                    pass

                if value is None:
                    continue

                if f == CAMERA_EXPOSURE or f == CAMERA_EXPOSUREABS:
                    tf = CAMERA_EXPOSUREMERGED
                    features.setdefault(tf, value)
                    self.exposure = value

                    # save the name of the camera exposure header
                    if not self._test_cam_exposure_feature():
                        self.debug("Setting camera exposure feature ({})".format(f))
                        self.cam_exposure_feature = f
                elif f == CAMERA_GAIN or f == CAMERA_GAIN_RAW:
                    tf = CAMERA_GAINMERGED
                    features.setdefault(tf, value)

                    self.gain = value

                    # save the name of the camera gain header
                    if not self._test_cam_gain_feature():
                        self.debug("Setting camera gain feature ({})".format(f))
                        self.cam_gain_feature = f
                else:
                    features.setdefault(f, value)
            try:
                self.feedback.reportCameraFeatures(features)
            except AttributeError:
                pass

    def frame_handler_async(self, cam: Camera, frame: Frame):
        """
        Callbacck function handles frames and passes them into the feedback object if necessary
        :return:
        """
        self.debug("Camera {}; Frame {}".format(cam.get_id(), frame))

        if self.frame_count > 0:
            self.count += 1

            if self.count >= self.frame_count:
                if self.qlocalstop.empty():
                    self.debug("!!! Stop queue")
                    self.qlocalstop.put(self.QUEUE_STOP_MSG)

        if frame.get_status() == FrameStatus.Complete:
            self.debug("Frame with id {} is complete".format(frame.get_id()))

            try:
                self.feedback.registerNewFrame(frame)
            except (RuntimeError, AttributeError):
                pass

        cam.queue_frame(frame)

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