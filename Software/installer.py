import os
import sys
from time import sleep
import __GUI_images__
from zipfile import ZipFile
from threading import Thread
from __installer__ import Ui_Dialog
from PyQt5 import QtCore, QtGui, QtWidgets

CURRENT_OS = sys.platform
COMPILED = False #: if compilation is wanted

if CURRENT_OS == "win32":
    import ctypes
    import getpass
    import pythoncom
    from specialfolders import *
    from win32com.shell import shell, shellcon

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
    signal = QtCore.pyqtSignal(int)
    global CURRENT_OS, COMPILED, LICENSE
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
        self.signal.connect(self.progressBar.setValue)

        self.default_location()
        self.path = None
        self.thread = None
        self.finished = False
        self.stop_thread = False
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
        path_exists = False
        try:
            self.make_destination(path)
            path_exists = True
        except Exception as e:
            self.errorWindow(e)

        if path_exists:
            self.deactivate(True)
            try:
                self.unzip()# self.start_thread()
            except PermissionError as e:
                self.permissionWindow()

    def permissionWindow(self):
        msg = "In order to install in the following folder we require admin privileges. \
        \n\n\nPlease restart installer as admin."
        reply = QtWidgets.QMessageBox.warning(self, 'Exit',
                         msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            sys.exit()
        else:
            self.cancel_install()

    def deactivate(self, status):
        self.destination_lineEdit.setDisabled(status)
        self.destination_Button.setDisabled(status)

    def cancel_install(self):
        self.stop_thread = True
        self.thread = None


        self.deactivate(False)
        self.progress_label.setText("Canceled.")
        self.signal.emit(0)

    def unzip(self):
        # when compiled
        if COMPILED:
            zipf = resource_path('Quantum.zip')
        else:
            zipf = 'Quantum.zip'

        with ZipFile(zipf) as extractfile:
            members = extractfile.infolist()
            total = len(members)
            for (i, member) in enumerate(members):
                name = member.filename
                extractfile.extract(member, self.path)
                self.progress_label.setText("Unziping %s, file %d of %d"%(name, i+1, total))
                self.signal.emit(100*(i+1)//total)
                if self.stop_thread:
                    break

        if i == total -1:
            self.finished = True
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDisabled(True)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.close)
            self.progress_label.setText("Done")
            self.create_shortcut()

    def create_shortcut(self):
        if CURRENT_OS == "win32":
            executable = "%s\Quantum.exe"%self.path
            shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink,
              None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
            shortcut.SetPath(executable)
            shortcut.SetDescription("Reimagined Quantum")
            shortcut.SetIconLocation(executable, 0)

            desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
            menu_path = get_path(FOLDERID.StartMenu).replace("Default", getpass.getuser())

            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist_file.Save(os.path.join(desktop_path, "Reimagined Quantum.lnk"), 0)
            persist_file.Save(os.path.join(menu_path, "Reimagined Quantum.lnk"), 0)


    def make_destination(self, path):
        if os.path.exists(path):
            self.path = path
        else:
            path_parent = os.path.dirname(path)
            if os.path.exists(path_parent):
                answer = QtWidgets.QMessageBox.warning(self, 'Warning', 'Folder does not exist,\nDo you want to create it?', QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                if answer:
                    try:
                        os.mkdir(path)
                        self.path = path
                    except PermissionError:
                        self.permissionWindow()
            else:
                raise(Exception('Path does not exist'))

    def default_location(self):
        if CURRENT_OS == "win32":
            location = get_path(FOLDERID.ProgramFiles)
            self.destination_lineEdit.setText("%s\ReimaginedQuantum"%location)

    def browse_destination(self):
        name = QtWidgets.QFileDialog.getExistingDirectory()
        if name != '':
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
        if self.finished:
            event.accept()
        else:
            quit_msg = "Are you sure you want to exit the program?"
            reply = QtWidgets.QMessageBox.question(self, 'Exit',
                             quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if CURRENT_OS == 'win32':
    import ctypes
    # import admin
    # if not admin.isUserAdmin():
    #     admin.runAsAdmin()
    # if admin.isUserAdmin():
    app = QtWidgets.QApplication(sys.argv)
    app.processEvents()
    app.setWindowIcon(QtGui.QIcon(':/icon.png'))
    myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    main = Main()
    main.show()
    sys.exit(app.exec_())
