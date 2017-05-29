import os
import sys
import __GUI_images__
from zipfile import ZipFile
from __installer__ import Ui_Dialog
from PyQt5 import QtCore, QtGui, QtWidgets

CURRENT_OS = sys.platform
LICENSE = """Reimagined Quantum
Copyright (C) 2017 Juan Barbosa

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

class Main(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.name_label.setFont(font)
        self.name_label.setText('Reimagined Quantum')

        self.license_PlainText.setPlainText(LICENSE)
        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(100, 220, QtCore.Qt.KeepAspectRatio)
        self.logo_label.setPixmap(image)

        self.destination_Button.clicked.connect(self.browse_destination)
        self.path = None

    def make_destination(self, path):
        if os.path.exists(path):
            self.path = path
        else:
            path_parent = os.path.dirname(path)
            if os.path.exists(path_parent):
                os.mkdir(path_parent)
                self.path = path
            else:
                self.errorWindow(Exception('Path does not exist'))


    def browse_destination(self):
        name = QtWidgets.QFileDialog.getExistingDirectory()
        try:
            self.make_destination(name)
            self.destination_lineEdit.setText(name)
        except:
            pass

    def errorWindow(self, error):
        error_text = str(error)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        msg.setText('An Error has ocurred.\n%s'%error_text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec_()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Exit',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if CURRENT_OS == 'win32':
    import ctypes
    import admin
    if not admin.isUserAdmin():
        # admin.runAsAdmin()
        app = QtWidgets.QApplication(sys.argv)

        app.processEvents()
        app.setWindowIcon(QtGui.QIcon(':/icon.png'))
        myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        main = Main()
        main.show()
        sys.exit(app.exec_())
