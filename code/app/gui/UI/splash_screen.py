# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_splash_screen.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SplashScreen(object):
    def setupUi(self, SplashScreen):
        SplashScreen.setObjectName("SplashScreen")
        SplashScreen.resize(600, 400)
        SplashScreen.setAutoFillBackground(False)
        SplashScreen.setStyleSheet("QLabel#label {color: #fff; font-size: 25px; font-family: Arial; padding-left: 20px;}")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(SplashScreen)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_empty = QtWidgets.QLabel(SplashScreen)
        self.label_empty.setMinimumSize(QtCore.QSize(0, 300))
        self.label_empty.setText("")
        self.label_empty.setObjectName("label_empty")
        self.verticalLayout_2.addWidget(self.label_empty)
        self.label = QtWidgets.QLabel(SplashScreen)
        self.label.setMinimumSize(QtCore.QSize(0, 40))
        self.label.setText("")
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)

        self.retranslateUi(SplashScreen)
        QtCore.QMetaObject.connectSlotsByName(SplashScreen)

    def retranslateUi(self, SplashScreen):
        _translate = QtCore.QCoreApplication.translate
        SplashScreen.setWindowTitle(_translate("SplashScreen", "Form"))

import app.gui.UI.resource_splash_rc
