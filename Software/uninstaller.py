import os
import sys
import __GUI_images__
from threading import Thread
from __uninstaller__ import Ui_Dialog
from PyQt5 import QtCore, QtGui, QtWidgets
from shutil import rmtree

from fileList import filelist

DEFAULT_PATH = None

CURRENT_OS = sys.platform

if CURRENT_OS == "win32":
    import ctypes
    import getpass
    import pythoncom
    from specialfolders import *
    from win32com.shell import shell, shellcon

    APP_PATH = get_path(FOLDERID.LocalAppData).replace("Default", getpass.getuser())
    APP_PATH = os.path.join(APP_PATH, "AbacusSoftware")

    DEFAULT_PATH = os.path.join(APP_PATH, "default.py")
    install_location = os.path.join(APP_PATH, "install_location.dat")

    if not os.path.exists(DEFAULT_PATH):
        DEFAULT_PATH = None
    if os.path.exists(install_location):
        with open(install_location) as file_:
            path = file_.readline()
        os.chdir(path)

class Main(QtWidgets.QDialog, Ui_Dialog):
    signal = QtCore.pyqtSignal(int)

    global CURRENT_OS
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        font = QtGui.QFont()
        font.setPointSize(16)
        self.name_label.setFont(font)
        self.name_label.setText('Abacus Software')

        self.label.setText("Are you sure you want to uninstall Abacus Software?")

        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(100, 220, QtCore.Qt.KeepAspectRatio)
        self.logo_label.setPixmap(image)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.uninstall)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.close)

        self.signal.connect(self.progressBar.setValue)

        self.finished = False

        self.thread = Thread(target = self.clean)
        self.thread.setDaemon(True)

    def cleanProgram(self):
        maxadvance = 98
        N = len(filelist)

        for (i, file) in enumerate(filelist):
            try:
                os.remove(file)
                self.progress_label.setText("Deleted %s"%file)
                self.signal.emit(maxadvance*i/N)

            except Exception as e:
                print(e)

        dirs = list(set([os.path.dirname(x) for x in filelist]))

        for dir_ in dirs:
            try:
                rmtree(dir_)
            except Exception as e:
                print(e)

        self.signal.emit(maxadvance)

    def cleanAppData(self):
        if DEFAULT_PATH != None:
            dir_ = os.path.dirname(DEFAULT_PATH)
            try:
                rmtree(dir_)
                self.progress_label.setText("Deleted %s"%dir_)
            except:
                print(e)

        self.signal.emit(99)

    def cleanShortCuts(self):
        desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        desktop_path = os.path.join(desktop_path, "Abacus Software.lnk")

        menu_path = get_path(FOLDERID.StartMenu).replace("Default", getpass.getuser())
        menu_path = os.path.join(menu_path, "Abacus Software")

        paths = [desktop_path, menu_path]
        for path in paths:
            try:
                if os.path.isdir(path):
                    rmtree(path)
                else:
                    os.remove(path)
                self.progress_label.setText("Deleted %s"%path)
            except Exception as e:
                print(e)

    def clean(self):
        self.cleanProgram()
        self.cleanAppData()
        self.cleanShortCuts()

        self.signal.emit(100)
        self.progress_label.setText("Done.")
        # self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(False)
        self.finished = True

    def uninstall(self):
        # self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.close)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(True)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setDisabled(True)

        self.thread.start()

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


if CURRENT_OS == 'win32':
    import ctypes
    import admin
    if not admin.isUserAdmin():
        admin.runAsAdmin()

    if admin.isUserAdmin():
        app = QtWidgets.QApplication(sys.argv)
        app.processEvents()
        app.setWindowIcon(QtGui.QIcon(':/uninstall.ico'))
        myappid = 'abacus.abacus.01' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        main = Main()
        main.show()
        sys.exit(app.exec_())
