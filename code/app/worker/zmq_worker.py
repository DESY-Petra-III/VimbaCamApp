from app.common.imports import *

import zmq

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

__all__ = ["ZMQserver"]

ZMQINSTANCE = None

class ZMQserver(Tester):
    """
    Class responsible for ZMQ communication
    """

    def __init__(self, zmqparams, qmsg=None, ctrl=None):
        Tester.__init__(self)

        self.ctrl = ctrl
        self.zmqparams = zmqparams

        self.get_instance()

        self.msg_queue = qmsg
        self.proc = None

    def getError(self):
        """
        Returns the error state
        :return:
        """
        res = None
        if isinstance(self.proc, ZmqProcess):
            if self.proc.is_alive():
                res = self.proc.getError()
            else:
                res = True
            self.debug("Reporting zmq error value: {} {}".format(res, self.proc.is_alive()))
        return res

    def startZMQ(self):
        """
        Starts the ZMQ session of communication, server
        :return:
        """
        if not isinstance(self.proc, multiprocessing.Process) or not self.proc.is_alive():
            self.debug("Starting process")
            self.proc = ZmqProcess(self.zmqparams, self.msg_queue, parent=self)
            self.proc.start()

    def stopZMQ(self):
        """
        Stops the external process
        :return:
        """
        if isinstance(self.proc, ZmqProcess) and self.proc.is_alive():
            self.debug("Stopping process")
            self.proc.loggerCleanup()

    def get_instance(self=None):
        """
        Returns the instance
        :return:
        """
        res = None

        global ZMQINSTANCE

        if self is None:
            res = ZMQINSTANCE
        else:
            if ZMQINSTANCE is None:
                res = ZMQINSTANCE = self

        return res

    def setData(self, data):
        """
        Sets the data into a separate process running zmq server
        :param data:
        :return:
        """
        if isinstance(self.proc, ZmqProcess) and self.proc.is_alive():
            self.proc.setData(data)

    def isRunning(self):
        """
        Returns status of the running process
        :return:
        """
        res = False
        if isinstance(self.proc, threading.Thread) and self.proc.is_alive():
            res = True
        return res


class ZmqProcess(threading.Thread, Tester):
    """
    Function starting as a process with respect to the ZMQ communication
    :return:
    """
    SETUP = zmq.REQ

    RESPONSE_OK = '"OK"'
    RESPONSE_INVALID = '"INVALID"'
    RESPONSE_FAULT = '"FAULT"'


    REQUEST_CMD = "cmd"
    REQUEST_READ = "read"
    REQUEST_CHANGE = "change"
    REQUEST_PARAMS = "parameters"

    def __init__(self, zmqparams: str, msg_queue: queue.Queue, parent=None):
        threading.Thread.__init__(self)
        Tester.__init__(self)

        self.parent = parent
        self.zmqparams = zmqparams
        self.msg_queue = msg_queue

        # initial test
        self._error = True
        self._error_lock = threading.Lock()

        self.cam_data = None
        self.cam_data_lock = threading.Lock()

        self.daemon = True

    def setData(self, data):
        """
        Copies data from the main process into the ZMQ one
        :return:
        """
        self.debug("Setting zmq data ({})".format(data))
        with self.cam_data_lock:
            self.cam_data = copy.deepcopy(data)

    def getData(self):
        """
        Returns data copied from outside process
        :return:
        """
        res = None
        with self.cam_data_lock:
            res = copy.deepcopy(self.cam_data)

        return res

    def setError(self, v):
        """
        Sets the error state
        :return:
        """
        with self._error_lock:
            self._error = v
            self.debug("Error value is {}".format(v))

    def getError(self):
        """
        Sets the error state
        :return:
        """
        res = None
        with self._error_lock:
            res = self._error
            self.debug("Reporting error value {}".format(res))
        return res

    def run(self):
        """
        Starts workload of the ZMQ communication
        :return:
        """
        context = zmq.Context()
        try:
            with context.socket(zmq.REP) as socket:
                socket.bind(self.zmqparams)

                self.setError(False)

                self.debug("Serving external requests using ({})".format(self.zmqparams))
                while True:
                    response = self.RESPONSE_INVALID

                    value = None
                    try:
                        value = socket.recv_string()
                        value = json.loads(value)
                        self.debug("Received a message ({})".format(value))
                    except json.decoder.JSONDecodeError:
                        self.debug("Error: malformed message ({})".format(value))
                        response = self.RESPONSE_FAULT

                    try:
                        # read request and act upon
                        if isinstance(value, dict):
                            keys = value.keys()


                            if self.REQUEST_CMD in keys:
                                cmd = value[self.REQUEST_CMD].lower()
                                self.debug(cmd == self.REQUEST_CHANGE and self.REQUEST_PARAMS in keys and isinstance(
                                    value[self.REQUEST_PARAMS], dict))

                                # send out data if it is read
                                if cmd == self.REQUEST_READ:
                                    data = self.getData()
                                    self.debug("Sending out data ({})".format(data))
                                    response = json.dumps(data)

                                elif cmd == self.REQUEST_CHANGE and self.REQUEST_PARAMS in keys and isinstance(value[self.REQUEST_PARAMS], dict):
                                    # passing value from zmq to camera thread
                                    self.debug("Adding values into the queue for application: {}".format(value[self.REQUEST_PARAMS]))
                                    self.msg_queue.put(value[self.REQUEST_PARAMS])
                                    response = self.RESPONSE_OK
                                else:
                                    raise ValueError
                        else:
                            raise ValueError
                    except ValueError:
                        response = self.RESPONSE_INVALID

                    socket.send_string(response)
        except zmq.error.ZMQError as e:
            self.handleError(e)

    def handleError(self, msg):
        """
        Handles errors, displays messages, sets state
        :param msg:
        :return:
        """
        self.setError(True)
        self.error("Error:\n{}".format(msg))
        if self.parent is not None:
            try:
                self.parent.setError(self._error)
            except AttributeError:
                pass

    def __del__(self, *args, **kwargs):
        print("The zmq server process has finished")


def main():
    q = queue.Queue()
    z = ZMQserver(zmqparams="tcp://127.0.0.1:5555", qmsg=q)
    z.startZMQ()

    time.sleep(5)
    z.stopZMQ()

if __name__ == "__main__":
    main()