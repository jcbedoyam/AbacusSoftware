import os
import numpy as np
from itertools import combinations

try:
    from PyQt5 import QtWidgets, QtGui, QtCore
    from PyQt5.QtGui import QTableWidgetItem
    from PyQt5.QtWidgets import QSizePolicy, QTabWidget, QWidget, QCheckBox, \
                        QVBoxLayout, QFrame, QGroupBox, QLabel, QSizePolicy, \
                        QComboBox, QSpinBox, QFormLayout
except ModuleNotFoundError:
    from PyQt4 import QtWidgets, QtGui, QtCore
    from PyQt4.QtGui import QTableWidgetItem
    from PyQt4.QtWidgets import QSizePolicy

from pyAbacus.constants import CURRENT_OS

import abacusSoftware.common as common
import abacusSoftware.constants as constants
import pyAbacus as abacus
from pyAbacus import findDevices

class SamplingWidget(object):
    def __init__(self, layout = None, label = None, method = None, number_channels = 2):
        self.layout = layout
        self.label = label
        self.method = method
        self.number_channels = 0
        self.widget = None
        self.value = 0
        self.changeNumberChannels(number_channels)

    def setEnabled(self, enabled):
        self.widget.setEnabled(enabled)

    def getValue(self):
        text_value = self.widget.currentText()
        return common.timeInUnitsToMs(text_value)

    def setValue(self, value):
        if value < 1000:
            index = self.widget.findText('%d ms' % value)
        elif value < 10000:
            index = self.widget.findText('%.1f s' % (value / 1000))
        else:
            index = self.widget.findText('%d s' % (value / 1000))

        self.widget.setCurrentIndex(index)

    def changeNumberChannels(self, number_channels):
        self.number_channels = number_channels
        if self.widget != None:
            self.layout.removeWidget(self.widget)
            self.widget.deleteLater()

        self.widget = QComboBox()
        if self.method != None: self.widget.currentIndexChanged.connect(self.method)
        self.widget.setEditable(True)
        self.widget.lineEdit().setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.widget.lineEdit().setReadOnly(True)
        if self.number_channels == 2:
            common.setSamplingComboBox(self.widget)
        else:
            bases = np.arange(10, 100, 1)
            values = list(range(1, 10))
            for i in range(5):
                values += list(bases * 10 ** i)
            values.append(int(1e6))
            common.setSamplingComboBox(self.widget, values = values)
        if self.label != None: self.label.setText("Sampling time:")
        if self.layout != None:
            self.layout.setWidget(0, QFormLayout.FieldRole, self.widget)

