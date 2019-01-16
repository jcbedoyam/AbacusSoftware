import os
import re
import sys
import webbrowser
import numpy as np
import abacusSoftware.__GUI_images__
import pyqtgraph as pg
from datetime import datetime
from itertools import combinations
from time import time, localtime, strftime
from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtWidgets import QLabel, QSpinBox, QComboBox, QSizePolicy
except ModuleNotFoundError:
    from PyQt4.QtGui import QLabel, QSpinBox, QComboBox, QSizePolicy

import abacusSoftware.constants as constants
import abacusSoftware.common as common
import abacusSoftware.builtin as builtin
import abacusSoftware.url as url
from abacusSoftware.menuBar import AboutWindow
from abacusSoftware.exceptions import ExtentionError
from abacusSoftware.files import ResultsFiles, RingBuffer
from abacusSoftware.supportWidgets import Table, CurrentLabels, ConnectDialog, \
                        SettingsDialog, SubWindow, ClickableLineEdit, Tabs, SamplingWidget

import pyAbacus as abacus

# if constants.CURRENT_OS == "win32":
#     import win_unicode_console
#     win_unicode_console.enable()

def getCombinations(n_channels):
    letters = [chr(i + ord('A')) for i in range(n_channels)]
    joined = "".join(letters)
    for i in range(2, n_channels + 1):
        letters += ["".join(pair) for pair in combinations(joined, i)]
    return letters

common.readConstantsFile()

