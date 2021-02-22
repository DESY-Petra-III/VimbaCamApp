import os
from app.config.keys import *
from app.common.keys import *

import configparser
import json
from threading import Lock

# storage for internal variables
CONFIG_STORAGE = {
    # Paths
    FOLDER_STARTUP: None,
    FOLDER_LOG: None,
    FOLDER_PLUGINS: None,  # common code for plugins
    FOLDER_PROFILES: None,  # profile is a plugin having its own heavy graphic independent code
    FOLDER_IMAGES: None,
    FOLDER_HTML: None,

    # logo of the file
    LOGO_FILE: None,

    # set of plugins
    MOVEPLUGINS: [],

    # configuration
    SETTINGS: None,  # QSettings
    CAMERA_ID: None,  # Camera ID - used for storing different config files
    FRAME_COLORINDEX: 222,  # Color index of the frame

    # Content
    DATA_IMAGE: None,

    # logging
    LOGGING_MAIN_FILE: "main_log",
    LOGGING_MAIN_FORMAT: '%(asctime)s %(levelname)-8s %(process)-8d %(thread)-10d %(threadName)-16s %(name)-12s: %(message)s',
    LOGGING_MAIN_DATE: '%m-%d %H:%M',

    LOGGING_FILE_FORMAT: '%(asctime)s %(levelname)-8s %(process)-8d %(thread)-10d %(threadName)-16s %(name)-12s: %(message)s',
    LOGGING_FILE_DATE: '%Y-%m-%d %H:%M:%S',

    # Main window
    WINDOW_TITLE: "Window title",
    DIALOG_SELECTOR_TITLE: "Select profile",

    # Profile source - in terms of a plugin (pluginbase) - tuple(PluginBase, PluginSource, Description, Path)
    PROFILE_SOURCE: None,

    # specific camera feature
    CAMERA_PIXELFORMAT: None
}

CONFIG_INSTANCE = None


