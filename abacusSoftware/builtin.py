import abacusSoftware.constants as constants
import abacusSoftware.common as common
# from abacusSoftware.supportWidgets import SamplingWidget
from abacusSoftware.files import File
import pyAbacus as abacus

import os
import time
import numpy as np
import pyqtgraph as pg
from threading import Thread
from abacusSoftware.supportWidgets import ClickableLineEdit

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtWidgets import QLabel, QSpinBox, QComboBox, QSizePolicy, \
                            QVBoxLayout, QHBoxLayout, QFrame, \
                            QPushButton, QDialog, QGroupBox, QFormLayout, QMessageBox,\
                            QFileDialog

except ModuleNotFoundError:
    from PyQt4.QtGui import QLabel, QSpinBox, QComboBox, QSizePolicy


class SweepDialogBase(QDialog):
    def __init__(self, parent):
        super(SweepDialogBase, self).__init__(parent)
        self.resize(400, 500)

        self.parent = parent

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.frame = QFrame()

        self.horizontalLayout = QVBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)

        label = QLabel("Save as:")
        self.lineEdit = ClickableLineEdit(self)
        self.lineEdit.clicked.connect(self.chooseFile)

        self.horizontalLayout.addWidget(label)
        self.horizontalLayout.addWidget(self.lineEdit)
        self.verticalLayout.addWidget(self.frame)

        self.groupBox = QGroupBox("Settings")

        self.formLayout = QFormLayout(self.groupBox)

        samplingLabel = QLabel("Sampling time:")
        coincidenceLabel = QLabel("Coincidence Window:")

        startLabel = QLabel("Start time (ns):")
        stopLabel = QLabel("Stop time (ns):")
        stepLabel = QLabel("Step size (ns):")
        nLabel = QLabel("Number of measurements per step:")

        self.samplingLabel = QLabel("")
        self.setSampling(0)
        self.coincidenceLabel = QLabel("")
        self.setCoincidence(self.parent.coincidence_spinBox.value())
        self.startSpin = QSpinBox()
        self.stopSpin = QSpinBox()
        self.stepSpin = QSpinBox()
        self.nSpin = QSpinBox()
        self.nSpin.setMinimum(1)

        self.startSpin.lineEdit().setReadOnly(True)
        self.stopSpin.lineEdit().setReadOnly(True)
        self.stepSpin.lineEdit().setReadOnly(True)

        self.samplingLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.coincidenceLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.startSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.stopSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.stepSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.nSpin.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.startSpin.valueChanged.connect(self.handleStart)

        self.formLayout.addRow(samplingLabel, self.samplingLabel)
        self.formLayout.addRow(coincidenceLabel, self.coincidenceLabel)
        self.formLayout.addRow(startLabel, self.startSpin)
        self.formLayout.addRow(stopLabel, self.stopSpin)
        self.formLayout.addRow(stepLabel, self.stepSpin)
        self.formLayout.addRow(nLabel, self.nSpin)

        self.verticalLayout.addWidget(self.groupBox)

        self.startStopButton = QPushButton("Start")
        self.startStopButton.setMaximumSize(QtCore.QSize(140, 60))
        self.verticalLayout.addWidget(self.startStopButton, alignment = QtCore.Qt.AlignRight)

        self.plot_win = pg.GraphicsWindow()
        self.plot = self.plot_win.addPlot()

        symbolSize = 5
        self.plot_line = self.plot.plot(pen = "r", symbol='o', symbolPen = "r", symbolBrush="r", symbolSize=symbolSize)
        self.verticalLayout.addWidget(self.plot_win)

        self.fileName = ""

        self.startStopButton.clicked.connect(self.startStop)

        self.x_data = []
        self.y_data = []

        self.completed = False

        self.timer = QtCore.QTimer()
        self.timer.setInterval(constants.CHECK_RATE)
        self.timer.timeout.connect(self.updatePlot)

        self.header = None

        self.error = None

    def handleStart(self, value):
        self.stopSpin.setMinimum(value + abacus.constants.DELAY_STEP_VALUE)

    def warning(self, error):
        error_text = str(error)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(error_text)
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg.exec_()

    def enableWidgets(self, enable):
        self.startSpin.setEnabled(enable)
        self.stopSpin.setEnabled(enable)
        self.stepSpin.setEnabled(enable)
        self.nSpin.setEnabled(enable)
        try:
            self.comboBox.setEnabled(enable)
        except:
            pass

    def updatePlot(self):
        self.plot_line.setData(self.x_data, self.y_data)
        if self.error != None:
            self.parent.errorWindow(self.error)
            self.error = None

        if self.completed:
            if self.fileName != "":
                file = File(self.fileName, self.header)
                data = np.vstack((self.x_data, self.y_data)).T
                file.npwrite(data, "%d" + constants.DELIMITER + "%d")

            self.x_data = []
            self.y_data = []
            self.timer.stop()
            self.completed = False
            self.startStopButton.setText("Start")
            self.startStopButton.setStyleSheet("background-color: none")
            self.enableWidgets(True)
            self.parent.check_timer.start()

    def cleanPlot(self):
        self.x_data = []
        self.y_data = []
        self.plot_line.setData(self.x_data, self.y_data)

    def chooseFile(self):
        try:
            directory = constants.directory_lineEdit
        except:
            directory = os.path.expanduser("~")

        dlg = QFileDialog(directory = directory)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setFileMode(QFileDialog.AnyFile)
        nameFilters = [constants.SUPPORTED_EXTENSIONS[extension] for extension in constants.SUPPORTED_EXTENSIONS]
        dlg.setNameFilters(nameFilters)
        dlg.selectNameFilter(constants.SUPPORTED_EXTENSIONS[constants.EXTENSION_DATA])
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            self.fileName = common.unicodePath(name)
            self.lineEdit.setText(self.fileName)

    def stopAcquisition(self):
        e = Exception("Data acquisition is active, in order to make the sweep it will be turned off.")
        ans = self.warning(e)
        if ans == QMessageBox.Ok:
            ans = True
        else: ans = False
        if ans: self.parent.startAcquisition()
        return ans

    def setSampling(self, val):
        self.samplingLabel.setText("%d (ms)"%val)

    def setCoincidence(self, val):
        self.coincidenceLabel.setText("%d ns"%val)

    def setDarkTheme(self):
        self.plot_win.setBackground((25, 35, 45))
        self.plot.getAxis('bottom').setPen(foreground = 'w')
        self.plot.getAxis('left').setPen(foreground = 'w')

    def setLightTheme(self):
        self.plot_win.setBackground(None)
        self.plot.getAxis('bottom').setPen()
        self.plot.getAxis('left').setPen()

