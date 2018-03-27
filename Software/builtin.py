import constants
import common
import PyAbacus as abacus

import numpy as np
import pyqtgraph as pg
from threading import Thread
from PyQt5 import QtWidgets, QtGui, QtCore
from supportWidgets import ClickableLineEdit

class SweepDialogBase(QtWidgets.QDialog):
    def __init__(self, parent):
        super(SweepDialogBase, self).__init__(parent)
        self.resize(400, 500)

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

        startLabel = QtWidgets.QLabel("Start time (ns):")
        stopLabel = QtWidgets.QLabel("Stop time (ns):")
        stepLabel = QtWidgets.QLabel("Step size (ns):")
        nLabel = QtWidgets.QLabel("Number of measurements per step:")

        self.startSpin = QtWidgets.QSpinBox()
        self.stopSpin = QtWidgets.QSpinBox()
        self.stepSpin = QtWidgets.QSpinBox()
        self.nSpin = QtWidgets.QSpinBox()
        self.nSpin.setMinimum(1)

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

    def updatePlot(self):
        if self.completed:
            self.x_data = []
            self.y_data = []
            self.timer.stop()
            self.completed = False
        else:
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

    def startStop(self):
        pass

class SleepDialog(SweepDialogBase):
    def __init__(self, parent):
        super(SleepDialog, self).__init__(parent)

        self.setWindowTitle("Sleep time sweep")

        self.plot.setLabel('left', "Counts")
        self.plot.setLabel('bottom', "Sleep time", units='ns')

class DelayDialog(SweepDialogBase):
    def __init__(self, parent):
        super(DelayDialog, self).__init__(parent)

        self.parent = parent

        self.setWindowTitle("Delay time sweep")

        label = QtWidgets.QLabel("Channel:")
        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.addItems(["A", "B"])

        self.formLayout.insertRow(0, label, self.comboBox)

        self.startSpin.setMinimum(abacus.MIN_DELAY)
        self.startSpin.setMaximum(abacus.MAX_DELAY)
        self.startSpin.setSingleStep(abacus.STEP_DELAY)
        self.startSpin.setValue(abacus.MIN_DELAY)

        self.stopSpin.setMinimum(abacus.MIN_DELAY)
        self.stopSpin.setMaximum(abacus.MAX_DELAY)
        self.stopSpin.setSingleStep(abacus.STEP_DELAY)
        self.stopSpin.setValue(abacus.MAX_DELAY)

        self.stepSpin.setMinimum(abacus.STEP_DELAY)
        self.stepSpin.setMaximum(((abacus.MAX_DELAY - abacus.MIN_DELAY) // abacus.STEP_DELAY) * abacus.STEP_DELAY)
        self.stepSpin.setSingleStep(abacus.STEP_DELAY)

        self.plot.setLabel('left', "Coincidences")
        self.plot.setLabel('bottom', "Delay time", units='ns')

    def startStop(self):
        step = self.stepSpin.value()
        n = self.nSpin.value()
        range_ = np.arange(self.startSpin.value(), self.stopSpin.value() + step, step)
        channel = self.comboBox.currentText()

        if self.parent.experiment != None:
            thread = Thread(target = self.heavyDuty, args = (channel, n, range_))
            thread.daemon = True
            thread.start()
            self.timer.start(0)

    def heavyDuty(self, channel, n, range_):
        self.startStopButton.setEnabled(False)
        try:
            for (i, delay) in enumerate(range_):
                result = self.parent.experiment.delaySweep(channel, delay, n)
                self.x_data.append(delay)
                self.y_data.append(result)

            self.completed = True
        except Exception as e:
            print(e)
        self.startStopButton.setEnabled(True)