class Tabs(QFrame):
    MAX_CHECKED_4CH = 1
    MAX_CHECKED_8CH = 8
    def __init__(self, parent = None):
        QFrame.__init__(self)
        self.parent = parent

        self.all = []
        self.letters = []
        self.double = []
        self.multiple = []
        self.multiple_checked = []
        self.last_multiple_checked = None
        self.number_channels = 0

        scrollArea1 = QtWidgets.QScrollArea()
        scrollArea1.setWidgetResizable(True)
        scrollArea1.setStyleSheet("background:transparent;")
        scrollArea2 = QtWidgets.QScrollArea()
        scrollArea2.setWidgetResizable(True)
        scrollArea2.setStyleSheet("background:transparent;")
        scrollArea3 = QtWidgets.QScrollArea()
        scrollArea3.setWidgetResizable(True)
        scrollArea3.setStyleSheet("background:transparent;")

        self.single_tab = QGroupBox("Single")
        self.double_tab = QGroupBox("Double")
        self.multiple_tab = QGroupBox("Multiple")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(3)

        self.single_tab_layout = QVBoxLayout(self.single_tab)
        self.double_tab_layout = QVBoxLayout(self.double_tab)
        self.multiple_tab_layout = QVBoxLayout(self.multiple_tab)

        self.layout.addWidget(QLabel("<b>COUNTS</b>"))
        self.layout.addWidget(scrollArea1)
        self.layout.addWidget(scrollArea2)
        self.layout.addWidget(scrollArea3)

        scrollArea1.setWidget(self.single_tab)
        scrollArea2.setWidget(self.double_tab)
        scrollArea3.setWidget(self.multiple_tab)

    def createSingle(self, letter, layout):
        widget = QCheckBox(letter)
        widget.setChecked(True)
        setattr(self, letter, widget)
        layout.addWidget(widget)
        return widget

    def setNumberChannels(self, n_channels):
        self.deleteCheckBoxs()
        self.number_channels = n_channels

        self.letters = [chr(i + ord('A')) for i in range(n_channels)]
        joined = "".join(self.letters)
        self.double = ["".join(pair) for pair in combinations(joined, 2)]
        self.multiple = []
        if n_channels > 2:
            for i in range(3, n_channels + 1):
                self.multiple += ["".join(pair) for pair in combinations(joined, i)]

        self.all = self.letters + self.double + self.multiple

        for letter in self.letters:
            widget = self.createSingle(letter, self.single_tab_layout)
            widget.stateChanged.connect(self.signal)
        for letter in self.double:
            widget = self.createSingle(letter, self.double_tab_layout)
            widget.stateChanged.connect(self.signal)
        for letter in self.multiple:
            widget = self.createSingle(letter, self.multiple_tab_layout)
            widget.setChecked(False)
            widget.stateChanged.connect(self.signalMultiple)

    def deleteSingle(self, widget, layout):
        layout.removeWidget(widget)
        widget.deleteLater()

    def deleteCheckBoxs(self):
        for letter in self.letters:
            self.deleteSingle(getattr(self, letter), self.single_tab_layout)
        for letter in self.double:
            self.deleteSingle(getattr(self, letter), self.double_tab_layout)
        for letter in self.multiple:
            self.deleteSingle(getattr(self, letter), self.multiple_tab_layout)

        self.all = []
        self.letters = []
        self.double = []
        self.multiple = []

    def getChecked(self):
        return [letter for letter in self.all if getattr(self, letter).isChecked()]

    def signal(self):
        self.parent.activeChannelsChanged(self.getChecked())

    def signalMultiple(self, user_input = True):
        multiple_checked = [letter for letter in self.multiple if getattr(self, letter).isChecked()]
        new = [m for m in multiple_checked if not m in self.multiple_checked]

        if self.number_channels == 4: max = self.MAX_CHECKED_4CH
        elif self.number_channels == 8: max = self.MAX_CHECKED_8CH

        if len(self.multiple_checked) == max and len(new):
            getattr(self, self.multiple_checked[-1]).setChecked(False)
            del self.multiple_checked[-1]
        self.multiple_checked += new
        if len(new) and new != self.last_multiple_checked:
            self.last_multiple_checked = new
            self.parent.sendMultipleCoincidences(new)
        self.signal()

    def setChecked(self, letters):
        if len(letters) <= 2:
            getattr(self, letters).setChecked(True)
        elif self.last_multiple_checked != letters:
            getattr(self, letters).setChecked(True)
            self.last_multiple_checked = letters

class Table(QtWidgets.QTableWidget):
    def __init__(self, active_labels, active_indexes):
        QtWidgets.QTableWidget.__init__(self)
        cols = len(active_indexes) + 2
        self.setColumnCount(cols)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.verticalHeader().setDefaultSectionSize(18)
        self.verticalHeader().setMinimumSectionSize(18)
        self.verticalHeader().setSortIndicatorShown(False)

        self.last_data = 0
        self.n_active = len(active_indexes)
        self.active_indexes = active_indexes

        self.headers = ['Time (s)', 'ID'] + active_labels
        self.setHorizontalHeaderLabels(self.headers)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True);

    def insertData(self, data):
        rows, cols = data.shape
        data = data[self.last_data : ]
        self.last_data = rows
        rows = data.shape[0]

        for i in range(rows):
            self.insertRow(0)
            for j in range(self.n_active + 2):
                fmt = "%d"
                if j < 2:
                    if j == 0:
                        fmt = "%.3f"
                    value = fmt % data[i, j]
                else:
                    value = fmt % data[i, 2 + self.active_indexes[j - 2]]
                self.setItem(0, j, QTableWidgetItem(value))
                self.item(0, j).setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

