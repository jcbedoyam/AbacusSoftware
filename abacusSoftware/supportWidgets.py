import os
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QTableWidgetItem
from pyAbacus.constants import CURRENT_OS

import abacusSoftware.common as common
import abacusSoftware.constants as constants
from pyAbacus.communication import findPorts

class Table(QtWidgets.QTableWidget):
    def __init__(self, cols):
        QtWidgets.QTableWidget.__init__(self)
        self.setColumnCount(cols)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.verticalHeader().setDefaultSectionSize(18)
        self.verticalHeader().setMinimumSectionSize(18)
        self.verticalHeader().setSortIndicatorShown(False)

        self.last_time = None

        self.headers = ['time (s)', 'A', 'B', 'AB']
        self.setHorizontalHeaderLabels(self.headers)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True);

    def insertData(self, data):
        rows, cols = data.shape

        if self.last_time == None:
            self.last_time = data[0, 0]
            index = 0
        else:
            index = np.where(data[:, 0] == self.last_time)[0][0]
            self.last_time = data[-1, 0]
            data = data[index + 1:]

        for i in range(data.shape[0]):
            self.insertRow(0)
            for j in range(cols):
                if j == 0:
                    fmt = "%.3f"
                else:
                    fmt = "%d"
                self.setItem(0, j, QTableWidgetItem(fmt%data[i, j]))
                self.item(0, j).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

class AutoSizeLabel(QtWidgets.QLabel):
    """ From reclosedev at http://stackoverflow.com/questions/8796380/automatically-resizing-label-text-in-qt-strange-behaviour
    and Jean-Sébastien http://stackoverflow.com/questions/29852498/syncing-label-fontsize-with-layout-in-pyqt
    """
    MAX_DIGITS = 7 #: Maximum number of digits of a number in label.
    MAX_CHARS = 9 + MAX_DIGITS #: Maximum number of letters in a label.
    global CURRENT_OS
    def __init__(self, text, value):
        QtWidgets.QLabel.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.font_name = "Monospace"
        if CURRENT_OS == "win32":
            self.font_name = "Courier New"
        self.setFont(QtGui.QFont(self.font_name))
        self.initial_font_size = 10
        self.font_size = 10
        self.MAX_TRY = 150
        self.height = self.contentsRect().height()
        self.width = self.contentsRect().width()
        self.name = text
        self.value = value
        self.setText(self.stylishText(text, value))
        self.setFontSize(self.font_size)

    def setFontSize(self, size):
        """ Changes the size of the font to `size` """
        f = self.font()
        f.setPixelSize(size)
        self.setFont(f)

    def setColor(self, color):
        """ Sets the font color.
        Args:
            color (string): six digit hexadecimal color representation.
        """
        self.setStyleSheet('color: %s'%color)

    def stylishText(self, text, value):
        """ Uses and incomning `text` and `value` to create and text of length
        `MAX_CHARS`, filled with spaces.
        Returns:
            string: text of length `MAX_CHARS`.
        """
        n_text = len(text)
        n_value = len(value)
        N = n_text + n_value
        spaces = [" " for i in range(self.MAX_CHARS - N-1)]
        spaces = "".join(spaces)
        text = "%s: %s%s"%(text, spaces, value)
        return text

    def changeValue(self, value):
        """ Sets the text in label with its name and its value. """
        if type(value) is not str:
            value = "%d"%value
        if self.value != value:
            self.value = value
            self.setText(self.stylishText(self.name, self.value))

    def resize(self):
        """ Finds the best font size to use if the size of the window changes. """
        f = self.font()
        cr = self.contentsRect()
        height = cr.height()
        width = cr.width()
        if abs(height*width - self.height*self.width) > 1:
            self.font_size = self.initial_font_size
            for i in range(self.MAX_TRY):
                f.setPixelSize(self.font_size)
                br =  QtGui.QFontMetrics(f).boundingRect(self.text())
                if br.height() <= cr.height() and br.width() <= cr.width():
                    self.font_size += 1
                else:
                    if CURRENT_OS == 'win32':
                        self.font_size += -1

                    else:
                        self.font_size += -2
                    f.setPixelSize(max(self.font_size, 1))
                    break
            self.setFont(f)
            self.height = height
            self.width = width

