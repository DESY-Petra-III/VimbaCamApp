import re
import sys
import zmq
import json
import time
import copy

class CameraZMQClient(object):
    """
    Object handling communication with external server.
    Communication is done via json string communication
    """

    POLLER_NUM = 5          # number of poll attempts before a timeout
    POLLER_DELAY = 200      # TIME IN ms

    EXPOSURE = "Exposure"
    GAIN = "Gain"

    # communication
    REQUEST_CMD = "cmd"
    REQUEST_READ = "read"
    REQUEST_CHANGE = "change"
    REQUEST_PARAMS = "parameters"

    def __init__(self, zmqserver):
        self.server = zmqserver

        self._error = False

        # prepare server
        self.prepServer()

    def prepServer(self):
        """
        Performs a test of the
        :return:
        """
        p = re.compile("^tcp://.*:[0-9]+$")
        if not p.match(self.server):
            self.handle_error()
            raise ValueError("ZMQ server format ({}) is invalid".format(self.server))

    def send_data(self, data=None, breport=False, bread=False):
        """
        Sends data
        :param data:
        :return:
        """
        if self.is_error():
            return

        if not isinstance(data, dict) and not bread:
            return

        if data is not None:
            packet = self.prep_packet(data)
        elif bread:
            packet = self.prep_read()
        else:
            return

        # setup ZMQ, make a test
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)

        socket.connect(self.server)

        # use poll for timeouts:
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        # send data
        socket.send_json(packet)  # send can block on other socket types, so keep track

        # wait for a response
        cnt = 0
        msg = ""
        try:
            while True:
                if cnt == self.POLLER_NUM:
                    raise IOError("Timeout processing auth request")
                if poller.poll(self.POLLER_DELAY):  # 1s timeout in milliseconds
                    msg = socket.recv_string()
                    msg = json.loads(msg)

                    if breport:
                        print("Sent a packet: {}\nReceived a response: {}\n".format(packet, msg))
                    raise ValueError
                cnt += 1
        except IOError as e:
            self.handle_error(e)
        except json.JSONDecodeError as e:
            self.handle_error("Cannot decode json response ({}): {}".format(msg, e))
        except ValueError:
            pass

        poller.unregister(socket)
        socket.close()
        context.term()

    def read_data(self, breport=False):
        """
        Simplified function call
        :return:
        """
        self.send_data(bread=True, breport=breport)

    def handle_error(self, msg=None):
        """
        Handles error
        :return:
        """
        self._error = True
        if msg is not None:
            print(msg)

    def is_error(self):
        """
        Returns error state
        :return:
        """
        return self._error

    def prep_packet(self, data):
        """
        Prepares a packet to send out
        :param data:
        :return:
        """
        return {self.REQUEST_CMD: self.REQUEST_CHANGE, self.REQUEST_PARAMS: copy.deepcopy(data)}

    def prep_read(self):
        """
        Prepares a packet to read out data
        :return:
        """
        return {self.REQUEST_CMD: self.REQUEST_READ}

def main():
    z = CameraZMQClient("tcp://131.169.45.56:5555")
    z.read_data(breport=True)
    z.send_data({z.EXPOSURE: 1000., z.GAIN: 15}, breport=True)

if __name__ == "__main__":
    main()