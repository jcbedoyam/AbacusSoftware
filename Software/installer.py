import os
import sys
from time import sleep
import __GUI_images__
from zipfile import ZipFile
from threading import Thread
from __installer__ import Ui_Dialog
from PyQt5 import QtCore, QtGui, QtWidgets
from shutil import rmtree

CURRENT_OS = sys.platform
COMPILED = True #: if compilation is wanted
APP_PATH = None

if CURRENT_OS == "win32":
    import ctypes
    import getpass
    import pythoncom
    from specialfolders import *
    from win32com.shell import shell, shellcon
    APP_PATH = get_path(FOLDERID.LocalAppData).replace("Default", getpass.getuser())
    APP_PATH = os.path.join(APP_PATH, "AbacusSoftware")

LICENSE = """Abacus Software
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
    finish_signal = QtCore.pyqtSignal()

    global CURRENT_OS, COMPILED, LICENSE
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.name_label.setFont(font)
        self.name_label.setText('Abacus Software')

        self.license_PlainText.setPlainText(LICENSE)
        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(100, 220, QtCore.Qt.KeepAspectRatio)
        self.logo_label.setPixmap(image)

        self.setWindowTitle("Install Abacus Software")

        self.destination_Button.clicked.connect(self.browse_destination)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.begin_install)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.cancel_install)
        self.signal.connect(self.progressBar.setValue)
        # self.extract_signal.connect(self.extra)
        self.finish_signal.connect(self.finishInstall)

        self.extracted_files = []
        self.default_location()
        self.path = None
        self.thread = None
        self.finished = False
        self.stop_thread = False
        self.create_thread()
        self.current_working = os.getcwd()

    def start_thread(self):
        self.stop_thread = False
        if self.thread != None:
            try:
                self.thread.start()
            except:
                self.thread = self.create_thread()
                self.thread.start()
        else:
            self.thread = self.create_thread()
            self.thread.start()

    def create_thread(self, target = "unzip"):
        if target == "unzip":
            target = self.unzip
        elif target == "cancel":
            target = self.delete_unzipped
        thread = Thread(target = target)
        thread.setDaemon(True)
        return thread

    def begin_install(self):
        path = self.destination_lineEdit.text()
        path_exists = False
        try:
            self.make_destination(path)
            path_exists = True
        except PermissionError:
            self.permissionWindow()
        except Exception as e:
            self.errorWindow(e)

        if path_exists:
            self.deactivate(True)
            self.start_thread()

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
        self.desktop_checkBox.setDisabled(status)
        self.startmenu_checkBox.setDisabled(status)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(status)

    def delete_unzipped(self):
        to_remove = []
        for (i, file) in enumerate(self.extracted_files):
            try:
                os.remove(file)
                to_remove.append(file)
                self.progress_label.setText("Deleted %s"%file)

            except Exception as e:
                pass

        dirs = list(set([os.path.dirname(x) for x in self.extracted_files]))

        for dir in dirs:
            try:
                rmtree(dir)
            except Exception as e:
                pass

        [self.extracted_files.remove(file) for file in to_remove]

        self.deactivate(False)
        sleep(0.1)
        self.signal.emit(0)
        self.progress_label.setText("Canceled.")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDisabled(False)

    def cancel_install(self):
        self.stop_thread = True
        self.thread = None
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDisabled(True)

        sleep(0.1)
        thread = self.create_thread('cancel')
        thread.start()

    def unzip(self):
        # when compiled
        i = 0
        if COMPILED:
            zipf = resource_path('AbacusSoftware.zip')
        else:
            zipf = 'AbacusSoftware.zip'
        try:
            with ZipFile(zipf) as extractfile:
                members = extractfile.namelist()
                total = len(members)
                for i, zipinfo in enumerate(members):
                    self.extracted_files.append(os.path.join(self.path, zipinfo))
                    extractfile.extract(zipinfo, self.path)

                    self.progress_label.setText("Unziping %s"%zipinfo)
                    self.signal.emit(98*(i+1)//total)
                    if self.stop_thread:
                        break

            with ZipFile(zipf) as extractfile:
                extractfile.extract("AbacusSoftware.exe", self.path)
                extractfile.extract("uninstaller.exe", self.path)

        except PermissionError:
            self.stop_thread = True
            self.permissionWindow()

        except Exception as e:
            self.stop_thread = True
            self.errorWindow(e)

        if i == total -1 and not self.stop_thread:
            self.finished = True
            self.finish_signal.emit()

    def finishInstall(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDisabled(True)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(sys.exit)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Finish")

        self.create_shortcut()
        self.progress_label.setText("Done")
        self.signal.emit(100)

    def create_shortcut(self):
        if CURRENT_OS == "win32":
            executable = os.path.join(self.path, "AbacusSoftware.exe")
            shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink,
              None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
            shortcut.SetPath(executable)
            shortcut.SetDescription("Abacus Software")
            shortcut.SetIconLocation(executable, 0)

            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            if self.desktop_checkBox.isChecked():
                desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
                persist_file.Save(os.path.join(desktop_path, "Abacus Software.lnk"), 0)

            if self.startmenu_checkBox.isChecked():
                menu_path = get_path(FOLDERID.StartMenu).replace("Default", getpass.getuser())
                folder = os.path.join(menu_path, "Abacus Software")
                if not os.path.exists(folder):
                    os.mkdir(folder)
                persist_file.Save(os.path.join(folder, "Abacus Software.lnk"), 0)

                executable = os.path.join(self.path, "uninstaller.exe")
                shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink,
                  None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
                shortcut.SetPath(executable)
                shortcut.SetDescription("Uninstall Abacus Software")
                shortcut.SetIconLocation(executable, 0)
                persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                persist_file.Save(os.path.join(folder, "Uninstall.lnk"), 0)

    def writePath(self):
        if APP_PATH != None:
            if not os.path.exists(APP_PATH):
                os.mkdir(APP_PATH)

            path = os.path.join(APP_PATH, "install_location.dat")
            with open(path, "w") as file_:
                file_.write(self.path)

    def make_destination(self, path):
        if os.path.exists(path):
            self.path = path
            self.writePath()
        else:
            path_parent = os.path.dirname(path)
            if os.path.exists(path_parent):
                os.mkdir(path)
                self.path = path
                self.writePath()
            else:
                raise(Exception('Path does not exist'))

    def default_location(self):
        if CURRENT_OS == "win32":
            location = get_path(FOLDERID.ProgramFiles)
            self.destination_lineEdit.setText("%s\Tausand"%location)

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
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if CURRENT_OS == 'win32':
    import ctypes
    import admin
    if not admin.isUserAdmin():
        admin.runAsAdmin()
    if admin.isUserAdmin():
        app = QtWidgets.QApplication(sys.argv)
        app.processEvents()
        app.setWindowIcon(QtGui.QIcon(':/icon.png'))
        myappid = 'abacus.abacus.01' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        main = Main()
        main.show()
        sys.exit(app.exec_())