class Config(object):
    """
    Simple wrapper for configuration
    """
    DEFAULT_SECTION = "camera"
    def __init__(self):
        global CONFIG_INSTANCE

        if CONFIG_INSTANCE is None:
            CONFIG_INSTANCE = self

        self.config = configparser.ConfigParser()
        self.config_lock = Lock()
        self.configfn = None

        self.camera_pixelformat_lock = Lock()

    def setConfigFile(self, id):
        """
        Prepares a configuration file object
        :param id:
        :return:
        """
        tdict = {
            MARKER_SHAPE: "0",
            MARKER_SIZE: "[300.0, 300.0]",
            MARKER_POSITION: "[0.0, 0.0]",
            MARKER_LINEWIDTH: "3",
            MARKER_COLORINDEX: "223",
            FRAME_COLORINDEX: "223",
            MARKER_DISPLAY: "0",
            FRAME_DISPLAY: "1",
            CAMERA_NICKNAME: "Nickname",
            CAMERA_DIRNAME: "None"
        }

        bwrite = False
        try:
            fp = self.getFolderProfiles()
            fn = "{}.ini".format(id)


            if isinstance(fp, str):
                tfn = os.path.join(fp, fn)

                self.configfn = tfn

                self.printHeaderMsg("Using configuration file ({})".format(self.configfn))

                if os.path.exists(tfn):
                    self.config.read(tfn)

                if not self.DEFAULT_SECTION in self.config.sections():
                    self.config.add_section(self.DEFAULT_SECTION)
                    bwrite = True

                # look through the keys - set default if not existing
                for k in tdict.keys():
                    try:
                        tv = self.config[self.DEFAULT_SECTION][k]
                    except KeyError:
                        self.config.set(self.DEFAULT_SECTION, k, str(tdict[k]))
                        bwrite = True

                # write config with default values
                if bwrite:
                    self.write_config()
        except (OSError, IOError) as e:
            pass

    def write_config(self):
        """
        Writes config file
        :return:
        """
        if isinstance(self.configfn, str):
            with open(self.configfn, "w") as fh:
                self.config.write(fh)

    def getcfValue(self, k):
        """
        Returns config value set by a key
        :param k:
        :return:
        """
        res = None
        try:
            v = self.config.get(self.DEFAULT_SECTION, k)
            # print("{}:{}".format(k, v))
            if k == CAMERA_NICKNAME:
                v = '"{}"'.format(v)
            res = json.loads(v)
        except json.JSONDecodeError as e:
            print("Json error while parsing config file ({}:{})".format(k, e))
        return res

    def setcfValue(self, k, v):
        """
        Sets config value by a key
        :param k:
        :return:
        """
        with self.config_lock:
            self.config.set(self.DEFAULT_SECTION, k, json.dumps(v))
            self.write_config()

    def setcfMarkerSize(self, v):
        """
        Sets config value for marker size
        :param k:
        :return:
        """
        print("Size {}".format(v))
        self.setcfValue(MARKER_SIZE, v)

    def setcfMarkerPosition(self, v):
        """
        Sets config value for marker size
        :param k:
        :return:
        """
        print("Position {}".format(v))
        self.setcfValue(MARKER_POSITION, v)

    def setcfMarkerLinewidth(self, v):
        """
        Sets config value for marker linewidth
        :param k:
        :return:
        """
        self.setcfValue(MARKER_LINEWIDTH, v)

    def setcfMarkerColorIndex(self, v):
        """
        Sets config value for marker color index
        :param k:
        :return:
        """
        self.setcfValue(MARKER_COLORINDEX, v)

    def setcfMarkerDisplay(self, v):
        """
        Sets config value for marker display on/off
        :param k:
        :return:
        """
        self.setcfValue(MARKER_DISPLAY, v)

    def setcfMarkerShape(self, v):
        """
        Sets config value for marker display on/off
        :param k:
        :return:
        """
        self.setcfValue(MARKER_SHAPE, v)

    def setcfFrameColorIndex(self, v):
        """
        Sets config value for frame color index
        :param k:
        :return:
        """
        self.setcfValue(FRAME_COLORINDEX, v)

    def setcfFrameDisplay(self, v):
        """
        Sets config value for frame display on/off
        :param k:
        :return:
        """
        self.setcfValue(FRAME_DISPLAY, v)

    def setcfCameraDirname(self, v):
        """
        Sets config value for frame display on/off
        :param k:
        :return:
        """
        self.setcfValue(CAMERA_DIRNAME, v)

    def getcfMarkerShape(self):
        """
        Returns marker shape
        :return:
        """
        return self.getcfValue(MARKER_SHAPE)

    def getcfMarkerSize(self):
        """
        Returns marker position
        :return:
        """
        res = self.getcfValue(MARKER_SIZE)
        return res

    def getcfMarkerPosition(self):
        """
        Returns marker position
        :return:
        """
        res = self.getcfValue(MARKER_POSITION)
        return res

    def getcfMarkerLinewidth(self):
        """
        Returns marker linewidth
        :return:
        """
        return self.getcfValue(MARKER_LINEWIDTH)

    def getcfMarkerColorIndex(self):
        """
        Returns marker color index
        :return:
        """
        return self.getcfValue(MARKER_COLORINDEX)

    def getcfMarkerDisplay(self):
        """
        Returns marker display value - on/off
        :return:
        """
        res = self.getcfValue(MARKER_DISPLAY)
        return res

    def getcfFrameColorIndex(self):
        """
        Returns frame color index
        :return:
        """
        return self.getcfValue(FRAME_COLORINDEX)

    def getcfFrameDisplay(self):
        """
        Returns frame display value - on/off
        :return:
        """
        return self.getcfValue(FRAME_DISPLAY)

    def getcfCameraNickName(self):
        """
        Returns frame display value - on/off
        :return:
        """
        return self.getcfValue(CAMERA_NICKNAME)

    def getcfCameraDirectory(self):
        """
        Returns frame display value - on/off
        :return:
        """
        return self.getcfValue(CAMERA_DIRNAME)

    def setConfiguration(self, key, value):
        global CONFIG_STORAGE

        # print("Setting configuration value ({}:{})".format(key, value))
        CONFIG_STORAGE[key] = value

    def getConfiguration(self, key):
        global CONFIG_STORAGE

        # print("Retrieving configuration value ({}:{})".format(key, CONFIG_STORAGE[key]))
        return CONFIG_STORAGE[key]

    def setFolderStartup(self, v):
        self.setConfiguration(FOLDER_STARTUP, v)

    def setFolderLog(self, v):
        self.setConfiguration(FOLDER_LOG, v)

    def setFolderPlugins(self, v):
        self.setConfiguration(FOLDER_PLUGINS, v)

    def setFolderProfiles(self, v):
        self.setConfiguration(FOLDER_PROFILES, v)

    def setFolderImages(self, v):
        self.setConfiguration(LOGO_FILE, os.path.join(v, "logo.png"))
        self.setConfiguration(FOLDER_IMAGES, v)

    def setFolderHtml(self, v):
        self.setConfiguration(FOLDER_HTML, v)

    def setProfileSource(self, v):
        self.setConfiguration(PROFILE_SOURCE, v)

    def setWindowTitle(self, v):
        self.setConfiguration(WINDOW_TITLE, v)

    def setCameraID(self, v):
        self.setConfiguration(CAMERA_ID, v)

    def setFrameColorIndex(self, v):
        self.setConfiguration(FRAME_COLORINDEX, v)

    def setCameraPixelFormat(self, v):
        with self.camera_pixelformat_lock:
            self.setConfiguration(CAMERA_PIXELFORMAT, v)

    def setPlugins(self, v):
        self.setConfiguration(MOVEPLUGINS, v)

    def checkBasicPaths(self):
        global CONFIG_STORAGE

        l = (
             FOLDER_STARTUP,
             FOLDER_LOG,
             FOLDER_PLUGINS,
             FOLDER_PROFILES,
             FOLDER_IMAGES,
             FOLDER_HTML,
             )

        self.printHeaderMsg("Testing configuration directories:")
        for (i, key) in enumerate(l):
            d = CONFIG_STORAGE[key]
            if os.path.exists(d) and os.path.isdir(d):
                self.printBulletMsg01("Directory ({} : {}) exists".format(key, d))
                pass
            if not os.path.exists(d):
                self.printBulletMsg02("Trying to create directory ({} : {})".format(key, d))
                os.mkdir(d)
                pass

    def getCameraPixelFormat(self):
        res = None
        with self.camera_pixelformat_lock:
            res = self.getConfiguration(CAMERA_PIXELFORMAT)
        return res

    def getPlugins(self):
        return self.getConfiguration(MOVEPLUGINS)

    def getFolderStartup(self):
        return self.getConfiguration(FOLDER_STARTUP)

    def getFolderPlugins(self):
        return self.getConfiguration(FOLDER_PLUGINS)

    def getMainLogFile(self):
        return self.getConfiguration(LOGGING_MAIN_FILE)

    def getFolderLog(self):
        return self.getConfiguration(FOLDER_LOG)

    def getFolderProfiles(self):
        return self.getConfiguration(FOLDER_PROFILES)

    def getLoggingMainFormat(self):
        return self.getConfiguration(LOGGING_MAIN_FORMAT)

    def getLoggingMainDate(self):
        return self.getConfiguration(LOGGING_MAIN_DATE)

    def getLoggingFileFormat(self):
        return self.getConfiguration(LOGGING_FILE_FORMAT)

    def getLoggingFileDate(self):
        return self.getConfiguration(LOGGING_FILE_DATE)

    def getWindowTitle(self):
        return self.getConfiguration(WINDOW_TITLE)

    def getCameraID(self):
        return self.getConfiguration(CAMERA_ID)

    def getFrameColorIndex(self):
        return self.getConfiguration(FRAME_COLORINDEX)

    def getDialogSelectorTitle(self):
        return self.getConfiguration(DIALOG_SELECTOR_TITLE)

    def getProfileSource(self):
        return self.getConfiguration(PROFILE_SOURCE)

    def getFolderHtml(self):
        return self.getConfiguration(FOLDER_HTML)

    def getLogoFile(self):
        return self.getConfiguration(LOGO_FILE)

    def printHeaderMsg(self, msg):
        """
        Prints message aas a header
        :param msg:
        :return:
        """
        print("\n### {}".format(msg))

    def printBulletMsg01(self, msg):
        """
        Prints message aas a header
        :param msg:
        :return:
        """
        print(" - {}".format(msg))

    def printBulletMsg02(self, msg):
        """
        Prints message aas a header
        :param msg:
        :return:
        """
        print("   {}".format(msg))


def get_instance():
    global CONFIG_INSTANCE

    if CONFIG_INSTANCE is None:
        Config()

    return CONFIG_INSTANCE