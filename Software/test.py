#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from random import random
# import __GUI_images__
import pyqtgraph as pg
from __mainwindow__ import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets

from constants import *
from files import ResultsFiles
from exceptions import ExtentionError

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """
        Defines the mainwindow.

    Constants
    """
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        self.settings_locked = False
        self.lock_settings_button.clicked.connect(self.lockSettings)

        self.port = None
        self.streaming = False
        self.acquisition_button.clicked.connect(self.startAcquisition)

        self.save_as_button.clicked.connect(self.chooseFile)

        self.save_as_lineEdit.editingFinished.connect(self.setSaveAs)

        """
        table
        """
        self.historical_table = QtGui.QTableWidget()
        self.historical_table.setColumnCount(4)
        self.historical_table.resizeRowsToContents()
        self.historical_table.resizeColumnsToContents()
        self.historical_layout = QtGui.QVBoxLayout()
        self.historical_layout.addWidget(self.historical_table)
        self.historical_tab.setLayout(self.historical_layout)

        self.initPlots()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.updatePlots)

    def lockSettings(self):
        self.sampling_comboBox.setEnabled(self.settings_locked)
        self.coincidence_spinBox.setEnabled(self.settings_locked)
        self.delay_A_spinBox.setEnabled(self.settings_locked)
        self.delay_B_spinBox.setEnabled(self.settings_locked)
        self.sleep_A_spinBox.setEnabled(self.settings_locked)
        self.sleep_B_spinBox.setEnabled(self.settings_locked)

        self.settings_locked = not self.settings_locked

    def connect(self):
        self.port = None

    def startAcquisition(self):
        if self.streaming:
            self.acquisition_button.setStyleSheet("background-color: none")
            self.acquisition_button.setText("Start acquisition")
            self.timer.stop()
        else:
            self.acquisition_button.setStyleSheet("background-color: green")
            self.acquisition_button.setText("Stop acquisition")
            self.timer.start()
        self.streaming = not self.streaming

    def updatePlots(self):
        n = 100

        self.countsA_line.setData(randomList(n))
        self.countsB_line.setData(randomList(n))

        self.coins_line.setData(randomList(n))

    def initPlots(self):
        pg.setConfigOptions(foreground = 'k', background = 'w', antialias = True)
        self.plot_win = pg.GraphicsWindow()
        self.counts_plot = self.plot_win.addPlot()
        self.coins_plot = self.plot_win.addPlot(row = 1, col = 0)

        symbolSize = 5
        self.countsA_line = self.counts_plot.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)
        self.countsB_line = self.counts_plot.plot(pen = "b", symbol='o', symbolPen = "b", symbolBrush="b", symbolSize=symbolSize)

        self.coins_line = self.coins_plot.plot(pen = "k", symbol='o', symbolPen = "k", symbolBrush="k", symbolSize=symbolSize)

        self.resultsFiles = None

        self.plot_layout = QtGui.QVBoxLayout()
        self.plot_layout.addWidget(self.plot_win)
        self.plots_frame.setLayout(self.plot_layout)

        self.counts_plot.setLabel('left', "Counts")
        self.coins_plot.setLabel('left', "Coincidences")
        self.coins_plot.setLabel('bottom', "Time", units='s')

    def setSaveAs(self):
        new_file_name = self.save_as_lineEdit.text()
        if new_file_name != "":
            name, ext = self.checkFileName(new_file_name)
            try:
                if self.resultsFiles == None:
                    self.resultsFiles = ResultsFiles(name, ext)
                else:
                    self.resultsFiles.changeName(name, ext)
                names = self.resultsFiles.getNames()
                self.statusBar.showMessage('Files: %s, %s.'%(names))
            except FileExistsError:
                print("FileExistsError")
        else:
            print("EmptyName")

    def checkFileName(self, name):
        if "." in name:
            name, ext = name.split(".")
            ext = ".%s"%ext
        else:
            ext = EXTENSION_DATA
            self.save_as_lineEdit.setText(name + ext)
        if ext in SUPPORTED_EXTENSIONS.keys():
            return name, ext
        else:
            raise ExtentionError()

    def chooseFile(self):
        """
        user interaction with saving file
        """
        dlg = QtWidgets.QFileDialog()
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        nameFilters = [SUPPORTED_EXTENSIONS[extension] for extension in SUPPORTED_EXTENSIONS]
        dlg.setNameFilters(nameFilters)
        dlg.selectNameFilter(SUPPORTED_EXTENSIONS[EXTENSION_DATA])
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            self.save_as_lineEdit.setText(name)
            self.setSaveAs()

    def closeEvent(self, event):
        if self.resultsFiles == None:
            event.accept()
        elif self.resultsFiles.areEmpty():
            event.accept()
        else:
            quit_msg = "Are you sure you want to exit the program?"
            reply = QtWidgets.QMessageBox.question(self, 'Exit',
                             quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

def randomList(n = 1):
    if n == 1:
        return random()
    else:
        return [random() for i in range(n-1)]

if __name__ == "__main__":
   app = QtWidgets.QApplication(sys.argv)
   # splash_pix = QtGui.QPixmap(':/splash.png')
   # splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
   # progressBar = QtWidgets.QProgressBar(splash)
   # progressBar.setGeometry(250, 350, 600, 20)
   # splash.show()
   app.processEvents()
   # icon = QtGui.QIcon(':/icon.png')
   # app.setWindowIcon(icon)
   #
   # if CURRENT_OS == 'win32':
   #     import ctypes
   #     myappid = 'abacus.abacus.01' # arbitrary string
   #     ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
   #
   # progressBar.setValue(15)
   #
   # thread = Thread(target = heavy_import)
   # thread.setDaemon(True)
   # thread.start()
   # i = 15
   # while thread.is_alive():
   #     if i < 95:
   #         i += 1
   #         progressBar.setValue(i)
   #     sleep(0.1)
   #
   # plt.rcParams.update({'font.size': 8})

   main = Main()
   # progressBar.setValue(100)
   main.show()
   # splash.close()
   sys.exit(app.exec_())
