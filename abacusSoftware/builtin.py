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
from PyQt5 import QtWidgets, QtGui, QtCore
from abacusSoftware.supportWidgets import ClickableLineEdit

class SweepDialogBase(QtWidgets.QDialog):
    def __init__(self, parent):
        super(SweepDialogBase, self).__init__(parent)
        self.resize(400, 500)

        self.parent = parent

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.frame = QtWidgets.QFrame()

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)

        label = QtWidgets.QLabel("Save as:")
        self.lineEdit = ClickableLineEdit(self)
        self.lineEdit.clicked.connect(self.chooseFile)

        self.horizontalLayout.addWidget(label)
        self.horizontalLayout.addWidget(self.lineEdit)
        self.verticalLayout.addWidget(self.frame)

        self.groupBox = QtWidgets.QGroupBox("Settings")

        self.formLayout = QtWidgets.QFormLayout(self.groupBox)

        samplingLabel = QtWidgets.QLabel("Sampling time:")
        coincidenceLabel = QtWidgets.QLabel("Coincidence Window:")

        startLabel = QtWidgets.QLabel("Start time (ns):")
        stopLabel = QtWidgets.QLabel("Stop time (ns):")
        stepLabel = QtWidgets.QLabel("Step size (ns):")
        nLabel = QtWidgets.QLabel("Number of measurements per step:")

        self.samplingLabel = QtWidgets.QLabel("")
        self.setSampling(0)
        self.coincidenceLabel = QtWidgets.QLabel("")
        self.setCoincidence(self.parent.coincidence_spinBox.value())
        self.startSpin = QtWidgets.QSpinBox()
        self.stopSpin = QtWidgets.QSpinBox()
        self.stepSpin = QtWidgets.QSpinBox()
        self.nSpin = QtWidgets.QSpinBox()
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

        self.startStopButton = QtWidgets.QPushButton("Start")
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
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(error_text)
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
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

        dlg = QtWidgets.QFileDialog(directory = directory)
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
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
        if ans == QtWidgets.QMessageBox.Ok:
            ans = True
        else: ans = False
        if ans: self.parent.startAcquisition()
        return ans

    def setSampling(self, val):
        self.samplingLabel.setText("%d (ms)"%val)

    def setCoincidence(self, val):
        self.coincidenceLabel.setText("%d ns"%val)

class DelayDialog(SweepDialogBase):
    def __init__(self, parent):
        super(DelayDialog, self).__init__(parent)

        self.setWindowTitle("Delay time sweep")

        self.startSpin.setMinimum(-abacus.constants.DELAY_MINIMUM_VALUE)
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

        self.plot.setLabel('left', "Coincidences")
        self.plot.setLabel('bottom', "Delay time", units='ns')

    def startStop(self):
        if self.startStopButton.text() == "Stop":
            self.timer.stop()
            self.completed = True
            self.updatePlot()
            self.completed = True

        else:
            step = self.stepSpin.value()
            n = self.nSpin.value()
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value(), step)
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
        self.completed = True
        # try:
        #     for (i, delay) in enumerate(range_):
        #         if not self.completed:
        #             if delay < 0:
        #                 delay1 = abs(delay)
        #                 delay2 = 0
        #             else:
        #                 delay1 = 0
        #                 delay2 = delay
        #
        #
        #             # result = self.parent.experiment.delaySweep("A", "B", delay1, delay2, n)
        #             # values = self.parent.experiment.delaySweep("A", "B", delay1, delay2, n)
        #             result = []
        #             for value in values:
        #                 result.append(value)
        #
        #             self.x_data.append(delay)
        #             self.y_data.append(np.mean(result))
        #         else:
        #             break
        #
        #     self.completed = True
        # except Exception as e:
        #     self.completed = True
        #     self.error = e

class SleepDialog(SweepDialogBase):
    def __init__(self, parent):
        super(SleepDialog, self).__init__(parent)

        self.parent = parent

        self.setWindowTitle("Sleep time sweep")

        label = QtWidgets.QLabel("Channel:")
        self.comboBox = QtWidgets.QComboBox()
        self.setNumberChannels(0)
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
            range_ = np.arange(self.startSpin.value(), self.stopSpin.value(), step)
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
        last_id = 0

        if port != None:
            try:
                for sleep in range_:
                    value = 0
                    abacus.setSetting(port, 'sleep_%s'%channel, sleep)
                    for j in range(n): # number of points
                        for i in range(10): # tries
                            if self.completed: return
                            try:
                                counters, id = abacus.getFollowingCounters(port, channel)
                                if id != last_id:
                                    last_id = id
                                    value += counters.getValue(channel)
                                    break
                                else:
                                    time_left = abacus.getTimeLeft(port) / 1000 # seconds
                                    time.sleep(time_left)

                            except abacus.BaseError as e:
                                if i == 9: raise(e)

                    self.x_data.append(sleep)
                    self.y_data.append(value / n)
                self.completed = True

            except Exception as e:
                self.completed = True
                self.error = e
                print(e)

    def setNumberChannels(self, number_channels):
        self.comboBox.clear()
        self.comboBox.addItems([chr(i + ord('A')) for i in range(number_channels)])
