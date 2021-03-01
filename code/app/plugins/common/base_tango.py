import threading

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

try:
    from tango import DeviceProxy, DevFailed, DevState
except ImportError:
    from PyTango import DeviceProxy, DevFailed, DevState

class TangoMover(object):
    """
    Class wrapping movements for Tango devices
    """
    MSG_QUIT = "MSG_QUIT"

    ATTR_POSITION = "Position"

    def __init__(self, devnamex, devnamey, convx, convy, brealmove=False):
        object.__init__(self)

        # device names for x and y motor
        self.devx = devnamex
        self.devy = devnamey

        # conversion factors for x and y motors
        self.convx = convx
        self.convy = convy

        # flag indicating if movement should be actually implemented - debugging reasons
        self.brealmove = brealmove

        # list of threads
        self.threads = []
        self.qquit = Queue()

    def run(self, dx=None, dy=None):
        """
        Executes the main pay load - initializes devices and changes the attributes
        """
        if dx is not None and dx != 0:
            th = threading.Thread(target=self._move, args=[self.devx, self.convx*dx], daemon=True)
            self.threads.append(th)
            self.qquit.put(self.MSG_QUIT)

        if dy is not None and dy != 0:
            th = threading.Thread(target=self._move, args=[self.devy, self.convy*dy], daemon=True)
            self.threads.append(th)

        # let's work asynchrously
        for th in self.threads:
            th.start()

        # wait for all threads to stop - happens when a thread processes the quit queue
        self.qquit.join()

    def _move(self, devname, dv):
        """
        Performs a relative movement via the tango device
        """
        try:
            d = DeviceProxy(devname)
            d.ping()

            state = d.state()
            if state not in (DevState.ON, DevState.ALARM):
                raise DevFailed("Device ({}) is moving".format(devname))

            old_pos = d.read_attribute(self.ATTR_POSITION).value
            new_pos = old_pos + dv

            print("Old device {} position {:6.4f}".format(devname, old_pos))
            print("Moving device {} to {:6.4f}".format(devname, new_pos))
            if self.brealmove:
                d.write_attribute_asynch(self.ATTR_POSITION, new_pos)

        except (DevFailed, Exception) as e:
            print("Error while working with device ({}): {}".format(devname,  e))
        finally:
            try:
                self.qquit.get()
                self.qquit.task_done()
            except Empty:
                pass
