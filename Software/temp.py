import os
import sys
import __GUI_images__
from zipfile import ZipFile
from threading import Thread
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
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.begin_install)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancel_install)

        self.default_location()
        self.path = None
        self.thread = None
        self.create_thread()

    def start_thread(self):
        if self.thread != None:
            try:
                self.thread.start()
            except:
                self.create_thread()
                self.thread.start()
        else:
            self.create_thread()
            self.thread.start()

    def create_thread(self):
        self.thread = Thread(target = self.unzip)
        self.thread.setDaemon(True)

    def begin_install(self):
        path = self.destination_lineEdit.text()
        try:
            self.make_destination(path)
        except exception as e:
            self.errorWindow(e)

    def cancel_install(self):
        pass

    def unzip(self):
        print("HERE")

    def make_destination(self, path):
        if os.path.exists(path):
            self.path = path
        else:
            path_parent = os.path.dirname(path)
            if os.path.exists(path_parent):
                answer = QtWidgets.QMessageBox.warning(self, 'Warning', 'Folder does not exist,\n Do you want to create it?', QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                if answer:
                    os.mkdir(path_parent)
                    self.path = path
            else:
                raise(Exception('Path does not exist'))

    def default_location(self):
        if CURRENT_OS == "win32":
            possible = ['C:\Program Files (x86)', 'C:\Program Files']
            for location in possible:
                exists = os.path.exists(location)
                if exists:
                    break
            if not exists:
                location = os.path.dirname(os.path.realpath(__file__))
            self.destination_lineEdit.setText("%s\ReimaginedQuantum"%location)

    def browse_destination(self):
        name = QtWidgets.QFileDialog.getExistingDirectory()
        self.destination_lineEdit.setText(name)

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
