from app.common.imports import *
from app.common.keys import *

from app.ctrl import *
from app.gui.UI.ui_gain_exposure import *

__all__ = ["WidgetGainExposure"]

class WidgetGainExposure(QtWidgets.QWidget, Tester, Ui_Form):
    """
    Class representing gain/exposure control
    """
    def __init__(self, data, ctrl=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        Tester.__init__(self)

        Ui_Form.setupUi(self, self)

        self.exposure = data[CAMERA_EXPOSUREMERGED]
        self.gain = int(data[CAMERA_GAIN])

        self.gi = int(data[CAMERA_GAINMIN])
        self.ga = int(data[CAMERA_GAINMAX])

        self.ctrl = ctrl

        self.sldr_gain.sliderReleased.connect(self.processGain)
        self.sldr_exposure.sliderReleased.connect(self.processExposure)

        self.sldr_gain.valueChanged.connect(self.processGainMove)
        self.sldr_exposure.valueChanged.connect(self.processExposureMove)

        self.prepareUI()

    def prepareUI(self):
        """
        Prepares the values as they are seen by the camera
        :return:
        """
        try:
            self.gain = self.gain
            self.sldr_gain.setMinimum(self.gi)
            self.sldr_gain.setMaximum(self.ga)
            self.sldr_gain.setSingleStep(1)
            self.sldr_gain.setPageStep(1)

            self.debug("Slider gain ({}:{}:{})".format(self.gain, self.gi, self.ga))
            self.debug("Slider gain test 1 ({}:{}:{})".format(self.sldr_gain.minimum(), self.sldr_gain.value(), self.sldr_gain.maximum()))
            self.sldr_gain.setValue(self.gain)
            self.processGainMove()
        except ValueError:
            pass

        try:
            self.exposure = float(self.exposure)
            v = self.microSecondsToExposureSlider(self.exposure)
            self.sldr_exposure.setValue(v)
            self.processExposureMove()
        except ValueError:
            pass


    def processGain(self, ev=None):
        """
        Applies gain change
        :param ev:
        :return:
        """
        self.debug("Gain slider position has changed - updating")
        if self.ctrl is not None:
            try:
                v = self.sldr_gain.value()
                self.ctrl.registerGainChange(v)
            except AttributeError:
                pass

    def processExposure(self, ev=None):
        """
        Applies exposure change
        :param ev:
        :return:
        """
        self.debug("Exposure slider position has changed - updating")
        if self.ctrl is not None:
            try:
                v = self.exposureSliderToMicroSeconds(self.sldr_exposure.value())
                self.ctrl.registerExposureChange(v)
            except AttributeError:
                pass

    def processGainMove(self, v=None):
        """
        Applies gain change
        :param ev:
        :return:
        """
        msg = "{:02}".format(self.sldr_gain.value())
        self.debug("Slider gain test 2 ({}:{}:{}) {}".format(self.sldr_gain.minimum(), self.sldr_gain.value(),
                                                          self.sldr_gain.maximum(), msg))
        self.lbl_wgain.setText(msg)

    def processExposureMove(self, v=None):
        """
        Applies exposure change
        :param ev:
        :return:
        """
        v = self.exposureSliderToMicroSeconds(self.sldr_exposure.value())

        # values are in us, convert to a readable format
        fmt = "{:3.1f}"
        if 1000 <= v < 1e6:
            v = v / 1000.
            msg = fmt.format(v) + " ms"
        elif 1000 <= v < 1e6:
            v = v / 1000.
            msg = fmt.format(v) + " ms"
        elif 1e6 <= v < 10e7:
            v = v / 1000.
            msg = fmt.format(v) + " s"
        else:
            msg = fmt.format(v) + " us"

        self.lbl_wexposure.setText(msg)

    def exposureSliderToMicroSeconds(self, v):
        """
        Converts slider exposure position to microseconds value
        :param v:
        :return:
        """
        a, b = 0., 0.
        if 0. <= v < 150.:
            a, b = 6.376, 50.000
        elif 150. <= v < 300.:
            a, b = 6704.698, -1004704.698
        elif 300. <= v < 451.:
            a, b = 60000.000, -17000000.000

        res = float(int(a*v+b))
        return res

    def microSecondsToExposureSlider(self, v):
        """
        Converts slider exposure position to microseconds value
        :param v:
        :return:
        """

        a, b = 0., 0.

        if 50 <= v < 1000:
            a, b = 0.156842105, -7.842105263
        elif 1000 <= v < 1e6:
            a, b = 0.000149149, 149.85085
        elif 1e6 <= v < 1e7:
            a, b = 0.0000166667, 283.3333

        res = int(float(a*v+b))

        if res < self.sldr_exposure.minimum():
            res = self.sldr_exposure.minimum()
        if res > self.sldr_exposure.maximum():
            res = self.sldr_exposure.maximum()

        self.debug("Converting exposure real:slider ({}:{}:{})".format(v, res, self.exposureSliderToMicroSeconds(res)))

        return res
