from app.common.imports import *

class AbstractItem(QtWidgets.QGraphicsItemGroup):
    """
    Item in the shape of an ellipse
    """
    def __init__(self, rect: QtCore.QRectF, parent=None):
        QtWidgets.QGraphicsItemGroup.__init__(self, parent=parent)

        self.shape = None
        self.penwidth = None

        self.prepShape(rect)

    def prepShape(self, rect):
        pass

    def changeRect(self, rect):
        """
        Default implementation for the change of the shape
        :param rect:
        :return:
        """
        if self.shape is not None:
            try:
                self.shape.prepareGeometryChange()
                self.shape.setRect(rect)
            except AttributeError:
                pass

    def adjustRect(self, dx, dy):
        """
        Adjusting the real size of the shape
        :param dx:
        :param dy:
        :return:
        """
        try:
            rect: QtCore.QRectF = self.shape.rect()
            rect.adjust(-dx, -dy, dx, dy)
            self.shape.prepareGeometryChange()
            self.shape.setRect(rect)
        except AttributeError:
            pass

    def getRealRect(self):
        """
        Returns rectangle of the shape variable
        :return:
        """
        res = None
        try:
            res = self.shape.rect()
        except AttributeError:
            pass
        return res

    def changePen(self, pen=None, width=None, color=None):
        """
        Default implementation changing pen, width, color
        :param pen:
        :param width:
        :param color:
        :return:
        """
        def _parse(elements, pen=None, width=None, color=None):
            try:
                for el in elements:
                    if isinstance(el, QtWidgets.QGraphicsItemGroup):
                        _parse(el.childItems(), pen=pen, width=width, color=color)
                    else:
                        if not isinstance(pen, QtGui.QPen):
                            pen = el.pen()

                        if isinstance(width, int):
                            pen.setWidth(width)

                        if isinstance(color, QtGui.QColor):
                            pen.setColor(color)

                        el.prepareGeometryChange()
                        el.setPen(pen)
                self.penwidth = pen.width()
            except AttributeError:
                pass

        _parse(self.childItems(), pen=pen, width=width, color=color)


class EllipseItem(AbstractItem):
    """
    Item in the shape of an ellipse
    """
    def prepShape(self, rect):
        self.shape = QtWidgets.QGraphicsEllipseItem(rect, parent=self)
        self.shape.setRect(rect)

class RectItem(AbstractItem):
    """
    Item in the shape of an rectangle
    """
    def prepShape(self, rect):
        self.shape = QtWidgets.QGraphicsRectItem(rect, parent=self)
        self.shape.setRect(rect)

class BoundsItem(AbstractItem):
    """
    Item in the shape of bounds
    """
    BOUNDS_MINUS = -10
    BOUNDS_PLUS = 10

    def adjustRect(self, dx, dy):
        """
        Adjusts position of the bounding element
        :param dx:
        :param dy:
        :return:
        """

        if dx != 0:
            self.l1.prepareGeometryChange()
            self.l2.prepareGeometryChange()
            self.l1.moveBy(-dx, 0)
            self.l2.moveBy(dx, 0)

        if dy != 0:
            self.l3.prepareGeometryChange()
            self.l4.prepareGeometryChange()
            self.l3.moveBy(0, -dy)
            self.l4.moveBy(0, dy)

    def prepShape(self, rect):
        self.shape = QtWidgets.QGraphicsItemGroup(parent=self)

        x1, y1 = rect.x(), self.BOUNDS_MINUS
        x2, y2 = x1, self.BOUNDS_PLUS
        self.l1 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        x1, y1 = rect.x()+rect.width(), self.BOUNDS_MINUS
        x2, y2 = x1, self.BOUNDS_PLUS
        self.l2 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        x1, y1 = self.BOUNDS_MINUS, rect.y()
        x2, y2 = self.BOUNDS_PLUS, y1
        self.l3 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        x1, y1 = self.BOUNDS_MINUS, rect.y()+rect.height()
        x2, y2 = self.BOUNDS_PLUS, y1
        self.l4 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        self.addToGroup(self.shape)

    def changeRect(self, rect):
        x1, y1 = rect.x(), self.BOUNDS_MINUS
        x2, y2 = x1, self.BOUNDS_PLUS
        self.l1.setLine(x1, y1, x2, y2)

        x1, y1 = rect.x() + rect.width(), self.BOUNDS_MINUS
        x2, y2 = x1, self.BOUNDS_PLUS
        self.l2.setLine(x1, y1, x2, y2)

        x1, y1 = self.BOUNDS_MINUS, rect.y()
        x2, y2 = self.BOUNDS_PLUS, y1
        self.l3.setLine(x1, y1, x2, y2)

        x1, y1 = self.BOUNDS_MINUS, rect.y() + rect.height()
        x2, y2 = self.BOUNDS_PLUS, y1
        self.l4.setLine(x1, y1, x2, y2)

class CrossItem(AbstractItem):
    """
    Item in the shape of a cross
    """
    CROSS_X1 = 5
    CROSS_X2 = 15

    def adjustRect(self, dx, dy):
        pass
    
    def prepShape(self, rect):
        self.shape = QtWidgets.QGraphicsItemGroup(parent=self)

        x1, y1 = -self.CROSS_X2, 0
        x2, y2 = -self.CROSS_X1, 0

        self.l1 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        x1, y1 = self.CROSS_X1, 0
        x2, y2 = self.CROSS_X2, 0
        self.l2 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        x1, y1 = 0, self.CROSS_X2
        x2, y2 = 0, self.CROSS_X1
        self.l3 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        x1, y1 = 0, -self.CROSS_X1
        x2, y2 = 0, -self.CROSS_X2
        self.l4 = QtWidgets.QGraphicsLineItem(QtCore.QLineF(x1, y1, x2, y2), parent=self.shape)

        self.addToGroup(self.shape)

    def changeRect(self, rect):
        pass

    def changePen(self, pen=None, width=None, color=None):
        if width != None:
            width = None
        AbstractItem.changePen(self, pen=pen, width=width, color=color)
