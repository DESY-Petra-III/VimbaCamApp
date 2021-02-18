from app.common.imports import *
from .marker_menu_widget import *

__all__ = ["MarkerMenuPlugin"]

class MarkerMenuPlugin(object):
    """
    Abstract class implementation of menu item for a marker
    """
    PENWIDTH_MIN = 1
    PENWIDTH_MAX = 10

    def __init__(self, view, scene):
        self.marker = None

        self.view = view
        self.scene = scene

    def _makeWidthSlider(self):
        """
        Make a widget controlling width of the marker
        :return:
        """
        res = QtWidgets.QWidget()
        res.setToolTip("Changes width of the marker line")
        l = QtWidgets.QHBoxLayout()
        res.setLayout(l)

        l1 = QtWidgets.QLabel("{}".format(self.PENWIDTH_MIN))
        l2 = QtWidgets.QLabel("{}".format(self.PENWIDTH_MAX))
        sl = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        sl.setMinimum(self.PENWIDTH_MIN)
        sl.setMaximum(self.PENWIDTH_MAX)

        sl.setSliderPosition(self.marker.penwidth)
        sl.valueChanged.connect(self.processLineWidthChange)

        l.addWidget(l1)
        l.addWidget(sl)
        l.addWidget(l2)
        l.setStretch(1, 50)
        res.setMinimumSize(80, 30)

        return res

    def _makeMarkerPositionSizeChanger(self):
        """
        Prepares a widget controlling the marker widget size
        :return:
        """
        res = MarkerMenuWidget(self.marker)
        return res

    def _makeMarkerStyleChanger(self):
        """
        Make a widget controlling shape of the marker
        :return:
        """
        res = QtWidgets.QWidget()
        res.setToolTip("Changes style of the marker")
        l = QtWidgets.QHBoxLayout()
        res.setLayout(l)

        l1 = QtWidgets.QLabel("Style")
        l1.setAlignment(QtCore.Qt.AlignCenter)
        b1 = QtWidgets.QPushButton("<")
        b2 = QtWidgets.QPushButton(">")

        b1.clicked.connect(self.processMarkerChangeMinus)
        b2.clicked.connect(self.processMarkerChangePlus)

        for el in (b1, b2):
            el.setMinimumSize(30, 30)
            el.setMaximumSize(30, 30)

        l.addWidget(b1)
        l.addWidget(l1)
        l.addWidget(b2)

        l.setStretch(1, 50)
        res.setMinimumSize(80, 30)

        return res

    def processLineWidthChange(self, value):
        """
        Changes line width of the underlying marker
        :return:
        """
        if self.marker is not None:
            self.marker.setPenWidth(value)

    def processMarkerChangeByStep(self, direction):
        """
        Processes marker style change
        :param direction:
        :return:
        """
        if self.marker is not None:
            self.marker.changeMarkerShapeByStep(direction=direction)

    def processMarkerChangePlus(self):
        """
        Processes positive change of marker style index
        :return:
        """
        self.processMarkerChangeByStep(1)

    def processMarkerChangeMinus(self):
        """
        Processes negative change of marker style index
        :return:
        """
        self.processMarkerChangeByStep(-1)

    def processMarkerMenu(self, data):
        """
        Shows menu
        :param ev:
        :return:
        """
        ev, obj = data

        menu = QtWidgets.QMenu(parent=self.parent())

        a1 = QtWidgets.QWidgetAction(menu)
        w1 = self._makeMarkerStyleChanger()
        a1.setDefaultWidget(w1)
        menu.addAction(a1)

        a2 = QtWidgets.QWidgetAction(menu)
        w2 = self._makeWidthSlider()
        a2.setDefaultWidget(w2)
        menu.addAction(a2)

        a3 = QtWidgets.QWidgetAction(menu)
        w3 = self._makeMarkerPositionSizeChanger()
        a3.setDefaultWidget(w3)
        menu.addAction(a3)

        if isinstance(ev, QtWidgets.QGraphicsSceneMouseEvent):
            tp = self.view.mapToGlobal(self.view.mapFromScene(ev.scenePos()))
        else:
            tp = self.view.mapToGlobal(self.view.mapFromScene(ev.pos()))
        menu.exec_(tp)

        w1.deleteLater()
        w2.deleteLater()
        w3.deleteLater()