class AutoSizeLabel(QtWidgets.QLabel):
    """ From reclosedev at http://stackoverflow.com/questions/8796380/automatically-resizing-label-text-in-qt-strange-behaviour
    and Jean-Sébastien http://stackoverflow.com/questions/29852498/syncing-label-fontsize-with-layout-in-pyqt
    """
    MAX_DIGITS = 7 #: Maximum number of digits of a number in label.
    MAX_CHARS = 9 + MAX_DIGITS #: Maximum number of letters in a label.
    INITIAL_FONT_SIZE = 10
    global CURRENT_OS
    def __init__(self, text, value):
        QtWidgets.QLabel.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.font_name = "Monospace"
        if CURRENT_OS == "win32":
            self.font_name = "Courier New"
        self.setFont(QtGui.QFont(self.font_name))
        self.font_size = self.INITIAL_FONT_SIZE
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

    def clearSize(self):
        self.setFontSize(self.INITIAL_FONT_SIZE)

    def resize(self):
        """ Finds the best font size to use if the size of the window changes. """
        f = self.font()
        cr = self.contentsRect()
        height = cr.height()
        width = cr.width()
        if abs(height * width - self.height * self.width) > 1:
            self.font_size = self.INITIAL_FONT_SIZE
            for i in range(self.MAX_TRY):
                f.setPixelSize(self.font_size)
                br =  QtGui.QFontMetrics(f).boundingRect(self.text())
                if br.height() <= cr.height() and br.width() <= cr.width():
                    self.font_size += 1
                else:
                    if (CURRENT_OS == 'win32'):
                        self.font_size += -1
                    else:
                        self.font_size += -2
                    if (not constants.IS_LIGHT_THEME):
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.installEventFilter(self)
        self.labels = []

    def createLabels(self, labels):
        self.removeLabels()
        n_colors = len(constants.COLORS)
        for (i, name) in enumerate(labels):
            label = AutoSizeLabel(name, "0")
            self.setColor(label, constants.COLORS[i % n_colors])
            self.layout.addWidget(label)
            self.labels.append(label)

    def removeLabels(self):
        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.labels = []

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
        sizes = [None] * len(self.labels)
        for (i, label) in enumerate(self.labels):
            label.resize()
            sizes[i] = label.font_size

        if len(self.labels) > 0:
            try:
                size = max(sizes)
                for label in self.labels:
                    label.setFontSize(size)
            except TypeError: pass

    def clearSizes(self):
        for label in self.labels: label.clearSize()

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
        self.ports = findDevices(print_on = False)[0]
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
    MAX_CHANNELS = 4
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self)

        self.parent = parent
        self.setWindowTitle("Default settings")

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        # self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)

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

        self.theme_label = QtWidgets.QLabel("Light theme:")
        self.theme_checkBox = QtWidgets.QCheckBox()

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        widgets = [(self.theme_label, self.theme_checkBox),
                    (self.check_updates_label, self.check_updates_checkBox),
                    (self.autogenerate_label, self.autogenerate_checkBox),
                    (self.datetime_label, self.datetime_checkBox),
                    (self.file_prefix_label, self.file_prefix_lineEdit),
                    (self.parameters_label, self.parameters_lineEdit),
                    (self.extension_label, self.extension_comboBox),
                    (self.delimiter_label, self.delimiter_comboBox),
                    ]

        self.fillFormLayout(self.file_tab_frame2_layout, widgets)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        self.theme_checkBox.setChecked(True)
        self.autogenerate_checkBox.setCheckState(2)
        self.check_updates_checkBox.setCheckState(2)
        self.autogenerate_checkBox.stateChanged.connect(self.actogenerateMethod)
        self.datetime_checkBox.setCheckState(2)
        self.parameters_lineEdit.setText(constants.PARAMS_SUFFIX)
        self.file_prefix_lineEdit.setText(constants.FILE_PREFIX)
        # self.setDirectory()
        # if not self.verifyDirectory():
        #     self.directory_lineEdit.setText(common.findDocuments())
        # else: self.direco
        self.delimiter_comboBox.insertItems(0, constants.DELIMITERS)
        self.extension_comboBox.insertItems(0, sorted(constants.SUPPORTED_EXTENSIONS.keys())[::-1])


        """
        settings tab
        """
        self.settings_tab_verticalLayout = QtWidgets.QVBoxLayout(self.settings_tab)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)

        self.settings_tab_frame = QtWidgets.QFrame()
        self.settings_tab_frame_layout = QtWidgets.QFormLayout(self.settings_tab_frame)

        scrollArea.setWidget(self.settings_tab_frame)

        self.sampling_label = QtWidgets.QLabel("Sampling time:")
        self.sampling_widget = SamplingWidget()#QtWidgets.QComboBox()
        self.coincidence_label = QtWidgets.QLabel("Coincidence window (ns):")
        self.coincidence_spinBox = QtWidgets.QSpinBox()
        self.coincidence_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        widgets = [(self.sampling_label, self.sampling_widget.widget),
                    (self.coincidence_label, self.coincidence_spinBox)]

        letters = [chr(i + ord('A')) for i in range(self.MAX_CHANNELS)]
        self.delays = []
        self.sleeps = []
        d_labels = []
        s_labels = []
        for letter in letters:
            d_label = QtWidgets.QLabel("Delay %s (ns):" % letter)
            d_spinBox = QtWidgets.QSpinBox()
            s_label = QtWidgets.QLabel("Sleep time %s (ns):" % letter)
            s_spinBox = QtWidgets.QSpinBox()
            d_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            s_spinBox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            common.setDelaySpinBox(d_spinBox)
            common.setSleepSpinBox(s_spinBox)

            setattr(self, "delay_%s_label"%letter, d_label)
            setattr(self, "sleep_%s_label"%letter, s_label)
            setattr(self, "delay_%s_spinBox"%letter, d_spinBox)
            setattr(self, "sleep_%s_spinBox"%letter, s_spinBox)
            d_labels.append(d_label)
            s_labels.append(s_label)
            self.delays.append(d_spinBox)
            self.sleeps.append(s_spinBox)

        widgets += [(d_labels[i], self.delays[i]) for i in range(self.MAX_CHANNELS)]
        widgets += [(s_labels[i], self.sleeps[i]) for i in range(self.MAX_CHANNELS)]

        self.fillFormLayout(self.settings_tab_frame_layout, widgets)

        self.settings_tab_verticalLayout.addWidget(self.settings_tab_frame)

        common.setSamplingComboBox(self.sampling_widget.widget)
        common.setCoincidenceSpinBox(self.coincidence_spinBox)

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

    def actogenerateMethod(self, val):
        self.datetime_checkBox.setEnabled(val)
        self.file_prefix_lineEdit.setEnabled(val)

    def fillFormLayout(self, layout, values):
        for (i, line) in enumerate(values):
            layout.setWidget(i, QtWidgets.QFormLayout.LabelRole, line[0])
            layout.setWidget(i, QtWidgets.QFormLayout.FieldRole, line[1])

    def constantsWriter(self, update_parent = True):
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
        lines.append("sampling_widget = %d" % self.sampling_widget.getValue())
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
        if update_parent: self.parent.updateConstants()

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
            self.sampling_widget.setValue(constants.sampling_widget)
            self.setDirectory()
        except AttributeError:
            pass

    def chooseFolder(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", common.findDocuments(), QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontUseNativeDialog))
        if folder != "":
            self.directory_lineEdit.setText(folder)

    def setDirectory(self):
        try:
            directory = constants.directory_lineEdit
            if os.path.exists(directory):
                self.directory_lineEdit.setText(directory)
                return
            directory = os.path.normpath(directory)
            documents = os.path.normpath(common.findDocuments())
            e = Exception('The default directory "%s" does not exist.\n\nThe default directory will be set to "%s".' % (directory, documents))
            self.parent.errorWindow(e)
        except AttributeError as e:
            pass
        directory = common.findDocuments()
        self.directory_lineEdit.setText(directory)
        common.directory_lineEdit = directory
        self.constantsWriter()

class SubWindow(QtWidgets.QMdiSubWindow):
    def __init__(self, parent = None):
        super(SubWindow, self).__init__(parent)
        self.parent = parent
        self.setWindowIcon(constants.ICON)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