class CurrentLabels(QtWidgets.QWidget):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.installEventFilter(self)
        self.labels = []

    def createLabels(self, labels=["counts A", "counts B", "coinc AB"]):
        for name in labels:
            label = AutoSizeLabel(name, "0")
            self.layout.addWidget(label)
            self.labels.append(label)

    # def createLabels(self, detectors, coincidences):
    #     for detector in detectors:
    #         name = detector.name
    #         label = AutoSizeLabel(name, "0")
    #         self.layout.addWidget(label)
    #         self.labels.append(label)
    #
    #     for coin in coincidences:
    #         name = coin.name
    #         label = AutoSizeLabel(name, "0")
    #         self.layout.addWidget(label)
    #         self.labels.append(label)

    def setColor(self, label, color):
        label.setColor(color)

    def setColors(self, colors):
        for (label, color) in zip(self.labels, colors):
            self.setColor(label, color)

    def changeValue(self, index, value):
        self.labels[index].changeValue(value)

    def eventFilter(self, object, evt):
        """ Checks if there is the window size has changed.
        Returns:
            boolean: True if it has not changed. False otherwise. """
        ty = evt.type()
        if ty == 97: # DONT KNOW WHY
            self.resizeEvent(evt)
            return False
        elif ty == 12:
            self.resizeEvent(evt)
            return False
        else:
            return True

    def resizeEvent(self, evt):
        sizes = [None]*3
        try:
            for (i, label) in enumerate(self.labels):
                label.resize()
                sizes[i] = label.font_size

            if len(self.labels) > 0:
                size = max(sizes)
                for label in self.labels:
                    label.setFontSize(size)
        except Exception as e:
            print(e)

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

        self.label.setText(constants.CONNECT_LABEL)
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
            self.label.setText(constants.CONNECT_EMPTY_LABEL)
        else:
            self.label.setText(constants.CONNECT_LABEL)
        self.comboBox.addItems(ports_names)
        self.adjustSize()

    def clear(self):
        self.comboBox.clear()

    def reject2(self):
        self.clear()
        self.reject()

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self)
        # self.setWindowFlags(QtCore.Qt.WindowSystemMenuHint  | QtCore.Qt.WindowTitleHint)

        self.parent = parent
        self.setWindowTitle("Default settings")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.tabWidget = QtWidgets.QTabWidget(self)

        self.file_tab = QtWidgets.QWidget()
        self.settings_tab = QtWidgets.QWidget()

        self.tabWidget.addTab(self.file_tab, "File")
        self.tabWidget.addTab(self.settings_tab, "Settings")

        self.verticalLayout.addWidget(self.tabWidget)

        """
        file tab
        """
        self.file_tab_verticalLayout = QtWidgets.QVBoxLayout(self.file_tab)

        # frame1
        self.file_tab_frame1 = QtWidgets.QFrame()
        self.file_tab_frame1_layout = QtWidgets.QHBoxLayout(self.file_tab_frame1)

        self.directory_label = QtWidgets.QLabel("Directory:")
        self.directory_lineEdit = ClickableLineEdit()
        self.directory_pushButton = QtWidgets.QPushButton("Open")

        self.file_tab_frame1_layout.addWidget(self.directory_label)
        self.file_tab_frame1_layout.addWidget(self.directory_lineEdit)
        self.file_tab_frame1_layout.addWidget(self.directory_pushButton)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame1)
        self.directory_lineEdit.clicked.connect(self.chooseFolder)
        self.directory_pushButton.clicked.connect(self.chooseFolder)

        # frame2
        self.file_tab_frame2 = QtWidgets.QFrame()
        self.file_tab_frame2_layout = QtWidgets.QFormLayout(self.file_tab_frame2)

        self.file_prefix_label = QtWidgets.QLabel("File prefix:")
        self.file_prefix_lineEdit = QtWidgets.QLineEdit()
        self.extension_label = QtWidgets.QLabel("Extension:")
        self.extension_comboBox = QtWidgets.QComboBox()
        self.delimiter_label = QtWidgets.QLabel("Delimiter:")
        self.delimiter_comboBox = QtWidgets.QComboBox()
        self.parameters_label = QtWidgets.QLabel("Parameters suffix:")
        self.parameters_lineEdit = QtWidgets.QLineEdit()
        self.autogenerate_label = QtWidgets.QLabel("Autogenerate file name:")
        self.autogenerate_checkBox = QtWidgets.QCheckBox()
        self.check_updates_label = QtWidgets.QLabel("Check for updates:")
        self.check_updates_checkBox = QtWidgets.QCheckBox()
        self.datetime_label = QtWidgets.QLabel("Use datetime:")
        self.datetime_checkBox = QtWidgets.QCheckBox()

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        widgets = [(self.check_updates_label, self.check_updates_checkBox),
                    (self.autogenerate_label, self.autogenerate_checkBox),
                    (self.datetime_label, self.datetime_checkBox),
                    (self.file_prefix_label, self.file_prefix_lineEdit),
                    (self.parameters_label, self.parameters_lineEdit),
                    (self.extension_label, self.extension_comboBox),
                    (self.delimiter_label, self.delimiter_comboBox),
                    ]

        self.fillFormLayout(self.file_tab_frame2_layout, widgets)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        self.autogenerate_checkBox.setCheckState(2)
        self.check_updates_checkBox.setCheckState(2)
        self.autogenerate_checkBox.stateChanged.connect(self.actogenerateMethod)
        self.datetime_checkBox.setCheckState(2)
        self.parameters_lineEdit.setText(constants.PARAMS_SUFFIX)
        self.file_prefix_lineEdit.setText(constants.FILE_PREFIX)
        self.directory_lineEdit.setText(common.findDocuments())
        self.delimiter_comboBox.insertItems(0, constants.DELIMITERS)
        self.extension_comboBox.insertItems(0, sorted(constants.SUPPORTED_EXTENSIONS.keys())[::-1])

        """
        settings tab
        """
        self.settings_tab_verticalLayout = QtWidgets.QVBoxLayout(self.settings_tab)

        self.settings_tab_frame = QtWidgets.QFrame()
        self.settings_tab_frame_layout = QtWidgets.QFormLayout(self.settings_tab_frame)

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
                    # (self.from_device_label, self.from_device_checkBox)]

        self.fillFormLayout(self.settings_tab_frame_layout, widgets)

        self.settings_tab_verticalLayout.addWidget(self.settings_tab_frame)

        common.setSamplingComboBox(self.sampling_comboBox)
        common.setCoincidenceSpinBox(self.coincidence_spinBox)
        common.setDelaySpinBox(self.delayA_spinBox)
        common.setDelaySpinBox(self.delayB_spinBox)
        common.setSleepSpinBox(self.sleepA_spinBox)
        common.setSleepSpinBox(self.sleepB_spinBox)

        """
        buttons
        """
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setText("Apply")
        self.buttons.accepted.connect(self.accept_replace)
        self.buttons.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttons)

        self.setConstants()
        self.constantsWriter()

    def actogenerateMethod(self, val):
        self.datetime_checkBox.setEnabled(val)
        self.file_prefix_lineEdit.setEnabled(val)

    def fillFormLayout(self, layout, values):
        for (i, line) in enumerate(values):
            layout.setWidget(i, QtWidgets.QFormLayout.LabelRole, line[0])
            layout.setWidget(i, QtWidgets.QFormLayout.FieldRole, line[1])

    def constantsWriter(self):
        lines = []
        for (widget, eval_) in zip(constants.WIDGETS_NAMES, constants.WIDGETS_GET_ACTIONS):
            complete = common.findWidgets(self, widget)
            for item in complete:
                val = eval(eval_%item)
                if type(val) is str:
                    if item == "directory_lineEdit":
                        val = common.unicodePath(val)
                    string = "%s = '%s'"%(item, val)
                else:
                    string = "%s = %s"%(item, val)
                lines.append(string)
        self.writeDefault(lines)
        lines += ["EXTENSION_DATA = '%s'"%self.extension_comboBox.currentText(),
                    "EXTENSION_PARAMS = '%s.txt'"%self.parameters_lineEdit.text()]
        delimiter = self.delimiter_comboBox.currentText()
        if delimiter == "Tab":
            delimiter = "\t"
        elif delimiter == "Space":
            delimiter = " "
        lines += ["DELIMITER = '%s'"%delimiter]
        self.updateConstants(lines)
        self.parent.updateConstants()

    def accept_replace(self):
        self.constantsWriter()
        self.accept()

    def writeDefault(self, lines):
        try:
            with open(constants.SETTINGS_PATH, "w") as file:
                [file.write(line + constants.BREAKLINE) for line in lines]
        except FileNotFoundError as e:
            print(e)

    def updateConstants(self, lines):
        [exec("constants.%s"%line) for line in lines]

    def setConstants(self):
        try:
            common.updateConstants(self)
        except AttributeError:
            pass

    def chooseFolder(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", common.findDocuments()))
        if folder != "":
            self.directory_lineEdit.setText(folder)

class SubWindow(QtWidgets.QMdiSubWindow):
    def __init__(self, parent = None):
        super(SubWindow, self).__init__(parent)
        self.parent = parent

    def closeEvent(self, evnt):
        evnt.ignore()
        self.hide()
        name = self.windowTitle().lower()
        actions = self.parent.menuView.actions()
        for action in actions:
            if name in action.text(): action.setChecked(False)

class ClickableLineEdit(QtGui.QLineEdit):
    clicked = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        super(ClickableLineEdit, self).__init__(parent)
        self.setReadOnly(True)

    def mousePressEvent(self, event):
        self.clicked.emit()
        QtGui.QLineEdit.mousePressEvent(self, event)
