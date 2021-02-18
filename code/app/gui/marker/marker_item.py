from app.common.imports import *
from app.config import main_config as config

from .marker_shape import *

class MarkerSignal(QtCore.QObject):
    """
    Dummy opject for the signals
    """

    sign = QtCore.Signal(object)

    def __init__(self, func, parent=None):
        QtCore.QObject.__init__(self, parent=parent)

        self.sign.connect(func)

    def reportMenu(self, obj):
        self.sign.emit(obj)


class MarkerItem(QtWidgets.QGraphicsItemGroup):
    DEFAULT_COLOR = QtGui.QColor(255, 0, 0)
    DEFAULT_PENWIDTH = 3

    DEFAULT_HEIGHT = 100
    DEFAULT_WIDTH = 100

    SHAPE_ELLIPSE = 1
    SHAPE_BOUNDS = 2
    SHAPE_RECT = 3

    def __init__(self, shape=None, x=None, y=None, width=None, height=None,
                 color=None, penwidth=None, parent=None, feedback=None):
        QtWidgets.QGraphicsItemGroup.__init__(self, parent=parent)

        self.feedback = feedback
        self.config = config.get_instance()

        # main parameters
        self.color = color
        self.penwidth = penwidth

        # shape of the marker
        self.shapenum = shape

        self.w = width
        self.h = height

        self.x = x
        self.y = y

        # report object
        self.emitter = None

        self.prepParams()

        self.shape_ellipse = None
        self.shape_rect = None
        self.shape_bounds = None
        self.shape_cross = None

        # prepare a SHAPE
        self.prepShape()

        self.bgrabbed = False

    def prepShape(self):
        """
        Prepares a shape of the marker
        :return:
        """
        # simple rect
        rect = QtCore.QRectF(-self.w / 2+self.x, -self.h / 2+self.y, self.w, self.h)

        pen = QtGui.QPen(self.color)
        pen.setWidth(self.penwidth)

        # prepare individual shapes
        self.prepEllipse(rect)
        self.prepRect(rect)
        self.prepBounds(rect)
        self.prepCross(rect)

        tlst = list(self.getMarkerShapes())
        tlst.append(self.shape_cross)

        for (i, el) in enumerate(self.childItems()):
            if el == self.shape_cross:
                continue

            if el is not None:
                el.changePen(pen=pen)

            if el != self.shape_cross:
                if i != self.shapenum:
                    el.hide()
                else:
                    el.show()

    def showFrame(self, bstate=True):
        """
        Shows/hides frame of the marker
        :param bstate:
        :return:
        """
        for (i, el) in enumerate(self.getMarkerShapes()):
            if bstate:
                if i == self.shapenum:
                    el.show()
                else:
                    el.hide()
            else:
                el.hide()

    def showCross(self, bstate=True):
        """
        Shows/hides cental cross indication for the marker
        :param bstate:
        :return:
        """
        if bstate:
            self.shape_cross.show()
        else:
            self.shape_cross.hide()

    def prepEllipse(self, rect):
        """
        Prepares a group called ellipse
        :return:
        """
        if self.shape_ellipse is None:
            self.shape_ellipse = EllipseItem(rect, parent=self)

    def prepCross(self, rect):
        """
        Prepares a group called cross
        :return:
        """
        if self.shape_cross is None:
            self.shape_cross = CrossItem(rect, parent=self)

    def prepRect(self, rect):
        """
        Prepares a group called rect
        :return:
        """
        if self.shape_rect is None:
            self.shape_rect = RectItem(rect, parent=self)

    def prepBounds(self, rect):
        """
        Prepares a group called bounds
        :return:
        """
        if self.shape_bounds is None:
            self.shape_bounds = BoundsItem(rect, parent=self)

    def prepParams(self):
        """
        Prepares color and pen width parameters
        :return:
        """
        if self.color is None:
            self.color = self.DEFAULT_COLOR

        if self.penwidth is None:
            self.penwidth = self.DEFAULT_PENWIDTH

        if self.x is None:
            self.x = 0

        if self.y is None:
            self.y = 0

        if self.w is None:
            self.w = self.DEFAULT_WIDTH

        if self.h is None:
            self.h = self.DEFAULT_HEIGHT

        if self.shapenum is None:
            self.shapenum = self.SHAPE_ELLIPSE

        if self.feedback is not None:
            try:
                self.emitter = MarkerSignal(func=self.feedback.processMarkerMenu, parent=self.parentWidget())
            except AttributeError:
                pass

    def mouseGrab(self):
        """
        Grab mouse
        :return:
        """
        self.bgrabbed = False
        self.grabMouse()

    def cleanMouseGrab(self):
        """
        Stops mouse grab
        :return:
        """
        self.bgrabbed = False
        self.ungrabMouse()

    def mousePressEvent(self, ev: 'QGraphicsSceneMouseEvent') -> None:
        """

        :param ev:
        :return:
        """
        # print("Pressed")
        if ev.button() == QtCore.Qt.LeftButton:
            ev.accept()
            self.mouseGrab()
        else:
            ev.ignore()

    def mouseReleaseEvent(self, ev: 'QGraphicsSceneMouseEvent') -> None:
        """

        :param ev:
        :return:
        """
        if ev.button() == QtCore.Qt.LeftButton and self.bgrabbed:
            self.cleanMouseGrab()
        elif ev.button() == QtCore.Qt.RightButton:
            if isinstance(self.emitter, MarkerSignal):
                self.emitter.reportMenu([ev, self])
        else:
            ev.ignore()

    def mouseMoveEvent(self, ev: 'QGraphicsSceneMouseEvent') -> None:
        """
        Mouse move event
        :param ev:
        :return:
        """
        dp = ev.scenePos() - ev.lastScenePos()
        dx, dy = dp.x(), dp.y()

        self.moveBy(dx, dy)
        self.update()

    def setPenWidth(self, v):
        """
        Changes pen width
        :param v:
        :return:
        """
        self.penwidth = v

        for el in self.childItems():
            if isinstance(el, CrossItem):
                continue
            el.changePen(width=v)
            self.config.setcfMarkerLinewidth(v)

    def setColor(self, v):
        """
        Changes pen color
        :param v:
        :return:
        """
        for el in self.childItems():
            el.changePen(color=v)

    def getMarkerShapes(self):
        """
        Returns marker shapes
        :return:
        """
        return (self.shape_ellipse, self.shape_bounds, self.shape_rect)

    def changeMarkerShapeByStep(self, step=1, direction=1):
        """
        Changes visible shape of marker by switching trough different shapes
        :param direction:
        :param step:
        :return:
        """
        tlst = self.getMarkerShapes()

        self.shapenum += int(step * direction)

        ml = len(tlst) - 1
        if self.shapenum > ml:
            self.shapenum = 0
        elif self.shapenum < 0:
            self.shapenum = ml

        cnt = 0

        for (i, el) in enumerate(self.childItems()):
            if isinstance(el, CrossItem):
                continue

            if cnt != self.shapenum:
                el.hide()
            else:
                el.show()
                self.config.setcfMarkerShape(i)
            cnt += 1

    def doHResizeBy(self, value):
        """
        Resizes underlying markers by a certain value
        :param value:
        :param direction:
        :return:
        """
        for (i, el) in enumerate(self.getMarkerShapes()):
            try:
                el.adjustRect(value/2, 0)
                if i == 0:
                    self.w += value
                    self.config.setcfMarkerSize([self.w, self.h])
            except AttributeError as e:
                pass

    def doVResizeBy(self, value):
        """
        Resizes underlying markers by a certain value
        :param value:
        :param direction:
        :return:
        """
        for (i, el) in enumerate(self.getMarkerShapes()):
            try:
                el.adjustRect(0, value/2)
                if i == 0:
                    self.h += value
                    self.config.setcfMarkerSize([self.w, self.h])
            except AttributeError:
                pass

    def doMoveBy(self, dx, dy):
        """
        Moves the underlying markers by value
        :param value:
        :param direction:
        :return:
        """
        self.prepareGeometryChange()
        self.moveBy(dx, dy)