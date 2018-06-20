import abacusSoftware.__GUI_images__ as __GUI_images__

import pyAbacus as pa
from abacusSoftware.constants import __version__
from PyQt5 import QtCore, QtGui, QtWidgets
from abacusSoftware.__about__ import Ui_Dialog as Ui_Dialog_about

class AboutWindow(QtWidgets.QDialog, Ui_Dialog_about):
    def __init__(self, parent = None):
        super(AboutWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        self.parent = parent

        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(220, 220, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(image)

        tausand = '<a href="https://www.tausand.com/"> https://www.tausand.com </a>'
        pages =  '<a href="https://github.com/Tausand-dev/AbacusSoftware"> https://github.com/Tausand-dev/AbacusSoftware </a>'
        message = "Abacus Software is a suite of tools build to ensure your experience with Tausand's coincidence counters becomes simplified. \n\nSoftware Version: %s\nPyAbacus Version: %s\n\n"%(__version__, pa.__version__)
        self.message_label.setText(message)
        self.visit_label = QtWidgets.QLabel()
        self.github_label = QtWidgets.QLabel()
        self.pages_label = QtWidgets.QLabel()

        self.visit_label.setText("Visit us at: %s "%tausand)
        self.github_label.setText("More information on Abacus Software implementation can be found at: %s"%pages)
        self.verticalLayout.addWidget(self.visit_label)
        self.verticalLayout.addWidget(self.github_label)

        self.visit_label.linkActivated.connect(self.open_link)
        self.github_label.linkActivated.connect(self.open_link)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def open_link(self, link):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))
