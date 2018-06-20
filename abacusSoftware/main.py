import os
import re
import sys
import webbrowser
import numpy as np
import abacusSoftware.__GUI_images__
import pyqtgraph as pg
from datetime import datetime
from time import time, localtime, strftime
from PyQt5 import QtCore, QtGui, QtWidgets

import abacusSoftware.constants as constants
import abacusSoftware.common as common
import abacusSoftware.builtin as builtin
import abacusSoftware.url as url
from abacusSoftware.menuBar import AboutWindow
from abacusSoftware.exceptions import ExtentionError
from abacusSoftware.files import ResultsFiles, RingBuffer
from abacusSoftware.supportWidgets import Table, CurrentLabels, ConnectDialog, SettingsDialog, SubWindow, ClickableLineEdit

import pyAbacus as abacus
from pyAbacus.communication import findPorts, CommunicationPort

# if constants.CURRENT_OS == "win32":
#     import win_unicode_console
#     win_unicode_console.enable()

common.readConstantsFile()

class MainWindow(QtWidgets.QMainWindow):
    count = 0

    def __init__(self, parent = None):
        super(QtWidgets.QMainWindow, self).__init__(parent)
        widget = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(widget)

        layout.setContentsMargins(11, 11, 11, 11)
        layout.setSpacing(6)

        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)

        horizontalLayout =  QtWidgets.QHBoxLayout(frame)
        label = QtWidgets.QLabel("Save as:")

        self.save_as_lineEdit = ClickableLineEdit()
        self.save_as_lineEdit.clicked.connect(self.chooseFile)

        self.save_as_button = QtWidgets.QPushButton("Open")

        horizontalLayout.addWidget(label)
        horizontalLayout.addWidget(self.save_as_lineEdit)
        horizontalLayout.addWidget(self.save_as_button)

        layout.addWidget(frame)

        frame2 = QtWidgets.QFrame()
        layout2 = QtWidgets.QHBoxLayout(frame2)
        layout.setSpacing(0)

        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.connect_button)
        self.acquisition_button = QtWidgets.QPushButton("Start Acquisition")
        self.acquisition_button.setMaximumSize(QtCore.QSize(140, 60))
        layout2.addWidget(self.acquisition_button)
        layout.addWidget(frame2)

        self.mdi = QtWidgets.QMdiArea(widget)
        self.mdi.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.mdi)
        self.setCentralWidget(widget)

        """
        settings
        """
        self.subPlots()
        self.subwindow_plots.show()

        self.subHistorical()
        self.subwindow_historical.show()

        self.subCurrent()
        self.subwindow_current.show()

        self.subSettings()
        self.subwindow_settings.show()

        """
        Config
        """
        self.setSettings()
        self.updateConstants()

        self.port = None
        self.port_name = None
        self.streaming = False
        self.experiment = None
        self.acquisition_button.clicked.connect(self.startAcquisition)

        self.connect_dialog = None
        self.connect_button.clicked.connect(self.connect)

        self.sampling_comboBox.currentIndexChanged.connect(self.samplingMethod)
        self.coincidence_spinBox.valueChanged.connect(self.coincidenceWindowMethod)
        self.delayA_spinBox.valueChanged.connect(self.delayAMethod)
        self.delayB_spinBox.valueChanged.connect(self.delayBMethod)
        self.sleepA_spinBox.valueChanged.connect(self.sleepAMethod)
        self.sleepB_spinBox.valueChanged.connect(self.sleepBMethod)

        self.initPlots()
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(constants.DATA_REFRESH_RATE)
        self.refresh_timer.timeout.connect(self.updateWidgets)

        self.data_timer = QtCore.QTimer()
        self.data_timer.setInterval(constants.DATA_REFRESH_RATE)
        self.data_timer.timeout.connect(self.updateData)

        self.check_timer = QtCore.QTimer()
        self.check_timer.setInterval(constants.CHECK_RATE)
        self.check_timer.timeout.connect(self.checkParams)

        self.results_files = None
        self.params_buffer = ""
        self.init_time = 0
        self.init_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        self.data_ring = RingBuffer(constants.BUFFER_ROWS, 4)

        self.save_as_button.clicked.connect(self.chooseFile)
        self.save_as_lineEdit.returnPressed.connect(self.setSaveAs)

        self.unlockSettings(True)

        """
        MenuBar
        """
        self.menubar = self.menuBar()

        self.menuFile = self.menubar.addMenu("File")
        self.menuProperties = self.menubar.addMenu("Properties")
        self.menuBuildIn = self.menubar.addMenu("Built In")
        self.menuView = self.menubar.addMenu("View")
        self.menuHelp = self.menubar.addMenu("Help")

        self.menuBuildInSweep = QtGui.QMenu("Sweep")

        sleepSweep = QtWidgets.QAction('Sleep time', self)
        delaySweep = QtWidgets.QAction('Delay time', self)

        self.menuBuildInSweep.addAction(sleepSweep)
        self.menuBuildInSweep.addAction(delaySweep)
        sleepSweep.triggered.connect(self.sleepSweep)
        delaySweep.triggered.connect(self.delaySweep)

        self.menuBuildIn.addMenu(self.menuBuildInSweep)

        self.statusBar = QtWidgets.QStatusBar(self)
        self.statusBar.setObjectName("statusBar")
        self.setStatusBar(self.statusBar)

        self.actionAbout = QtWidgets.QAction('About', self)
        self.actionSave_as = QtWidgets.QAction('Save as', self)
        self.actionDefault_settings = QtWidgets.QAction('Default settings', self)
        self.actionExit = QtWidgets.QAction('Exit', self)

        self.menuFile.addAction(self.actionSave_as)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuHelp.addAction(self.actionAbout)
        self.menuProperties.addAction(self.actionDefault_settings)


        self.menuView.addAction(QtGui.QAction("Show settings", self.menubar, checkable=True))
        self.menuView.addAction(QtGui.QAction("Show historical", self.menubar, checkable=True))
        self.menuView.addAction(QtGui.QAction("Show current", self.menubar, checkable=True))
        self.menuView.addAction(QtGui.QAction("Show plots", self.menubar, checkable=True))
        self.menuView.addSeparator()
        self.menuView.addAction("Tiled")
        self.menuView.addAction("Cascade")

        for action in self.menuView.actions():
            if action.isCheckable(): action.setChecked(True)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuProperties.menuAction())
        self.menubar.addAction(self.menuBuildIn.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.menuView.triggered[QtWidgets.QAction].connect(self.handleViews)

        self.actionSave_as.triggered.connect(self.chooseFile)
        self.actionSave_as.setShortcut("Ctrl+S")
        self.actionDefault_settings.triggered.connect(self.settingsDialogCaller)

        self.actionAbout.triggered.connect(self.aboutWindowCaller)
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setShortcut("Ctrl+Q")

        self.acquisition_button.setDisabled(True)
        self.about_window = AboutWindow()
        self.settings_dialog = SettingsDialog(self)

        self.resize(800, 700)
        self.setWindowTitle(constants.WINDOW_NAME)
        self.showMaximized()

        # self.centerOnScreen()

        self.sleepSweepDialog = builtin.SleepDialog(self)
        self.delaySweepDialog = builtin.DelayDialog(self)

        self.mdi.tileSubWindows()
        # self.mdi.cascadeSubWindows()
        # self.subwindow_plots.resize(400, 350)

    def centerOnScreen(self):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        sw = resolution.width()
        fw = self.frameSize().width()
        print(sw, fw)
        self.move((sw - fw) / 2,
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

    def handleViews(self, q):
        text = q.text()
        if "Show" in text:
            for action in self.menuView.actions():
                if text == action.text():
                    text = text[5:]
                    check = not action.isChecked()
                    if check:
                        action.setChecked(False)
                        exec("self.subwindow_%s.hide()"%text)
                    else:
                        action.setChecked(True)
                        exec("self.subwindow_%s.show()"%text)

        elif text == "Cascade":
            self.mdi.cascadeSubWindows()

        elif text == "Tiled":
            self.mdi.tileSubWindows()

    def sleepSweep(self):
        self.sleepSweepDialog.show()

    def delaySweep(self):
        self.delaySweepDialog.show()

    def subSettings(self):
        def fillFormLayout(layout, values):
            for (i, line) in enumerate(values):
                layout.setWidget(i, QtWidgets.QFormLayout.LabelRole, line[0])
                layout.setWidget(i, QtWidgets.QFormLayout.FieldRole, line[1])

        settings_frame = QtWidgets.QFrame()
        settings_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        settings_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        settings_verticalLayout = QtWidgets.QVBoxLayout(settings_frame)
        settings_verticalLayout.setContentsMargins(11, 11, 11, 11)
        settings_verticalLayout.setSpacing(0)

        settings_frame2 = QtWidgets.QFrame()
        settings_frame2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        settings_frame2.setFrameShadow(QtWidgets.QFrame.Raised)

        settings_frame2_formLayout =  QtWidgets.QFormLayout(settings_frame2)

        self.sampling_label = QtWidgets.QLabel("Sampling time:")
        self.sampling_comboBox = QtWidgets.QComboBox()
        self.coincidence_label = QtWidgets.QLabel("Coincidence window (ns):")
        self.coincidence_spinBox = QtWidgets.QSpinBox()
        self.delayA_label = QtWidgets.QLabel("Delay A (ns):")
        self.delayA_spinBox = QtWidgets.QSpinBox()
        self.delayB_label = QtWidgets.QLabel("Delay B (ns):")
        self.delayB_spinBox = QtWidgets.QSpinBox()
        self.sleepA_label = QtWidgets.QLabel("Sleep time A (ns):")
        self.sleepA_spinBox = QtWidgets.QSpinBox()
        self.sleepB_label = QtWidgets.QLabel("Sleep time B (ns):")
        self.sleepB_spinBox = QtWidgets.QSpinBox()

        self.sampling_comboBox.setEditable(True)
        self.sampling_comboBox.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.sampling_comboBox.lineEdit().setReadOnly(True)

        self.coincidence_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.delayA_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.delayB_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.sleepA_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.sleepB_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        widgets = [(self.sampling_label, self.sampling_comboBox),
                    (self.coincidence_label, self.coincidence_spinBox),
                    (self.delayA_label, self.delayA_spinBox),
                    (self.delayB_label, self.delayB_spinBox),
                    (self.sleepA_label, self.sleepA_spinBox),
                    (self.sleepB_label, self.sleepB_spinBox),]

        fillFormLayout(settings_frame2_formLayout, widgets)

        self.unlock_settings_button = QtWidgets.QPushButton("Unlock settings")
        self.unlock_settings_button.clicked.connect(lambda: self.unlockSettings(True))
        settings_frame2_formLayout.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.unlock_settings_button)

        # settings_verticalLayout.addWidget(settings_frame3)
        settings_verticalLayout.addWidget(settings_frame2)

        # self.subwindow_settings = QtWidgets.QMdiSubWindow(self.mdi)
        self.subwindow_settings = SubWindow(self)
        self.subwindow_settings.setWidget(settings_frame)
        self.subwindow_settings.setWindowTitle("Settings")

        # self.subwindow_settings
        self.mdi.addSubWindow(self.subwindow_settings)

        self.setSettings()

    def unlockSettings(self, unlock = True):
        self.sampling_comboBox.setEnabled(unlock)
        self.coincidence_spinBox.setEnabled(unlock)
        self.delayA_spinBox.setEnabled(unlock)
        self.delayB_spinBox.setEnabled(unlock)
        self.sleepA_spinBox.setEnabled(unlock)
        self.sleepB_spinBox.setEnabled(unlock)
        if unlock:
            self.unlock_settings_button.setEnabled(False)
        else:
            self.unlock_settings_button.setEnabled(True)

    def subHistorical(self):
        widget = QtWidgets.QWidget()
        self.historical_table = Table(4)
        historical_layout = QtGui.QVBoxLayout(widget)
        historical_layout.addWidget(self.historical_table)

        self.subwindow_historical = SubWindow(self)
        self.subwindow_historical.setWidget(widget)
        self.subwindow_historical.setWindowTitle("Historical")
        self.mdi.addSubWindow(self.subwindow_historical)

    def subCurrent(self):
        widget = QtWidgets.QWidget()
        self.current_labels = CurrentLabels(widget)

        self.subwindow_current = SubWindow(self)
        self.subwindow_current.setMinimumSize(200, 100)
        self.subwindow_current.setWidget(widget)
        self.subwindow_current.setWindowTitle("Current")
        self.mdi.addSubWindow(self.subwindow_current)

    def subPlots(self):
        pg.setConfigOptions(foreground = 'k', background = None, antialias = True)
        self.plot_win = pg.GraphicsWindow()

        self.subwindow_plots = SubWindow(self)
        self.subwindow_plots.setWidget(self.plot_win)
        self.subwindow_plots.setWindowTitle("Plots")
        self.mdi.addSubWindow(self.subwindow_plots)

    def aboutWindowCaller(self):
        self.about_window.show()

    def settingsDialogCaller(self):
        self.settings_dialog.show()

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
        self.delayAMethod(self.delayA_spinBox.value())
        self.delayBMethod(self.delayB_spinBox.value())
        self.sleepAMethod(self.sleepA_spinBox.value())
        self.sleepBMethod(self.sleepB_spinBox.value())

    def samplingMethod(self, index):
        text_value = self.sampling_comboBox.currentText()
        value = common.timeInUnitsToMs(text_value)
        if value > 0 and self.experiment != None:
            if value > constants.DATA_REFRESH_RATE:
                self.refresh_timer.setInterval(value)
            else:
                self.refresh_timer.setInterval(constants.DATA_REFRESH_RATE)

            self.data_timer.setInterval(value)
            if self.results_files != None:
                self.results_files.writeParams("Sampling time (ms),%s"%value)
            try:
                self.experiment.setSampling(value)
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)

            self.sleepSweepDialog.samplingLabel.setText(text_value)
            self.delaySweepDialog.samplingLabel.setText(text_value)
        else:
            print("Sampling Value, %d"%value)

    def coincidenceWindowMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.setCoinWindow(val)
                if self.results_files != None:
                    self.results_files.writeParams("Coincidence Window (ns), %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Coincidence Window Value: %d"%val)

    def delayAMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[0].setDelay(val)
                if self.results_files != None:
                    self.results_files.writeParams("Delay A (ns), %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Delay A Value: %d"%val)

    def delayBMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[1].setDelay(val)
                if self.results_files != None:
                    self.results_files.writeParams("Delay B (ns), %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Delay B Value: %d"%val)

    def sleepAMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[0].setSleep(val)
                if self.results_files != None:
                    self.results_files.writeParams("Sleep A (ns), %s"%str(val))
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)
        else:
            print("Sleep A Value: %d"%val)

    def sleepBMethod(self, val):
        if self.experiment != None:
            try:
                self.experiment.detectors[1].setSleep(val)
                if self.results_files != None:
                    self.results_files.writeParams("Sleep B (ns), %s"%str(val))
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

                if common.timeInUnitsToMs(self.sampling_comboBox.currentText()) != samp:
                    if samp >= 1000:
                        index = self.sampling_comboBox.findText('%d s'%(samp/1000))
                    else:
                        index = self.sampling_comboBox.findText('%d ms'%samp)
                    self.sampling_comboBox.setCurrentIndex(index)
                if self.coincidence_spinBox.value() != coin:
                    self.coincidence_spinBox.setValue(coin)
                if self.delayA_spinBox.value() != dA:
                    self.delayA_spinBox.setValue(dA)
                if self.delayB_spinBox.value() != dB:
                    self.delayB_spinBox.setValue(dB)
                if self.sleepA_spinBox.value() != sA:
                    self.sleepA_spinBox.setValue(sA)
                if self.sleepB_spinBox.value() != sB:
                    self.sleepB_spinBox.setValue(sB)
            except abacus.exceptions.ExperimentError as e:
                self.errorWindow(e)

    def unlockSettings(self, unlock = True):
        self.sampling_comboBox.setEnabled(unlock)
        self.coincidence_spinBox.setEnabled(unlock)
        self.delayA_spinBox.setEnabled(unlock)
        self.delayB_spinBox.setEnabled(unlock)
        self.sleepA_spinBox.setEnabled(unlock)
        self.sleepB_spinBox.setEnabled(unlock)
        if unlock:
            self.unlock_settings_button.setEnabled(False)
        else:
            self.unlock_settings_button.setEnabled(True)

    def setSettings(self):
        common.setSamplingComboBox(self.sampling_comboBox)
        common.setCoincidenceSpinBox(self.coincidence_spinBox)
        common.setDelaySpinBox(self.delayA_spinBox)
        common.setDelaySpinBox(self.delayB_spinBox)
        common.setSleepSpinBox(self.sleepA_spinBox)
        common.setSleepSpinBox(self.sleepB_spinBox)

    def cleanPort(self):
        if self.streaming:
            self.startAcquisition()

        if self.port != None:
            self.port.close()
            self.port_name = None
            self.port = None

        if self.experiment != None:
            self.check_timer.stop()
            self.experiment = None

    def connect(self):
        if self.port != None:
            self.connect_button.setText("Connect")
            self.acquisition_button.setDisabled(True)
            if self.results_files != None:
                self.results_files.writeParams("Disconnected from device in port,%s"%self.port_name)
            self.cleanPort()
        else:
            self.connect_dialog = ConnectDialog()
            self.connect_dialog.refresh()
            self.connect_dialog.exec_()

            port = self.connect_dialog.comboBox.currentText()

            if port != "":
                self.port_name = port
                self.port = CommunicationPort(self.connect_dialog.ports[self.port_name])
                self.experiment = abacus.Experiment(self.port)

                self.acquisition_button.setDisabled(False)
                self.acquisition_button.setStyleSheet("background-color: none")
                self.acquisition_button.setText("Start acquisition")
                self.connect_button.setText("Disconnect")

                if len(self.current_labels.labels) == 0:
                    self.current_labels.createLabels()
                    self.current_labels.setColors(["red", "blue", "black"])
                # self.checkParams()
                self.check_timer.start()

                msg = "Connected to device in port,%s"%self.port_name
                if self.results_files != None:
                    try:
                        self.results_files.writeParams(msg)
                    except FileNotFoundError as e:
                        self.errorWindow(e)
                else:
                    self.params_buffer += constants.BREAKLINE + strftime("%H:%M:%S", localtime()) + "," + msg

            else:
                self.connect_button.setText("Connect")
                self.acquisition_button.setDisabled(True)

    def startClocks(self):
        self.refresh_timer.start()
        self.data_timer.start()

    def stopClocks(self):
        self.refresh_timer.stop()
        self.data_timer.stop()
        try:
            self.data_ring.save()
        except FileNotFoundError as e:
            self.errorWindow(e)

    def startAcquisition(self):
        if self.port == None:
            QtWidgets.QMessageBox.warning(self, 'Error', "Port has not been choosed", QtWidgets.QMessageBox.Ok)
        elif self.results_files != None:
            if self.streaming:
                self.acquisition_button.setStyleSheet("background-color: none")
                self.acquisition_button.setText("Start acquisition")
                self.results_files.writeParams("Acquisition stopped")
                self.unlockSettings()
                self.stopClocks()
            else:
                self.acquisition_button.setStyleSheet("background-color: green")
                self.acquisition_button.setText("Stop acquisition")
                self.results_files.writeParams("Acquisition started")
                self.sendSettings()
                self.unlockSettings(False)
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
        except FileNotFoundError as e:
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
        self.counts_plot = self.plot_win.addPlot()
        self.coins_plot = self.plot_win.addPlot(row = 1, col = 0)

        self.counts_plot.addLegend()
        self.coins_plot.addLegend()

        symbolSize = 5
        self.countsA_line = self.counts_plot.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize, name="Detector A")
        self.countsB_line = self.counts_plot.plot(pen = "b", symbol='o', symbolPen = "b", symbolBrush="b", symbolSize=symbolSize, name="Detector B")

        self.coins_line = self.coins_plot.plot(pen = "k", symbol='o', symbolPen = "k", symbolBrush="k", symbolSize=symbolSize, name="Coincidences AB")

        self.counts_plot.setLabel('left', "Counts")
        self.coins_plot.setLabel('left', "Coincidences")
        self.coins_plot.setLabel('bottom', "Time", units='s')

    def setSaveAs(self):
        new_file_name = self.save_as_lineEdit.text()
        try:
            if new_file_name != "":
                try:
                    name, ext = self.checkFileName(new_file_name)
                    if self.results_files == None:
                        self.results_files = ResultsFiles(name, ext, self.init_date)
                        self.results_files.params_file.header += self.params_buffer
                        self.params_buffer = ""
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
        except FileNotFoundError as e:
            self.errorWindow(e)

    def checkFileName(self, name):
        if "." in name:
            name, ext = name.split(".")
            ext = ".%s"%ext
        else:
            try:
                ext = constants.extension_comboBox
                print(ext)
            except AttributeError:
                ext = constants.EXTENSION_DATA
            name = common.unicodePath(name)
            self.save_as_lineEdit.setText(name + ext)
        if ext in constants.SUPPORTED_EXTENSIONS.keys():
            return name, ext
        else:
            raise ExtentionError()

    def chooseFile(self):
        """
        user interaction with saving file
        """
        try:
            directory = constants.directory_lineEdit
        except:
            directory = os.path.expanduser("~")

        dlg = QtWidgets.QFileDialog(directory = directory)
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        nameFilters = [constants.SUPPORTED_EXTENSIONS[extension] for extension in constants.SUPPORTED_EXTENSIONS]
        dlg.setNameFilters(nameFilters)
        dlg.selectNameFilter(constants.SUPPORTED_EXTENSIONS[constants.EXTENSION_DATA])
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            self.save_as_lineEdit.setText(common.unicodePath(name))
            self.setSaveAs()

    def updateConstants(self):
        try:
            common.updateConstants(self)

            if constants.autogenerate_checkBox:
                file_name = constants.file_prefix_lineEdit
                if constants.datetime_checkBox: file_name += strftime("_%Y%m%d_%H%M")
                file_name += constants.extension_comboBox
                path = os.path.join(constants.directory_lineEdit, file_name)
                self.save_as_lineEdit.setText(common.unicodePath(path))
                self.setSaveAs()

            self.data_ring.updateFormat(delimiter = constants.DELIMITER)

        except AttributeError:
            pass

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
            self.connect_button.setText("Connect")

        try:
            self.results_files.writeParams("Error,%s"%error_text)
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

    def initial(self):
        self.__sleep_timer__.stop()
        # self.softwareUpdate()
        self.connect()

    def show2(self):
        self.show()

        self.__sleep_timer__ = QtCore.QTimer()
        self.__sleep_timer__.setInterval(10)
        self.__sleep_timer__.timeout.connect(self.initial)
        self.__sleep_timer__.start()

def softwareUpdate(splash):
    try:
        check = constants.check_updates_checkBox
    except:
        if constants.SETTING_FILE_EXISTS:
            os.remove(constants.SETTINGS_PATH)
        check = True
    if check:
        version = url.checkUpdate()
        if version != None:
            splash.close()
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("There is a new version avaible (%s).\nDo you want to download it?"%version)
            msg.setWindowTitle("Update avaible")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if msg.exec_() == QtWidgets.QMessageBox.Yes:
                webbrowser.open(url.TARGET_URL)
                exit()

def run():
    from time import sleep

    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Fusion')) # <- Choose the style

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

    softwareUpdate(splash)
    splash.close()

    main = MainWindow()
    main.setWindowIcon(icon)

    main.show2()
    app.exec_()

if __name__ == "__main__":
    run()
    sys.exit()
