from app.common.imports import *
from app.starter import Starter

def prep_args():
    parcer = argparse.ArgumentParser(description="Allied Camera homebrew application")
    parcer.add_argument('--id')
    parcer.add_argument('--zmq')

    return parcer.parse_args()

def test_params(params):
    """
    Performs a test of parameters
    :param id:
    :param zmq:
    :return:
    """
    res = False

    msg = ""
    try:
        id = str(params.id)
        zmq = str(params.zmq)

        pid = re.compile("^DEV_[a-zA-Z0-9]{12}$", re.IGNORECASE)
        pzmq = re.compile("^tcp://[^\:]:[0-9]+$", re.IGNORECASE)

        cnt = 0
        msg = ""
        if pid.match(id):
            cnt += 2
        else:
            msg += "Error: camera id parameter is invalid ({})\n".format(id)

        if pzmq.match(zmq):
            cnt += 4
        else:
            msg += "Error: zmq parameter is invalid ({})\n".format(zmq)

        if cnt & 4 and cnt & 2:
            res = True
    except AttributeError as e:
        print("Error {}".format(e))

    if len(msg) > 0:
        app = QtWidgets.QApplication([])
        msg = msg + """
Typical examples:
 --id DEV_000F314C6B39 - DEV_+12 alpha-numerical characters
 --zmq tcp://*:5555 - protocol name, IP address and port values"""
        QtWidgets.QMessageBox.critical(None, "Error with starting parameters", msg)
        print(msg)

    return res


def main():
    # preparation of arguments parser
    params = prep_args()

    # test of the supplied parameters
    test = test_params(params)

    # start of the main program
    if test:
        s = Starter(sys.argv, __file__, params, debug_level=logging.INFO, file_logging=False)

if __name__ == "__main__":
    main()

# DEV_1AB22C004C6D USB test usb iface VimbaUSBInterface_0x0
# DEV_000F314C6953 - test gige camera iface wifi
# DEV_000F314C6B39 - gp table cam
# --id DEV_000F314C6B39 --zmq tcp://*:5555