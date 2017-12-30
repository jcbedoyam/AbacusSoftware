#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import numpy as np
from time import time
import __GUI_images__
import pyqtgraph as pg
from __mainwindow__ import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets

from constants import *
from supportWidgets import Table, CurrentLabels
from files import ResultsFiles, RingBuffer
from MenuBar import AboutWindow
from exceptions import ExtentionError

import PyAbacus as abacus
from PyAbacus.communication import findPorts, CommunicationPort

class ConnectDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.frame = QtWidgets.QFrame()

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)

        self.label = QtWidgets.QLabel()

        self.verticalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.frame)

        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        self.refresh_button = QtWidgets.QPushButton()
        self.refresh_button.setText("Refresh")
        self.refresh_button.clicked.connect(self.refresh)

        self.horizontalLayout.addWidget(self.comboBox)
        self.horizontalLayout.addWidget(self.refresh_button)

        self.label.setText(CONNECT_LABEL)
        self.label.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        self.setWindowTitle("Tausand Abacus device selection")
        self.setMinimumSize(QtCore.QSize(450, 100))

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        self.verticalLayout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject2)

        self.ports = None

    def refresh(self):
        self.clear()
        self.ports = findPorts()
        ports_names = list(self.ports.keys())
        if len(ports_names) == 0:
            self.label.setText(CONNECT_EMPTY_LABEL)
        else:
            self.label.setText(CONNECT_LABEL)
        self.comboBox.addItems(ports_names)
        self.adjustSize()

    def clear(self):
        self.comboBox.clear()

    def reject2(self):
        self.clear()
        self.reject()

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """
        Defines the mainwindow.

    Constants
    """
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        self.resize(650, 750)

        self.setSettings()

        self.settings_locked = False
        self.lock_settings_button.clicked.connect(self.lockSettings)

        self.port = None
        self.port_name = None
        self.streaming = False
        self.experiment = None
        self.acquisition_button.clicked.connect(self.startAcquisition)

        """
        connect
        """
        self.connect_dialog = None
        self.connect_button.clicked.connect(self.connect)


        """
        settigns connections
        """
        self.sampling_comboBox.currentIndexChanged.connect(self.samplingMethod)
        self.coincidence_spinBox.valueChanged.connect(self.coincidenceWindowMethod)
        self.delay_A_spinBox.valueChanged.connect(self.delayAMethod)
        self.delay_B_spinBox.valueChanged.connect(self.delayBMethod)
        self.sleep_A_spinBox.valueChanged.connect(self.sleepAMethod)
        self.sleep_B_spinBox.valueChanged.connect(self.sleepBMethod)

        """
        table
        """
        self.historical_table = Table(4)
        self.historical_layout = QtGui.QVBoxLayout()
        self.historical_layout.addWidget(self.historical_table)
        self.historical_tab.setLayout(self.historical_layout)

        """
        current labels
        """
        self.current_labels = CurrentLabels(self.current_tab)

        self.initPlots()
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(DATA_REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.updateWidgets)

        self.data_timer = QtCore.QTimer()
        self.data_timer.setInterval(DATA_REFRESH_RATE)
        self.data_timer.timeout.connect(self.updateData)

        self.check_timer = QtCore.QTimer()
        self.check_timer.setInterval(CHECK_RATE)
        self.check_timer.timeout.connect(self.checkParams)

        self.results_files = None
        self.init_time = 0

        self.data_ring = RingBuffer(BUFFER_ROWS, 4)

        self.save_as_button.clicked.connect(self.chooseFile)
        self.save_as_lineEdit.returnPressed.connect(self.setSaveAs)

        """
        MenuBar
        """
        self.actionSave_as.triggered.connect(self.chooseFile)
        self.actionSave_as.setShortcut("Ctrl+S")
        self.actionAbout.triggered.connect(self.aboutWindowCaller)
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setShortcut("Ctrl+Q")

        self.acquisition_button.setDisabled(True)
        self.about_window = AboutWindow()

        self.setWindowTitle(WINDOW_NAME)

        self.connect()

    def aboutWindowCaller(self):
        self.about_window.show()

    def timeInUnitsToMs(self, time):
        value = 0
        if 'ms' in time:
            value = int(time.replace('ms', ''))
        elif 's' in time:
            value = int(time.replace('s', ''))*1000
        return value

    def sendSettings(self):
        self.samplingMethod(self.sampling_comboBox.currentIndex())
        self.coincidenceWindowMethod(self.coincidence_spinBox.value())
        self.delayAMethod(self.delay_A_spinBox.value())
        self.delayBMethod(self.delay_B_spinBox.value())
        self.sleepAMethod(self.sleep_A_spinBox.value())
        self.sleepBMethod(self.sleep_B_spinBox.value())

    def samplingMethod(self, index):
        text_value = self.sampling_comboBox.currentText()
        value = self.timeInUnitsToMs(text_value)
        if value > 0:
            if value > DATA_REFRESH_RATE:
                self.refresh_timer.setInterval(value)
            else:
                self.refresh_timer.setInterval(DATA_REFRESH_RATE)

            self.data_timer.setInterval(value)
            if self.results_files != None:
                self.results_files.writeParams("Sampling time: %s"%text_value)
            try:
                self.experiment.setSampling(value)
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)

    def coincidenceWindowMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.setCoinWindow(val)
                if self.results_files != None:
                    self.results_files.writeParams("Coincidence Window: %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Coincidence Window Value: %d"%val)

    def delayAMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[0].setDelay(val)
                if self.results_files != None:
                    self.results_files.writeParams("Delay A: %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Delay A Value: %d"%val)

    def delayBMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[1].setDelay(val)
                if self.results_files != None:
                    self.results_files.writeParams("Delay B: %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Delay B Value: %d"%val)

    def sleepAMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[0].setSleep(val)
                if self.results_files != None:
                    self.results_files.writeParams("Sleep A: %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Sleep A Value: %d"%val)

    def sleepBMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[1].setSleep(val)
                if self.results_files != None:
                    self.results_files.writeParams("Sleep B: %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Sleep B Value: %d"%val)

    def checkParams(self):
        if self.experiment != None:
            try:
                self.experiment.periodicCheck()
                samp = self.experiment.getSamplingValue()
                coin = self.experiment.getCoinwinValue()
                values = self.experiment.getDetectorsTimersValues()
                (dA, sA), (dB, sB) = values

                if self.timeInUnitsToMs(self.sampling_comboBox.currentText()) != samp:
                    if samp > 1000:
                        index = self.sampling_comboBox.findText('%d s'%(samp/1000))
                    else:
                        index = self.sampling_comboBox.findText('%d ms'%samp)
                    self.sampling_comboBox.setCurrentIndex(index)
                if self.coincidence_spinBox.value() != coin:
                    self.coincidence_spinBox.setValue(coin)
                if self.delay_A_spinBox.value() != dA:
                    self.delay_A_spinBox.setValue(dA)
                if self.delay_B_spinBox.value() != dB:
                    self.delay_B_spinBox.setValue(dB)
                if self.sleep_A_spinBox.value() != sA:
                    self.sleep_A_spinBox.setValue(sA)
                if self.sleep_B_spinBox.value() != sB:
                    self.sleep_B_spinBox.setValue(sB)
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)

    def lockSettings(self):
        self.sampling_comboBox.setEnabled(self.settings_locked)
        self.coincidence_spinBox.setEnabled(self.settings_locked)
        self.delay_A_spinBox.setEnabled(self.settings_locked)
        self.delay_B_spinBox.setEnabled(self.settings_locked)
        self.sleep_A_spinBox.setEnabled(self.settings_locked)
        self.sleep_B_spinBox.setEnabled(self.settings_locked)

        self.settings_locked = not self.settings_locked

    def setSettings(self):
        self.sampling_comboBox.clear()

        model = self.sampling_comboBox.model()
        for row in abacus.SAMP_VALUES:
            item = QtGui.QStandardItem(row)
            if self.timeInUnitsToMs(row) < abacus.SAMP_CUTOFF:
                item.setBackground(QtGui.QColor('red'))
                item.setForeground(QtGui.QColor('white'))
            model.appendRow(item)

        index = self.sampling_comboBox.findText(abacus.DEFAULT_SAMP)
        self.sampling_comboBox.setCurrentIndex(index)
        self.coincidence_spinBox.setMinimum(abacus.MIN_COIN)
        self.coincidence_spinBox.setMaximum(abacus.MAX_COIN)
        self.coincidence_spinBox.setSingleStep(abacus.STEP_COIN)
        self.coincidence_spinBox.setValue(abacus.DEFAULT_COIN)

        self.delay_A_spinBox.setMinimum(abacus.MIN_DELAY)
        self.delay_A_spinBox.setMaximum(abacus.MAX_DELAY)
        self.delay_A_spinBox.setSingleStep(abacus.STEP_DELAY)
        self.delay_A_spinBox.setValue(abacus.DEFAULT_DELAY)

        self.delay_B_spinBox.setMinimum(abacus.MIN_DELAY)
        self.delay_B_spinBox.setMaximum(abacus.MAX_DELAY)
        self.delay_B_spinBox.setSingleStep(abacus.STEP_DELAY)
        self.delay_B_spinBox.setValue(abacus.DEFAULT_DELAY)

        self.sleep_A_spinBox.setMinimum(abacus.MIN_SLEEP)
        self.sleep_A_spinBox.setMaximum(abacus.MAX_SLEEP)
        self.sleep_A_spinBox.setSingleStep(abacus.STEP_SLEEP)
        self.sleep_A_spinBox.setValue(abacus.DEFAULT_SLEEP)

        self.sleep_B_spinBox.setMinimum(abacus.MIN_SLEEP)
        self.sleep_B_spinBox.setMaximum(abacus.MAX_SLEEP)
        self.sleep_B_spinBox.setSingleStep(abacus.STEP_SLEEP)
        self.sleep_B_spinBox.setValue(abacus.DEFAULT_SLEEP)

    def cleanPort(self):
        if self.port != None:
            self.port.close()
            self.port_name = None
            self.port = None

    def connect(self):
        self.cleanPort()
        self.connect_dialog = ConnectDialog()
        self.connect_dialog.refresh()
        self.connect_dialog.exec_()

        port = self.connect_dialog.comboBox.currentText()

        if port != "":
            self.port_name = port
            self.port = CommunicationPort(self.connect_dialog.ports[self.port_name])
            self.experiment = abacus.Experiment(self.port)

            # self.current_labels.createLabels(self.experiment.detectors, self.experiment.coin_channels)
            self.acquisition_button.setDisabled(False)
            self.acquisition_button.setStyleSheet("background-color: none")
            self.acquisition_button.setText("Start acquisition")

            if len(self.current_labels.labels) == 0:
                self.current_labels.createLabels()
                self.current_labels.setColors(["red", "blue", "black"])
        else:
            self.acquisition_button.setDisabled(True)

    def startClocks(self):
        self.refresh_timer.start()
        self.check_timer.start()
        self.data_timer.start()

    def stopClocks(self):
        self.refresh_timer.stop()
        self.check_timer.stop()
        self.data_timer.stop()
        self.data_ring.save()

    def startAcquisition(self):
        if self.port == None:
            QtWidgets.QMessageBox.warning(self, 'Error', "Port has not been choosed", QtWidgets.QMessageBox.Ok)
        elif self.results_files != None:
            if self.streaming:
                self.acquisition_button.setStyleSheet("background-color: none")
                self.acquisition_button.setText("Start acquisition")
                self.results_files.writeParams("STOPED")
                self.stopClocks()
            else:
                self.acquisition_button.setStyleSheet("background-color: green")
                self.acquisition_button.setText("Stop acquisition")
                self.results_files.writeParams("STARTED")
                self.sendSettings()
                self.startClocks()

            self.streaming = not self.streaming
            if self.init_time == 0:
                self.init_time = time()
        else:
            QtWidgets.QMessageBox.warning(self, 'Error', "Please choose an output file.", QtWidgets.QMessageBox.Ok)

    def updateData(self):
        try:
            time_, detectors, coins = self.experiment.currentValues()
            time_ += -self.init_time

            values = np.array([time_] + detectors + coins)
            values = values.reshape((1, values.shape[0]))
            self.data_ring.extend(values)
        except abacus.exceptions.ExperimentError as e:
            self.errorWindow(e)

    def updateWidgets(self):
        data = self.data_ring[:]

        self.updatePlots(data)
        self.updateTable(data)
        self.updateCurrents(data)

    def updateTable(self, data):
        self.historical_table.insertData(data)

    def updateCurrents(self, data):
        for i in range(1, 4):
            self.current_labels.changeValue(i-1, data[-1, i])

    def updatePlots(self, data):
        time_ = data[:, 0]

        self.countsA_line.setData(time_, data[:, 1])
        self.countsB_line.setData(time_, data[:, 2])

        self.coins_line.setData(time_, data[:, 3])

    def initPlots(self):
        pg.setConfigOptions(foreground = 'k', background = None, antialias = True)
        self.plot_win = pg.GraphicsWindow()

        self.counts_plot = self.plot_win.addPlot()
        self.coins_plot = self.plot_win.addPlot(row = 1, col = 0)

        self.counts_plot.addLegend()
        self.coins_plot.addLegend()

        symbolSize = 5
        self.countsA_line = self.counts_plot.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize, name="Detector A")
        self.countsB_line = self.counts_plot.plot(pen = "b", symbol='o', symbolPen = "b", symbolBrush="b", symbolSize=symbolSize, name="Detector B")

        self.coins_line = self.coins_plot.plot(pen = "k", symbol='o', symbolPen = "k", symbolBrush="k", symbolSize=symbolSize, name="Coincidences AB")

        self.plot_layout = QtGui.QVBoxLayout()
        self.plot_layout.addWidget(self.plot_win)
        self.plots_frame.setLayout(self.plot_layout)

        self.counts_plot.setLabel('left', "Counts")
        self.coins_plot.setLabel('left', "Coincidences")
        self.coins_plot.setLabel('bottom', "Time", units='s')

    def setSaveAs(self):
        new_file_name = self.save_as_lineEdit.text()
        if new_file_name != "":
            try:
                name, ext = self.checkFileName(new_file_name)
                if self.results_files == None:
                    self.results_files = ResultsFiles(name, ext)
                else:
                    self.results_files.changeName(name, ext)
                names = self.results_files.getNames()
                self.data_ring.setFile(self.results_files.data_file)
                self.statusBar.showMessage('Files: %s, %s.'%(names))
                try:
                    self.results_files.checkFilesExists()
                except FileExistsError:
                    print("FileExistsError")
            except ExtentionError as e:
                self.save_as_lineEdit.setText("")
                self.errorWindow(e)
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
        dlg = QtWidgets.QFileDialog(directory = os.path.expanduser("~"))
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        nameFilters = [SUPPORTED_EXTENSIONS[extension] for extension in SUPPORTED_EXTENSIONS]
        dlg.setNameFilters(nameFilters)
        dlg.selectNameFilter(SUPPORTED_EXTENSIONS[EXTENSION_DATA])
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            self.save_as_lineEdit.setText(name)
            self.setSaveAs()

    def errorWindow(self, exception):
        error_text = str(exception)
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        if type(exception) is abacus.exceptions.ExperimentError:
            self.stopClocks()
            self.cleanPort()
            self.experiment = None
            self.streaming = False
            self.acquisition_button.setDisabled(True)
            self.acquisition_button.setStyleSheet("background-color: red")
            msg.setIcon(QtWidgets.QMessageBox.Critical)

        try:
            self.results_files.writeParams("Error: %s"%error_text)
        except Exception:
            pass

        msg.setText('An Error has ocurred.\n%s'%error_text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec_()

    def closeEvent(self, event):
        if self.results_files == None:
            event.accept()
        elif self.results_files.areEmpty():
            event.accept()
        elif self.results_files.data_file.isEmpty():
            self.results_files.params_file.delete()
            event.accept()
        else:
            quit_msg = "Are you sure you want to exit the program?"
            reply = QtWidgets.QMessageBox.question(self, 'Exit',
                             quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

if __name__ == "__main__":
    from time import sleep

    app = QtWidgets.QApplication(sys.argv)
    splash_pix = QtGui.QPixmap(':/splash.png').scaledToWidth(600)
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()

    icon = QtGui.QIcon(':/abacus_small.ico')
    app.setWindowIcon(icon)
    app.processEvents()

    if abacus.CURRENT_OS == 'win32':
        import ctypes
        myappid = 'abacus.abacus.01' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    sleep(1)
    splash.close()

    main = Main()
    main.setWindowIcon(icon)
    main.show()
    sys.exit(app.exec_())
