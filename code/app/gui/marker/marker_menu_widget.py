from app.common.imports import *

__all__ = ["MarkerMenuWidget"]

class MarkerMenuWidget(QtWidgets.QWidget):
    DEFAULT_POSSTEP = 2
    DEFAULT_SIZESTEP = 4

    PAGE_SIZE = 1
    PAGE_POSITION = 0

    MAX_STEP = 300

    DIRECTION_HORIZONTAL = 0
    DIRECTION_VERTICAL = 1

    STEP_SCALE = 10

    def __init__(self, marker, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.setMinimumSize(200, 200)
        self.setMaximumSize(300, 200)
        self.prepUI()

        # reference to the marker to control
        self.marker = marker

        # saving different steps fr
        self.last_posstep = None
        self.last_sizestep = None

        self.prepEvents()
        self.prepParams()

        self.sw_mode.setCurrentIndex(self.PAGE_SIZE)

        self.processModeChange(bswitch=False)

    def prepUI(self):
        """
        Prepares the design
        :return:
        """
        self.setObjectName("MarkerMenu")
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.widget_2 = QtWidgets.QWidget(self)
        self.widget_2.setObjectName("widget_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.widget_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.btn_hneg2 = QtWidgets.QPushButton(self.widget_2)
        self.btn_hneg2.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_hneg2.setObjectName("btn_hneg2")
        self.gridLayout_3.addWidget(self.btn_hneg2, 0, 0, 1, 1)
        self.btn_hneg = QtWidgets.QPushButton(self.widget_2)
        self.btn_hneg.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_hneg.setObjectName("btn_hneg")
        self.gridLayout_3.addWidget(self.btn_hneg, 0, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.widget_2)
        self.label_3.setMinimumSize(QtCore.QSize(50, 0))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 2, 1, 1)
        self.btn_hpos = QtWidgets.QPushButton(self.widget_2)
        self.btn_hpos.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_hpos.setObjectName("btn_hpos")
        self.gridLayout_3.addWidget(self.btn_hpos, 0, 3, 1, 1)
        self.btn_hpos2 = QtWidgets.QPushButton(self.widget_2)
        self.btn_hpos2.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_hpos2.setObjectName("btn_hpos2")
        self.gridLayout_3.addWidget(self.btn_hpos2, 0, 4, 1, 1)
        self.btn_vneg2 = QtWidgets.QPushButton(self.widget_2)
        self.btn_vneg2.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_vneg2.setObjectName("btn_vneg2")
        self.gridLayout_3.addWidget(self.btn_vneg2, 1, 0, 1, 1)
        self.btn_vneg = QtWidgets.QPushButton(self.widget_2)
        self.btn_vneg.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_vneg.setObjectName("btn_vneg")
        self.gridLayout_3.addWidget(self.btn_vneg, 1, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.widget_2)
        self.label_4.setMinimumSize(QtCore.QSize(50, 0))
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 1, 2, 1, 1)
        self.btn_vpos = QtWidgets.QPushButton(self.widget_2)
        self.btn_vpos.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_vpos.setObjectName("btn_vpos")
        self.gridLayout_3.addWidget(self.btn_vpos, 1, 3, 1, 1)
        self.btn_vpos2 = QtWidgets.QPushButton(self.widget_2)
        self.btn_vpos2.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_vpos2.setObjectName("btn_vpos2")
        self.gridLayout_3.addWidget(self.btn_vpos2, 1, 4, 1, 1)
        self.gridLayout.addWidget(self.widget_2, 1, 0, 1, 1)
        self.widget = QtWidgets.QWidget(self)
        self.widget.setObjectName("widget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.sw_mode = QtWidgets.QStackedWidget(self.widget)
        self.sw_mode.setObjectName("sw_mode")
        self.page_9 = QtWidgets.QWidget()
        self.page_9.setObjectName("page_9")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.page_9)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.label = QtWidgets.QLabel(self.page_9)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout_8.addWidget(self.label, 0, 0, 1, 1)
        self.sw_mode.addWidget(self.page_9)
        self.page_10 = QtWidgets.QWidget()
        self.page_10.setObjectName("page_10")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.page_10)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.label_9 = QtWidgets.QLabel(self.page_10)
        self.label_9.setAlignment(QtCore.Qt.AlignCenter)
        self.label_9.setObjectName("label_9")
        self.gridLayout_9.addWidget(self.label_9, 0, 0, 1, 1)
        self.sw_mode.addWidget(self.page_10)
        self.gridLayout_2.addWidget(self.sw_mode, 0, 1, 1, 1)
        self.btn_nextmode = QtWidgets.QPushButton(self.widget)
        self.btn_nextmode.setMinimumSize(QtCore.QSize(30, 30))
        self.btn_nextmode.setObjectName("btn_nextmode")
        self.gridLayout_2.addWidget(self.btn_nextmode, 0, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 0, 3, 1, 1)
        self.sb_step = QtWidgets.QSpinBox(self.widget)
        self.sb_step.setMinimumSize(QtCore.QSize(80, 30))
        self.sb_step.setAlignment(QtCore.Qt.AlignCenter)
        self.sb_step.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
        self.sb_step.setMinimum(1)
        self.sb_step.setMaximum(100)
        # self.sb_step.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.sb_step.setObjectName("sb_step")
        self.gridLayout_2.addWidget(self.sb_step, 0, 4, 1, 1)
        self.gridLayout_2.setColumnStretch(1, 50)
        self.gridLayout_2.setColumnStretch(2, 50)
        self.gridLayout.addWidget(self.widget, 0, 0, 1, 1)

        self.retranslateUi()
        self.sw_mode.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.setTabOrder(self.btn_hneg2, self.btn_hneg)
        self.setTabOrder(self.btn_hneg, self.btn_hpos)
        self.setTabOrder(self.btn_hpos, self.btn_hpos2)
        self.setTabOrder(self.btn_hpos2, self.btn_vneg2)
        self.setTabOrder(self.btn_vneg2, self.btn_vneg)
        self.setTabOrder(self.btn_vneg, self.btn_vpos)
        self.setTabOrder(self.btn_vpos, self.btn_vpos2)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.btn_hneg2.setToolTip(_translate("MarkerMenu", "Moves negative by 10*step"))
        self.btn_hneg2.setText(_translate("MarkerMenu", "<<"))
        self.btn_hneg.setToolTip(_translate("MarkerMenu", "Moves negative by single step"))
        self.btn_hneg.setText(_translate("MarkerMenu", "<"))
        self.label_3.setText(_translate("MarkerMenu", "Hor."))
        self.btn_hpos.setToolTip(_translate("MarkerMenu", "Moves positive by single step"))
        self.btn_hpos.setText(_translate("MarkerMenu", ">"))
        self.btn_hpos2.setToolTip(_translate("MarkerMenu", "Moves positive by 10*step"))
        self.btn_hpos2.setText(_translate("MarkerMenu", ">>"))
        self.btn_vneg2.setToolTip(_translate("MarkerMenu", "Moves negative by 10*step"))
        self.btn_vneg2.setText(_translate("MarkerMenu", "<<"))
        self.btn_vneg.setToolTip(_translate("MarkerMenu", "Moves negative by single step"))
        self.btn_vneg.setText(_translate("MarkerMenu", "<"))
        self.label_4.setText(_translate("MarkerMenu", "Ver."))
        self.btn_vpos.setToolTip(_translate("MarkerMenu", "Moves negative by single step"))
        self.btn_vpos.setText(_translate("MarkerMenu", ">"))
        self.btn_vpos2.setToolTip(_translate("MarkerMenu", "Moves positive by 10*step"))
        self.btn_vpos2.setText(_translate("MarkerMenu", ">>"))
        self.btn_nextmode.setToolTip(_translate("MarkerMenu", "Changes operating mode ()"))
        self.btn_nextmode.setText(_translate("MarkerMenu", ">"))
        self.sw_mode.setToolTip(_translate("MarkerMenu", "Operating mode"))
        self.label.setText(_translate("MarkerMenu", "Position"))
        self.label_9.setToolTip(_translate("MarkerMenu", "Operating mode"))
        self.label_9.setText(_translate("MarkerMenu", "Resize"))
        self.sb_step.setToolTip(_translate("MarkerMenu", "step size"))
        self.label_2.setText(_translate("MarkerMenu", "Step size:"))

    def prepEvents(self):
        """
        Prepares evens for the widget gui elements
        :return:
        """
        func = lambda: self.processModeChange(bswitch=True)
        self.btn_nextmode.clicked.connect(func)

        dh = self.DIRECTION_HORIZONTAL
        func = lambda: self.processMarkerGeometryChange(1, dh)
        self.btn_hpos.clicked.connect(func)
        func = lambda: self.processMarkerGeometryChange(-1, dh)
        self.btn_hneg.clicked.connect(func)
        func = lambda: self.processMarkerGeometryChange(self.STEP_SCALE, dh)
        self.btn_hpos2.clicked.connect(func)
        func = lambda: self.processMarkerGeometryChange(-self.STEP_SCALE, dh)
        self.btn_hneg2.clicked.connect(func)

        dv = self.DIRECTION_VERTICAL
        func = lambda: self.processMarkerGeometryChange(1, dv)
        self.btn_vpos.clicked.connect(func)
        func = lambda: self.processMarkerGeometryChange(-1, dv)
        self.btn_vneg.clicked.connect(func)
        func = lambda: self.processMarkerGeometryChange(self.STEP_SCALE, dv)
        self.btn_vpos2.clicked.connect(func)
        func = lambda: self.processMarkerGeometryChange(-self.STEP_SCALE, dv)
        self.btn_vneg2.clicked.connect(func)


    def prepParams(self):
        """
        Prepares default parameters
        :return:
        """
        if self.last_posstep is None:
            self.last_posstep = self.DEFAULT_POSSTEP

        if self.last_sizestep is None:
            self.last_sizestep = self.DEFAULT_SIZESTEP

        self.sb_step.setMaximum(self.MAX_STEP)

    def processModeChange(self, bswitch=True):
        """
        Shows indication which mode is active (resizing, moving)
        :return:
        """
        old_ci = ci = self.sw_mode.currentIndex()

        if bswitch:
            len = self.sw_mode.count() - 1
            ci += 1

            if ci > len:
                ci = 0

        self.sw_mode.setCurrentIndex(ci)

        if ci == self.PAGE_SIZE:
            self.last_posstep = self.sb_step.value()
            self.sb_step.setMinimum(self.DEFAULT_SIZESTEP)
            self.sb_step.setValue(self.last_sizestep)
        elif ci == self.PAGE_POSITION:
            self.last_sizestep = self.sb_step.value()
            self.sb_step.setMinimum(self.DEFAULT_POSSTEP)
            self.sb_step.setValue(self.last_posstep)

    def processMarkerGeometryChange(self, *args):
        """
        Receives events changing geometry of the marker
        :return:
        """

        value, direction = args
        value = float(value * self.sb_step.value())

        mode = self.sw_mode.currentIndex()

        if mode == self.PAGE_POSITION:
            self.changeMarkerPosition(value=value, direction=direction)
        elif mode == self.PAGE_SIZE:
            self.changeMarkerSize(value=value, direction=direction)

    def changeMarkerSize(self, value=1, direction=None):
        """
        Induces a change of marker size
        :param direction:
        :param value:
        :return:
        """
        if self.marker is not None:
            try:
                if direction == self.DIRECTION_VERTICAL:
                    self.marker.doVResizeBy(value)
                elif direction == self.DIRECTION_HORIZONTAL:
                    self.marker.doHResizeBy(value)
            except AttributeError:
                pass

    def changeMarkerPosition(self, value=1, direction=None):
        """
        Induces a change of marker position
        :param direction:
        :param value:
        :return:
        """
        if self.marker is not None:
            try:
                if direction == self.DIRECTION_HORIZONTAL:
                    self.marker.doMoveBy(value, 0)
                elif direction == self.DIRECTION_VERTICAL:
                    self.marker.doMoveBy(0, value)
            except AttributeError:
                pass