class DelayDialog(SweepDialogBase):
    def __init__(self, parent):
        super(DelayDialog, self).__init__(parent)
        self.setWindowTitle("Delay time sweep")

        self.comboBox1 = QComboBox()
        self.comboBox2 = QComboBox()

        self.number_channels = 0

        self.comboBox1.setEditable(True)
        self.comboBox2.setEditable(True)
        self.comboBox1.lineEdit().setReadOnly(True)
        self.comboBox2.lineEdit().setReadOnly(True)
        self.comboBox1.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox2.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox1.currentIndexChanged.connect(self.channelsChange)
        self.comboBox2.currentIndexChanged.connect(self.channelsChange)

        self.setNumberChannels(4)

        self.formLayout.insertRow(0, QLabel("Channel 2:"), self.comboBox2)
        self.formLayout.insertRow(0, QLabel("Channel 1:"), self.comboBox1)

        self.startSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
        self.startSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_STEP_VALUE)
        self.startSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.startSpin.setValue(-abacus.constants.DELAY_MAXIMUM_VALUE)

        self.stopSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
        self.stopSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
        self.stopSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.stopSpin.setValue(abacus.constants.DELAY_MAXIMUM_VALUE)

        self.stepSpin.setMinimum(abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setMaximum(((abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_MINIMUM_VALUE) // abacus.constants.DELAY_STEP_VALUE) * abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
        self.stepSpin.setValue(abacus.constants.DELAY_STEP_VALUE) #new on v1.4.0 (2020-06-30)

        self.plot.setLabel('left', "Coincidences")
        self.plot.setLabel('bottom', "Delay time", units='ns')

    def channelsChange(self, index):
        i1 = self.comboBox1.currentIndex()
        i2 = self.comboBox2.currentIndex()
        if(i1 == i2):
            self.comboBox2.setCurrentIndex((i1 + 1) % self.number_channels)

    def createComboBox(self):
        self.comboBox2 = QComboBox()
        self.comboBox2.setEditable(True)
        self.comboBox2.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox2.lineEdit().setReadOnly(True)

        self.comboBox1.currentIndexChanged.connect(self.channelsChange)

    def startStop(self):
        if self.startStopButton.text() == "Stop":
            self.timer.stop()
            self.completed = True
            self.updatePlot()
            self.completed = True

        else:
            step = self.stepSpin.value()
            n = self.nSpin.value()
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value() + 1, step)
            range_ = range_[range_ <= abacus.constants.DELAY_MAXIMUM_VALUE]

            if self.parent.port_name != None:
                if self.parent.streaming:
                    if self.stopAcquisition():
                        self.run(n, range_)
                else:
                    self.run(n, range_)
            else:
                self.parent.connect()
                if self.parent.port_name != None:
                    if self.parent.streaming:
                        if self.stopAcquisition():
                            self.run(n, range_)
                    else:
                        self.run(n, range_)

    def run(self, n, range_):
        self.cleanPlot()
        self.completed = False
        self.startStopButton.setText("Stop")
        self.startStopButton.setStyleSheet("background-color: green")
        self.enableWidgets(False)

        self.header = "Delay time (ns)"  + constants.DELIMITER +  "Coincidences"

        self.parent.check_timer.stop()
        thread = Thread(target = self.heavyDuty, args = (n, range_))
        thread.daemon = True
        self.timer.start()
        thread.start()

    def heavyDuty(self, n, range_):
        port = self.parent.port_name
        channel1 = self.comboBox1.currentText()
        channel2 = self.comboBox2.currentText()
        if port != None:
            try:
                for delay in range_:
                    value = 0
                    last_id = 0
                    if delay > 0:
                        delay1 = 0
                        delay2 = delay
                    else:
                        delay1 = abs(delay)
                        delay2 = 0
                    delay1_ = -1
                    delay2_ = -1
                    for j in range(constants.NUMBER_OF_TRIES):
                        abacus.setSetting(port, "delay_%s" % channel1, delay1)
                        abacus.setSetting(port, "delay_%s" % channel2, delay2)
                        time.sleep(1e-3)
                        try:
                            delay1_ = abacus.getSetting(port, "delay_%s" % channel1)
                            delay2_ = abacus.getSetting(port, "delay_%s" % channel2)
                            if ((delay1 != delay1_) and (delay2 != delay2_)): break
                        except abacus.BaseError as e:
                            time.sleep(1e-2)
                            if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    time.sleep(self.parent.sampling_widget.getValue() / 1000)

                    for i in range(n):
                        for j in range(constants.NUMBER_OF_TRIES):
                            if self.completed: return
                            try:
                                counters, id = abacus.getFollowingCounters(port, [channel1 + channel2])
                                if (id != last_id) and (id != 0):
                                    value += counters.getValue(channel1 + channel2)
                                    last_id = id
                                    break
                                else:
                                    time_left = abacus.getTimeLeft(port) / 1000 # seconds
                                    time.sleep(time_left)

                            except abacus.BaseError as e:
                                if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    self.x_data.append(delay)
                    self.y_data.append(value / n)
                self.completed = True
            except Exception as e:
                self.completed = True
                self.error = e

    def setNumberChannels(self, number_channels):
        self.number_channels = number_channels
        self.comboBox1.blockSignals(True)
        self.comboBox2.blockSignals(True)
        self.comboBox1.clear()
        self.comboBox2.clear()
        self.comboBox1.addItems([chr(i + ord('A')) for i in range(number_channels)])
        self.comboBox2.addItems([chr(i + ord('A')) for i in range(number_channels)])

        self.comboBox2.setCurrentIndex(1)

        self.comboBox1.blockSignals(False)
        self.comboBox2.blockSignals(False)

    def updateConstants(self): #new on v1.4.0 (2020-06-30)
        try:
            self.startSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
            self.startSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_STEP_VALUE)
            self.startSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.startSpin.setValue(-abacus.constants.DELAY_MAXIMUM_VALUE)

            self.stopSpin.setMinimum(-abacus.constants.DELAY_MAXIMUM_VALUE)
            self.stopSpin.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
            self.stopSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.stopSpin.setValue(abacus.constants.DELAY_MAXIMUM_VALUE)

            self.stepSpin.setMinimum(abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setMaximum(((abacus.constants.DELAY_MAXIMUM_VALUE - abacus.constants.DELAY_MINIMUM_VALUE) // abacus.constants.DELAY_STEP_VALUE) * abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
            self.stepSpin.setValue(abacus.constants.DELAY_STEP_VALUE)
        except AttributeError as e:
            if abacus.constants.DEBUG: print(e)

class SleepDialog(SweepDialogBase):
    def __init__(self, parent):
        super(SleepDialog, self).__init__(parent)

        self.parent = parent

        self.setWindowTitle("Sleep time sweep")

        label = QLabel("Channel:")
        self.comboBox = QComboBox()
        self.comboBox.setEditable(True)
        self.comboBox.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.comboBox.lineEdit().setReadOnly(True)

        self.formLayout.insertRow(0, label, self.comboBox)

        self.startSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
        self.startSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_STEP_VALUE)
        self.startSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
        self.startSpin.setValue(abacus.constants.SLEEP_MINIMUM_VALUE)

        self.stopSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
        self.stopSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE)
        self.stopSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
        self.stopSpin.setValue(abacus.constants.SLEEP_MAXIMUM_VALUE)

        self.stepSpin.setMinimum(abacus.constants.SLEEP_STEP_VALUE)
        self.stepSpin.setMaximum(((abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_MINIMUM_VALUE) // abacus.constants.SLEEP_STEP_VALUE) * abacus.constants.SLEEP_STEP_VALUE)
        self.stepSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
        self.stepSpin.setValue(abacus.constants.SLEEP_STEP_VALUE) #new on v1.4.0 (2020-06-30)

        self.plot.setLabel('left', "Counts")
        self.plot.setLabel('bottom', "Sleep time", units='ns')

    def startStop(self):
        if self.startStopButton.text() == "Stop":
            self.timer.stop()
            self.completed = True
            self.updatePlot()
            self.completed = True

        else:
            step = self.stepSpin.value()
            n = self.nSpin.value()
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value() + 1, step)
            range_ = range_[range_ <= abacus.constants.SLEEP_MAXIMUM_VALUE]
            channel = self.comboBox.currentText()

            if self.parent.port_name != None:
                if self.parent.streaming:
                    if self.stopAcquisition():
                        self.run(channel, n, range_)
                else:
                    self.run(channel, n, range_)
            else:
                self.parent.connect()
                if self.parent.port_name!= None:
                    if self.parent.streaming:
                        if self.stopAcquisition():
                            self.run(channel, n, range_)
                    else:
                        self.run(channel, n, range_)

    def run(self, channel, n, range_):
        self.cleanPlot()
        self.completed = False
        self.startStopButton.setText("Stop")
        self.startStopButton.setStyleSheet("background-color: green")
        self.enableWidgets(False)

        self.header = "Sleep time (ns)"  + constants.DELIMITER +  "Counts (%s)"%channel

        self.parent.check_timer.stop()
        thread = Thread(target = self.heavyDuty, args = (channel, n, range_))
        thread.daemon = True
        self.timer.start()
        thread.start()

    def heavyDuty(self, channel, n, range_):
        port = self.parent.port_name
        if port != None:
            try:
                for sleep in range_:
                    value = 0
                    last_id = 0
                    sleep_ = -1
                    for j in range(constants.NUMBER_OF_TRIES):
                        try:
                            abacus.setSetting(port, 'sleep_%s' % channel, sleep)
                            time.sleep(1e-3)
                            sleep_ = abacus.getSetting(port, "sleep_%s" % channel)
                            if (sleep != sleep_): break
                        except abacus.BaseError as e:
                            time.sleep(1e-2)
                            if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    time.sleep(self.parent.sampling_widget.getValue() / 1000)

                    for i in range(n): # number of points
                        for j in range(constants.NUMBER_OF_TRIES): # tries
                            if self.completed: return
                            try:
                                counters, id = abacus.getFollowingCounters(port, [channel])
                                if (id != last_id) and (id != 0):
                                    last_id = id
                                    value += counters.getValue(channel)
                                    break
                                else:
                                    time_left = abacus.getTimeLeft(port) / 1000 # seconds
                                    time.sleep(time_left)

                            except abacus.BaseError as e:
                                if j == (constants.NUMBER_OF_TRIES - 1): raise(e)

                    self.x_data.append(sleep)
                    self.y_data.append(value / n)
                self.completed = True

            except Exception as e:
                self.completed = True
                self.error = e

    def setNumberChannels(self, number_channels):
        self.comboBox.clear()
        self.comboBox.addItems([chr(i + ord('A')) for i in range(number_channels)])

    def updateConstants(self): #new on v1.4.0 (2020-06-30)
        try:
            self.startSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
            self.startSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_STEP_VALUE)
            self.startSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
            self.startSpin.setValue(abacus.constants.SLEEP_MINIMUM_VALUE)

            self.stopSpin.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
            self.stopSpin.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE)
            self.stopSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
            self.stopSpin.setValue(abacus.constants.SLEEP_MAXIMUM_VALUE)

            self.stepSpin.setMinimum(abacus.constants.SLEEP_STEP_VALUE)
            self.stepSpin.setMaximum(((abacus.constants.SLEEP_MAXIMUM_VALUE - abacus.constants.SLEEP_MINIMUM_VALUE) // abacus.constants.SLEEP_STEP_VALUE) * abacus.constants.SLEEP_STEP_VALUE)
            self.stepSpin.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
            self.stepSpin.setValue(abacus.constants.SLEEP_STEP_VALUE) #new on v1.4.0 (2020-06-30)
        except AttributeError as e:
            if abacus.constants.DEBUG: print(e)
