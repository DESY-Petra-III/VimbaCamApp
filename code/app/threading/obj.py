from app.common.imports import *


class THO(QtCore.QObject, Tester):
    """
    Threadable object receiving notifications
    """
    COUNTER = 1

    # signals
    signshutdown = QtCore.Signal()

    def __init__(self, main_thread=None, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        Tester.__init__(self)

        # main thread
        self._mth = main_thread

        # stop flag
        self._bstop = False

        # active mutex
        self._mutex = QtCore.QMutex()

        # keep track of the inner counter
        self.inner_counter = 0
        self.COUNTER += 1

    @property
    def main_thread(self):
        return self._mth

    def work(self):
        """
        Main work done by the thread
        :return:
        """
        with QtCore.QMutexLocker(self._mutex):
            self.inner_counter += 1
            self.debug("Counter value ({})".format(self.inner_counter))

    def shutdown(self):
        self.debug("Shutdown was requested")

        # will wait until the end of the operation and then return to the main thread
        with QtCore.QMutexLocker(self._mutex):
            self.debug("Moving to the main thread ({})".format(self.main_thread))
            self.moveToThread(self.main_thread)

        self.debug("Notifying the main thread")

        # tell the tread to exit
        self.signshutdown.emit()

    def addThreadSignals(self, thread):
        """
        Add signals
        :param thread:
        :return:
        """
        self.debug("Connecting signals to the thread quit function")

        # notify the thread to quit
        self.signshutdown.connect(thread.quit)

class TO(QtCore.QObject, Tester):
    """
    Object polling data
    """

    signtimeout = QtCore.Signal()
    signshutdown = QtCore.Signal()

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        Tester.__init__(self)

        # properties
        self._ti = 1000

        # setup the polling timer
        self.th_timer = QtCore.QTimer(parent=self)
        self.th_timer.setSingleShot(False)

        # thread
        self.thread = QtCore.QThread()

        # main thread
        self._mth = QtCore.QThread.currentThread()

        # threaded object
        self.th_obj = THO(main_thread=self._mth)

        # start the threading
        self.startThreading()

    @property
    def timer_interval(self):
        return self._ti

    @timer_interval.setter
    def timer_interval(self, value):
        self._ti = value

    @property
    def main_thread(self):
        return self._mth

    def startTOTimer(self):
        """
        Starts timer
        :return:
        """
        self.debug("Starting timer")

        self.th_timer.setInterval(self.timer_interval)
        self.th_timer.start()

    def stopTimer(self):
        """
        Stops the polling timer
        :return:
        """
        self.debug("Stopping timer")

        self.th_timer.stop()

    def startThreading(self):
        """
        Starts the operation of threading
        :return:
        """
        self.debug("Initializing threading")

        # events - object related
        self.th_obj.addThreadSignals(self.thread)

        # connect current object to the worker
        self.signshutdown.connect(self.th_obj.shutdown)

        # move the object back to the thread
        self.th_obj.moveToThread(self.thread)

        # thread
        self.thread.started.connect(self.reportThreadStarted)
        self.thread.finished.connect(self.reportThreadFinished)
        # thread memory cleaning up
        self.thread.finished.connect(self.th_obj.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # timer
        self.th_timer.timeout.connect(self.th_obj.work)

        # start the thread and polling
        self.thread.start()

    def startPolling(self):
        """
        Starts the polling of the object
        :return:
        """
        # start the timer
        self.debug("Starting polling (timer state: {})".format(self.th_timer.isActive()))

        if not self.th_timer.isActive():
            self.startTOTimer()
        else:
            pass

    def stopPolling(self):
        """
        Stops the object polling
        :return:
        """
        # stop the timer
        if self.th_timer.isActive():
            self.th_timer.stop()
        else:
            pass

    def notifyShutdown(self):
        """
        Notify the worker about the shutdown
        :return:
        """
        self.debug("Notifying the event loop object of the shutdown")
        self.signshutdown.emit()

    def cleanup(self):
        """
        Cleans up the operation
        :return:
        """
        self.debug("Performing cleanup")

        if self.th_timer.isActive():
            self.stopTimer()

        # We notify the object on the shutdown
        if self.thread.isRunning():
            self.notifyShutdown()

        # we wait for the thread to finish
        self.thread.wait()

    def reportThreadStarted(self):
        """
        Report the thread status
        :return:
        """
        self.debug("Thread has reported a startup (started)")

    def reportThreadFinished(self):
        """
        Report the thread status
        :return:
        """
        self.debug("Thread has reported a shutdown (finished)")

    def reportThreadTerminated(self):
        """
        Report the thread status
        :return:
        """
        self.debug("Thread has reported a shutdown (terminated)")

# TODO - project control: work with PyTango - setup some dummy PyTango - need DeviceProxy, DevFailed, Attribute, Attribute config
# TODO - project batch processor - setup processing environment