class MainWindow(QtWidgets.QMainWindow):
    count = 0

    def __init__(self, parent = None):
        super(QtWidgets.QMainWindow, self).__init__(parent)
        self.port_name = None
        self.start_position = None
        self.number_channels = 0
        self.active_channels = []
        widget = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(widget)

        layout.setContentsMargins(11, 11, 11, 11)
        layout.setSpacing(6)

        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)

        horizontalLayout =  QtWidgets.QHBoxLayout(frame)
        label = QLabel("Save as:")

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

        frame3 = QtWidgets.QFrame()
        layout3 = QtWidgets.QHBoxLayout(frame3)
        layout.addWidget(frame3)

        toolbar_frame = QtWidgets.QFrame()
        toolbar_frame_layout = QtWidgets.QVBoxLayout(toolbar_frame)

        self.tabs_widget = Tabs(self)
        toolbar_frame_layout.addWidget(self.tabs_widget)
        toolbar_frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        toolbar_frame.setMaximumWidth(300)

        layout3.addWidget(toolbar_frame)
        layout3.setContentsMargins(0, 0, 0, 0)
        layout3.setSpacing(0)

        self.mdi = QtWidgets.QMdiArea(frame3)
        self.mdi.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        layout3.addWidget(self.mdi)
        self.setCentralWidget(widget)

        """
        settings
        """
        self.sampling_widget = None
        self.delay_widgets = []
        self.sleep_widgets = []
        self.subSettings_delays_sleeps = []

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
        self.streaming = False
        self.acquisition_button.clicked.connect(self.startAcquisition)

        self.connect_dialog = None
        self.connect_button.clicked.connect(self.connect)

        self.coincidence_spinBox.valueChanged.connect(self.coincidenceWindowMethod)

        """
        Plot
        """
        self.plot_lines = []
        self.legend = None
        self.counts_plot = self.plot_win.addPlot()
        self.counts_plot.setLabel('left', "Counts")
        self.counts_plot.setLabel('bottom', "Time", units='s')

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

        self.data_ring = None
        self.combinations = []
        self.combination_indexes = []
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

        # self.menuBuildInSweep.addAction(sleepSweep)
        # self.menuBuildInSweep.addAction(delaySweep)
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

        self.menuView.addAction(QtGui.QAction("Show settings", self.menubar, checkable = True))
        self.menuView.addAction(QtGui.QAction("Show historical", self.menubar, checkable = True))
        self.menuView.addAction(QtGui.QAction("Show current", self.menubar, checkable = True))
        self.menuView.addAction(QtGui.QAction("Show plots", self.menubar, checkable = True))
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
        self.setWindowTitle(constants.WINDOW_NAME)

        self.sleepSweepDialog = builtin.SleepDialog(self)
        self.delaySweepDialog = builtin.DelayDialog(self)

        self.mdi.tileSubWindows()
        self.mdi.cascadeSubWindows()

        self.setSettings()
        self.updateConstants()

    def centerOnScreen(self):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        x_0 = self.pos().x()
        y_0 = self.pos().y()
        sw = resolution.width()
        sh = resolution.height()
        fh = self.frameSize().height()
        y_o = (sh - fh) / 2
        self.move(sw / 2 - x_0, y_o)

    def handleViews(self, q):
        text = q.text()
        if "Show" in text:
            for action in self.menuView.actions():
                if text == action.text():
                    text = text[5:]
                    check = not action.isChecked()
                    subwindow = getattr(self, "subwindow_%s" % text)
                    if check:
                        action.setChecked(False)
                        print("here")
                        subwindow.hide()
                    else:
                        action.setChecked(True)
                        print("True")
                        subwindow.show()

        elif text == "Cascade":
            self.mdi.cascadeSubWindows()

        elif text == "Tiled":
            self.mdi.tileSubWindows()

    def sleepSweep(self):
        self.sleepSweepDialog.show()

    def delaySweep(self):
        self.delaySweepDialog.show()

    def subSettings(self, new = True):
        def fillFormLayout(layout, values, new = True):
            for (i, line) in enumerate(values):
                if not new: i += 2
                layout.setWidget(i, QtWidgets.QFormLayout.LabelRole, line[0])
                layout.setWidget(i, QtWidgets.QFormLayout.FieldRole, line[1])

        def deleteWidgets(layout, widgets):
            for label, widget in widgets:
                layout.removeWidget(label)
                layout.removeWidget(widget)
                label.deleteLater()
                widget.deleteLater()

        def createWidgets():
            delays = []
            sleeps = []
            self.delay_widgets = []
            self.sleep_widgets = []
            for i in range(self.number_channels):
                letter = self.getLetter(i)
                delay_label = 'delay_%s_label'%letter
                delay_spinBox = 'delay_%s_spinBox'%letter
                sleep_label = 'sleep_%s_label'%letter
                sleep_spinBox = 'sleep_%s_spinBox'%letter

                setattr(self, delay_label, QLabel("Delay %s (ns):"%letter))
                setattr(self, delay_spinBox, QSpinBox())
                setattr(self, sleep_label, QLabel("Sleep %s (ns):"%letter))
                setattr(self, sleep_spinBox, QSpinBox())

                getattr(self, delay_spinBox).setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                getattr(self, sleep_spinBox).setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                delays.append((getattr(self, delay_label), getattr(self, delay_spinBox)))
                sleeps.append((getattr(self, sleep_label), getattr(self, sleep_spinBox)))

                self.delay_widgets.append(getattr(self, delay_spinBox))
                self.sleep_widgets.append(getattr(self, sleep_spinBox))

            self.subSettings_delays_sleeps = delays + sleeps

            if self.number_channels == 2:
                self.delay_widgets[0].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[0], 'A', arg))
                self.delay_widgets[1].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[1], 'B', arg))
                self.sleep_widgets[0].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[0], 'A', arg))
                self.sleep_widgets[1].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[1], 'B', arg))
            elif self.number_channels == 4:
                self.delay_widgets[0].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[0], 'A', arg))
                self.delay_widgets[1].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[1], 'B', arg))
                self.delay_widgets[2].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[2], 'C', arg))
                self.delay_widgets[3].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[3], 'D', arg))
                self.sleep_widgets[0].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[0], 'A', arg))
                self.sleep_widgets[1].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[1], 'B', arg))
                self.sleep_widgets[2].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[2], 'C', arg))
                self.sleep_widgets[3].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[3], 'D', arg))
            elif self.number_channels == 8:
                self.delay_widgets[0].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[0], 'A', arg))
                self.delay_widgets[1].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[1], 'B', arg))
                self.delay_widgets[2].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[2], 'C', arg))
                self.delay_widgets[3].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[3], 'D', arg))
                self.delay_widgets[4].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[4], 'E', arg))
                self.delay_widgets[5].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[5], 'F', arg))
                self.delay_widgets[6].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[6], 'G', arg))
                self.delay_widgets[7].valueChanged.connect(lambda arg: self.delayMethod(self.delay_widgets[7], 'H', arg))
                self.sleep_widgets[0].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[0], 'A', arg))
                self.sleep_widgets[1].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[1], 'B', arg))
                self.sleep_widgets[2].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[2], 'C', arg))
                self.sleep_widgets[3].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[3], 'D', arg))
                self.sleep_widgets[4].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[4], 'E', arg))
                self.sleep_widgets[5].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[5], 'F', arg))
                self.sleep_widgets[6].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[6], 'G', arg))
                self.sleep_widgets[7].valueChanged.connect(lambda arg: self.sleepMethod(self.sleep_widgets[7], 'H', arg))

        if new:
            settings_frame = QtWidgets.QFrame()
            settings_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            settings_frame.setFrameShadow(QtWidgets.QFrame.Raised)
            settings_verticalLayout = QtWidgets.QVBoxLayout(settings_frame)
            settings_verticalLayout.setContentsMargins(11, 11, 11, 11)
            settings_verticalLayout.setSpacing(0)

            scrollArea = QtWidgets.QScrollArea()
            scrollArea.setWidgetResizable(True)

            self.settings_frame2 = QtWidgets.QFrame()
            self.settings_frame2.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.settings_frame2.setFrameShadow(QtWidgets.QFrame.Raised)

            settings_frame3 = QtWidgets.QFrame()

            self.settings_frame2_formLayout =  QtWidgets.QFormLayout(self.settings_frame2)
            settings_frame3_formLayout =  QtWidgets.QFormLayout(settings_frame3)

            scrollArea.setWidget(self.settings_frame2)

            self.sampling_label = QLabel("Sampling time:")
            self.sampling_widget = SamplingWidget(self.settings_frame2_formLayout, \
                                self.sampling_label, self.samplingMethod)
            self.coincidence_label = QLabel("Coincidence window (ns):")
            self.coincidence_spinBox = QSpinBox()
            self.coincidence_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            createWidgets()

            self.settings_frame2_formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.sampling_label)
            self.settings_frame2_formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.coincidence_label)
            self.settings_frame2_formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.coincidence_spinBox)

            self.unlock_settings_button = QtWidgets.QPushButton("Unlock settings")
            self.unlock_settings_button.clicked.connect(lambda: self.unlockSettings(True))

            # fillFormLayout(self.settings_frame2_formLayout, widgets)
            settings_frame3_formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.unlock_settings_button)

            settings_verticalLayout.addWidget(scrollArea)
            settings_verticalLayout.addWidget(settings_frame3)

            self.subwindow_settings = SubWindow(self)
            self.subwindow_settings.setWidget(settings_frame)
            self.subwindow_settings.setWindowTitle("Settings")

            self.settings_frame2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.mdi.addSubWindow(self.subwindow_settings)

        else:
            deleteWidgets(self.settings_frame2_formLayout, self.subSettings_delays_sleeps)
            createWidgets()
            fillFormLayout(self.settings_frame2_formLayout, self.subSettings_delays_sleeps, new = False)

        # createSampling()
        self.setSettings()

    def unlockSettings(self, unlock = True):
        self.sampling_widget.setEnabled(unlock)
        self.coincidence_spinBox.setEnabled(unlock)
        for widget in self.delay_widgets + self.sleep_widgets:
            widget.setEnabled(unlock)
        if unlock:
            self.unlock_settings_button.setEnabled(False)
        else:
            self.unlock_settings_button.setEnabled(True)

    def subHistorical(self):
        widget = QtWidgets.QWidget()
        self.historical_table = Table([], [])
        self.historical_layout = QtGui.QVBoxLayout(widget)
        self.historical_layout.addWidget(self.historical_table)

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

    def sendMultipleCoincidences(self, coincidences):
        if self.port_name != None:
            try:
                for (i, letters) in enumerate(coincidences):
                    abacus.setSetting(self.port_name, 'config_custom_c%d'%(i + 1), letters)
            except Exception as e:
                self.errorWindow(e)

    def sendSettings(self):
        self.samplingMethod(self.sampling_widget.getValue())
        self.coincidenceWindowMethod(self.coincidence_spinBox.value())

        for i in range(self.number_channels):
            letter = self.getLetter(i)
            delay_widget = self.delay_widgets[i]
            sleep_widget = self.sleep_widgets[i]
            self.delayMethod(delay_widget, letter, delay_widget.value())
            self.sleepMethod(sleep_widget, letter, sleep_widget.value())

    def samplingMethod(self, value, force_write = False):
        if self.sampling_widget != None:
            if force_write: self.sampling_widget.setValue(value)
            value = self.sampling_widget.getValue()
            if value > 0 and self.port_name != None:
                if value > constants.DATA_REFRESH_RATE: self.refresh_timer.setInterval(value)
                else: self.refresh_timer.setInterval(constants.DATA_REFRESH_RATE)
                self.data_timer.setInterval(value)
                try:
                    abacus.setSetting(self.port_name, 'sampling', value)
                    self.sampling_widget.valid()
                    if self.results_files != None:
                        self.results_files.writeParams("Sampling time (ms),%s"%value)
                except abacus.InvalidValueError:
                    self.sampling_widget.invalid()
                except abacus.BaseError as e:
                    self.errorWindow(e)
            else:
                print("Sampling Value, %d"%value)
        try:
            self.sleepSweepDialog.setSampling(value)
            self.delaySweepDialog.setSampling(value)
        except AttributeError: pass

    def coincidenceWindowMethod(self, val):
        text_value = "%d"%val
        if self.number_channels > 2:
            step = 10**int(np.log10(val) - 1)
            if step < 10: step = 5
            self.coincidence_spinBox.setSingleStep(step)
        if self.port_name != None:
            try:
                abacus.setSetting(self.port_name, 'coincidence_window', val)
                self.coincidence_spinBox.setStyleSheet("color: black")
                if self.results_files != None:
                    self.results_files.writeParams("Coincidence Window (ns), %s"%str(val))
            except abacus.InvalidValueError:
                self.coincidence_spinBox.setStyleSheet("color: red")
            except abacus.BaseError:
                self.errorWindow(e)
        else:
            print("Coincidence Window Value: %d"%val)
        try:
            self.sleepSweepDialog.setCoincidence(val)
            self.delaySweepDialog.setCoincidence(val)
        except AttributeError: pass

    def delayMethod(self, widget, letter, val):
        if self.port_name != None:
            try:
                abacus.setSetting(self.port_name, 'delay_%s'%letter, val)
                widget.setStyleSheet("color: black")
                if self.results_files != None:
                    self.results_files.writeParams("Delay A (ns), %s"%str(val))
            except abacus.InvalidValueError:
                widget.setStyleSheet("color: red")
            except abacus.BaseError as e:
                self.errorWindow(e)
        else:
            print("Delay %s Value: %d"%(letter, val))

    def sleepMethod(self, widget, letter, val):
        if self.port_name != None:
            try:
                abacus.setSetting(self.port_name, 'sleep_%s'%letter, val)
                if self.results_files != None:
                    self.results_files.writeParams("sleep A (ns), %s"%str(val))
            except abacus.InvalidValueError:
                widget.setStyleSheet("color: red")
            except abacus.BaseError as e:
                self.errorWindow(e)
        else:
            print("Sleep %s Value: %d"%(letter, val))

    def activeChannelsChanged(self, actives):
        self.active_channels = actives
        self.initPlots()
        self.current_labels.createLabels(self.active_channels)
        self.combination_indexes = [i for (i, com) in enumerate(self.combinations) if com in self.active_channels]

        "Clear table"
        self.historical_layout.removeWidget(self.historical_table)
        self.historical_table.deleteLater()

        "Create new table"
        self.historical_table = Table(self.active_channels, self.combination_indexes)
        self.historical_layout.addWidget(self.historical_table)

        self.updateWidgets()

    def getLetter(self, i):
        return chr(i + ord('A'))

    def checkParams(self):
        if self.port_name != None:
            try:
                settings = abacus.getAllSettings(self.port_name)
                samp = settings.getSetting("sampling")
                coin = settings.getSetting("coincidence_window")
                if self.number_channels == 4:
                    custom = settings.getSetting("config_custom_c1")
                    self.tabs_widget.setChecked(custom)
                elif self.number_channels == 8:
                    for i in range(8):
                        custom = settings.getSetting("config_custom_c%d"%(i + 1))
                        self.tabs_widget.setChecked(custom)

                if self.coincidence_spinBox.value() != coin:
                    self.coincidence_spinBox.setValue(coin)
                for i in range(self.number_channels):
                    letter = self.getLetter(i)
                    delay = self.delay_widgets[i]
                    sleep = self.sleep_widgets[i]
                    delay_new_val = settings.getSetting("delay_%s"%letter)
                    sleep_new_val = settings.getSetting("sleep_%s"%letter)
                    if delay.value() != delay_new_val:
                        delay.setValue(delay_new_val)
                    if sleep.value() != sleep_new_val:
                        sleep.setValue(sleep_new_val)

                if self.sampling_widget.getValue() != samp:
                    self.sampling_widget.setValue(samp)
            except abacus.BaseError as e:
                self.errorWindow(e)

    def setSettings(self):
        common.setCoincidenceSpinBox(self.coincidence_spinBox)
        for widget in self.delay_widgets:
            common.setDelaySpinBox(widget)
        for widget in self.sleep_widgets:
            common.setSleepSpinBox(widget)

    def cleanPort(self):
        if self.streaming:
            self.startAcquisition()

        if self.port_name != None:
            abacus.close(self.port_name)
            self.port_name = None
            self.setNumberChannels(0)
            self.subSettings(new = False)
            self.check_timer.stop()

    def setNumberChannels(self, n):
        self.number_channels = n
        self.tabs_widget.setNumberChannels(n)
        self.sampling_widget.changeNumberChannels(n)
        self.sleepSweepDialog.setNumberChannels(n)
        self.tabs_widget.signal()

    def connect(self):
        if self.port_name != None:
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
                abacus.open(self.port_name)
                n = abacus.getChannelsFromName(self.port_name)
                self.combinations = getCombinations(n)

                self.setNumberChannels(n)
                self.acquisition_button.setDisabled(False)
                self.acquisition_button.setStyleSheet("background-color: none")
                self.acquisition_button.setText("Start acquisition")
                self.connect_button.setText("Disconnect")

                self.subSettings(new = False)

                self.data_ring = RingBuffer(constants.BUFFER_ROWS, len(self.combinations) + 2, self.combinations)
                if self.results_files != None:
                    self.data_ring.setFile(self.results_files.data_file)

                self.updateConstants()
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
        if self.port_name == None:
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
        def get(counters, time_, id):
            last = -1
            if self.number_channels == 4: last = 10
            elif self.number_channels == 8: last = 36
            values = counters.getValues(self.combinations[:last])
            "could be better"
            i = 1
            for letters in self.combinations[last :]:
                if letters in self.active_channels:
                    val = counters.getValue("custom_c%d"%i)
                    i += 1
                else: val = 0
                values.append(val)

            values = np.array([time_, id] + values)
            values = values.reshape((1, values.shape[0]))
            self.data_ring.extend(values)
        try:
            if self.number_channels == 2:
                counters, id = abacus.getAllCounters(self.port_name)
            else:
                counters, id = abacus.getFollowingCounters(self.port_name, self.active_channels)

            time_ = time() - self.init_time
            data = self.data_ring[:]
            if len(data) == 0:
                get(counters, time_, id)
            elif data[-1, 1] != id:
                get(counters, time_, id)

        except abacus.BaseError as e:
            self.errorWindow(e)
        except FileNotFoundError as e:
            self.errorWindow(e)

    def updateWidgets(self):
        if self.data_ring != None:
            data = self.data_ring[:]
            if data.shape[0]:
                self.updatePlots(data)
                self.updateTable(data)
                self.updateCurrents(data)

    def updateTable(self, data):
        self.historical_table.insertData(data)

    def updateCurrents(self, data):
        for (pos, index) in enumerate(self.combination_indexes):
            self.current_labels.changeValue(pos, data[-1, index + 2])

    def updatePlots(self, data):
        time_ = data[:, 0]
        for (i, j) in enumerate(self.combination_indexes):
            self.plot_lines[i].setData(time_, data[:, j + 2])

    def removePlots(self):
        if self.legend != None:
            self.legend.scene().removeItem(self.legend)
        for line in self.plot_lines:
            line.clear()
        self.plot_lines = []
        self.legend = None

    def initPlots(self):
        self.removePlots()
        self.legend = self.counts_plot.addLegend()
        n = len(constants.COLORS)
        symbolSize = 5
        for i in range(len(self.active_channels)):
            color = constants.COLORS[i % n]
            letter = self.active_channels[i]
            plot = self.counts_plot.plot(pen = color, symbol='o',
                symbolPen = color, symbolBrush = color,
                symbolSize = symbolSize, name = letter)
            self.plot_lines.append(plot)

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
                    if self.data_ring != None:
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

            self.sampling_widget.setValue(constants.sampling_widget)
            self.sendSettings()

            if self.data_ring != None: self.data_ring.updateDelimiter(constants.DELIMITER)

        except AttributeError as e: pass

    def errorWindow(self, exception):
        error_text = str(exception)
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        if type(exception) is abacus.BaseError:
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
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        if self.results_files == None:
            if self.results_files.data_file.isEmpty():
                self.results_files.params_file.delete()

        # if self.results_files == None:
        #     event.accept()
        # elif self.results_files.areEmpty():
        #     event.accept()
        # elif self.results_files.data_file.isEmpty():
        #     temp = False
        #     if self.data_ring != None:
        #         if len(self.data_ring[:]) == 0: temp = True
        #     else: temp = True
        #     if temp:
        #         self.results_files.params_file.delete()
        #         event.accept()
        #     else:
        #         exit()
        # else:
        #     exit()
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Exit',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def initial(self):
        self.__sleep_timer__.stop()
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
    main.resize(800, 500)
    main.mdi.tileSubWindows()
    main.centerOnScreen()

    app.exec_()

if __name__ == "__main__":
    run()
    sys.exit()
