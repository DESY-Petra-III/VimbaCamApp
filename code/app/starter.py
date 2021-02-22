from app.common.imports import *
import app.config.main_config as config

from app.gui import *

class StarterException(Exception):
    pass

class Starter(Tester):
    # delay for dummy messages
    DUMMY_DELAY = 0.3

    def __init__(self, argv, script_fn, args, debug_level=None, file_logging=True):
        # setup default debug level
        if debug_level is not None:
            Tester.setDefaultLogging(debug_level)
        if isinstance(file_logging, bool):
            Tester.setDefaultFileLogging(file_logging)

        # preparation
        argv = self.prepare_additional_arguments(argv)
        self.config = config.get_instance()

        self.prepare_paths(argv, script_fn)
        self.config.setConfigFile(args.id)

        # cleaning logs
        self.cleanLogs()

        # class relies on logs
        Tester.__init__(self, def_file="{}".format(self.__class__.__name__.lower()))

        # vars
        #   application
        self.app = None
        #   splash
        self.spl = None
        #   main window
        self.main_wnd = None

        # port number
        self.camera_id = args.id
        self.config.setCameraID(self.camera_id)

        self.zmq = args.zmq

        # real application
        self.startApplication(argv)

    def startApplication(self, argv):
        """
        Initialization of the program
        :return:
        """
        c = self.config

        try:
            self.debug("Trying to show the splash screen")
            self.app = QtWidgets.QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(True)

            if not self.performTests():
                raise StarterException

            # here place initialization tests
            self.spl = AppSplashScreen()

            # start splash
            # processing initialization
            self.spl.show()
            self.setDummyMessage()

            self.main_wnd = MainWindow(self.camera_id, self.zmq)

            self.spl.finish(self.main_wnd)
            self.spl.close()

            sys.exit(self.app.exec_())
        except StarterException:
            self.debug("Exit on initial tests")
            sys.exit(-1)

    def prepare_additional_arguments(self, argv):
        """
        Prepares additional arguments
        :return:
        """
        return argv

    def prepare_paths(self, argv, script_fn):
        """
        prepares the most important paths
        :return:
        """
        basepath = os.path.dirname(argv[0])

        if len(basepath) == 0:
            basepath = os.path.dirname(script_fn)

        if len(basepath) == 0:
            basepath = os.getcwd()


        c = self.config

        if isinstance(c, config.Config):
            c.printHeaderMsg("Preparing configuration paths")
            path = basepath
            c.printBulletMsg01("Startup path ({})".format(path))
            c.setFolderStartup(path)

            path = os.path.join(basepath, "log")
            c.printBulletMsg01("Log path ({})".format(path))
            c.setFolderLog(path)

            path = os.path.join(basepath, "app", "plugins")
            c.printBulletMsg01("Plugin path ({})".format(path))
            c.setFolderPlugins(path)

            path = os.path.join(basepath, "html")
            c.printBulletMsg01("Html path ({})".format(path))
            c.setFolderHtml(path)

            path = os.path.join(basepath, "config")
            c.printBulletMsg01("Config path ({})".format(path))
            c.setFolderProfiles(path)

            path = os.path.join(basepath, "app", "images")
            c.printBulletMsg01("Config path ({})".format(path))
            c.setFolderImages(path)

            c.checkBasicPaths()

    def setDummyMessage(self):
        """
        Set dummy message
        :return:
        """
        self.spl.addDummyMessage()
        self.app.processEvents()
        time.sleep(self.DUMMY_DELAY)

        self.spl.addDummyMessage()
        self.app.processEvents()
        time.sleep(self.DUMMY_DELAY)

        self.spl.addDummyMessage()
        self.app.processEvents()
        time.sleep(self.DUMMY_DELAY)

        self.spl.addDummyMessage()
        self.app.processEvents()
        time.sleep(self.DUMMY_DELAY)
        pass

    def performTests(self):
        """
        Tests necessary for the startup
        :return:
        """
        self.debug("Performing startup tests")
        res = True

        return res

    def cleanLogs(self):
        """
        Cleans up the logs
        :return:
        """
        c = config.get_instance()
        c.printHeaderMsg("Cleaning log files")
        c.printBulletMsg01("Log directory is ({})".format(c.getFolderLog()))
        log_folder = c.getFolderLog()

        if log_folder is not None:
            for fn in os.listdir(c.getFolderLog()):
                fn = os.path.join(log_folder, fn)
                if os.path.isfile(fn):
                    print(" - Deleting old log file ({})".format(fn))
                    os.unlink(fn)