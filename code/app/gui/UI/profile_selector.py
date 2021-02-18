# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_profile_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dialog_profile(object):
    def setupUi(self, dialog_profile):
        dialog_profile.setObjectName("dialog_profile")
        dialog_profile.resize(560, 416)
        self.gridLayout = QtWidgets.QGridLayout(dialog_profile)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(dialog_profile)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.listWidget = QtWidgets.QListWidget(dialog_profile)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 0, 0, 1, 1)

        self.retranslateUi(dialog_profile)
        self.buttonBox.accepted.connect(dialog_profile.accept)
        self.buttonBox.rejected.connect(dialog_profile.reject)
        QtCore.QMetaObject.connectSlotsByName(dialog_profile)

    def retranslateUi(self, dialog_profile):
        _translate = QtCore.QCoreApplication.translate
        dialog_profile.setWindowTitle(_translate("dialog_profile", "Dialog"))

