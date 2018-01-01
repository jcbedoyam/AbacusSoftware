import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QTableWidgetItem
from PyAbacus.constants import CURRENT_OS

from constants import *
from PyAbacus.communication import findPorts

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
    MAX_CHARS = 25 #: Maximum number of letters in a label.
    MAX_DIGITS = 7 #: Maximum number of digits of a number in label.
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
        self.MAX_TRY = 40
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
    def __init__(self, parent=None):
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

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
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

        self.file_tab_frame1_directory_label = QtWidgets.QLabel("Directory:")
        self.file_tab_frame1_directory_lineEdit = QtWidgets.QLineEdit()
        self.file_tab_frame1_directory_pushButton = QtWidgets.QPushButton("Open")

        self.file_tab_frame1_layout.addWidget(self.file_tab_frame1_directory_label)
        self.file_tab_frame1_layout.addWidget(self.file_tab_frame1_directory_lineEdit)
        self.file_tab_frame1_layout.addWidget(self.file_tab_frame1_directory_pushButton)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame1)

        # frame2
        self.file_tab_frame2 = QtWidgets.QFrame()
        self.file_tab_frame2_layout = QtWidgets.QFormLayout(self.file_tab_frame2)

        self.file_tab_frame2_extension_label = QtWidgets.QLabel("Extension:")
        self.file_tab_frame2_extension_comboBox = QtWidgets.QComboBox()
        self.file_tab_frame2_delimiter_label = QtWidgets.QLabel("Delimiter:")
        self.file_tab_frame2_delimiter_comboBox = QtWidgets.QComboBox()
        self.file_tab_frame2_parameters_label = QtWidgets.QLabel("Parameters suffix:")
        self.file_tab_frame2_parameters_lineEdit = QtWidgets.QLineEdit()
        self.file_tab_frame2_datetime_label = QtWidgets.QLabel("Use datetime:")
        self.file_tab_frame2_datetime_checkBox = QtWidgets.QCheckBox()
        self.file_tab_frame2_autogenerate_label = QtWidgets.QLabel("Autogenerate file name:")
        self.file_tab_frame2_autogenerate_checkBox = QtWidgets.QCheckBox()

        self.file_tab_frame2_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.file_tab_frame2_extension_label)
        self.file_tab_frame2_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.file_tab_frame2_extension_comboBox)
        self.file_tab_frame2_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.file_tab_frame2_delimiter_label)
        self.file_tab_frame2_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.file_tab_frame2_delimiter_comboBox)
        self.file_tab_frame2_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.file_tab_frame2_parameters_label)
        self.file_tab_frame2_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.file_tab_frame2_parameters_lineEdit)
        self.file_tab_frame2_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.file_tab_frame2_datetime_label)
        self.file_tab_frame2_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.file_tab_frame2_datetime_checkBox)
        self.file_tab_frame2_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.file_tab_frame2_autogenerate_label)
        self.file_tab_frame2_layout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.file_tab_frame2_autogenerate_checkBox)

        self.file_tab_verticalLayout.addWidget(self.file_tab_frame2)

        """
        settings tab
        """
        self.settings_tab_verticalLayout = QtWidgets.QVBoxLayout(self.settings_tab)

        self.settings_tab_frame = QtWidgets.QFrame()
        self.settings_tab_frame_layout = QtWidgets.QFormLayout(self.settings_tab_frame)

        self.settings_tab_frame_sampling_label = QtWidgets.QLabel("Sampling time:")
        self.settings_tab_frame_sampling_comboBox = QtWidgets.QComboBox()
        self.settings_tab_frame_coincidence_label = QtWidgets.QLabel("Coincidence window (ns):")
        self.settings_tab_frame_coincidence_spinBox = QtWidgets.QSpinBox()
        self.settings_tab_frame_delayA_label = QtWidgets.QLabel("Delay A (ns):")
        self.settings_tab_frame_delayA_spinBox = QtWidgets.QSpinBox()
        self.settings_tab_frame_delayB_label = QtWidgets.QLabel("Delay B (ns):")
        self.settings_tab_frame_delayB_spinBox = QtWidgets.QSpinBox()
        self.settings_tab_frame_sleepA_label = QtWidgets.QLabel("Sleep time A (ns):")
        self.settings_tab_frame_sleepA_spinBox = QtWidgets.QSpinBox()
        self.settings_tab_frame_sleepB_label = QtWidgets.QLabel("Sleep time B (ns):")
        self.settings_tab_frame_sleepB_spinBox = QtWidgets.QSpinBox()

        self.settings_tab_frame_from_device_label = QtWidgets.QLabel("Get settings from device:")
        self.settings_tab_frame_from_device_checkBox = QtWidgets.QCheckBox()

        self.settings_tab_frame_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_sampling_label)
        self.settings_tab_frame_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_sampling_comboBox)
        self.settings_tab_frame_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_coincidence_label)
        self.settings_tab_frame_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_coincidence_spinBox)
        self.settings_tab_frame_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_delayA_label)
        self.settings_tab_frame_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_delayA_spinBox)
        self.settings_tab_frame_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_delayB_label)
        self.settings_tab_frame_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_delayB_spinBox)
        self.settings_tab_frame_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_sleepA_label)
        self.settings_tab_frame_layout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_sleepA_spinBox)
        self.settings_tab_frame_layout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_sleepB_label)
        self.settings_tab_frame_layout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_sleepB_spinBox)
        self.settings_tab_frame_layout.setWidget(6, QtWidgets.QFormLayout.LabelRole, self.settings_tab_frame_from_device_label)
        self.settings_tab_frame_layout.setWidget(6, QtWidgets.QFormLayout.FieldRole, self.settings_tab_frame_from_device_checkBox)

        self.settings_tab_verticalLayout.addWidget(self.settings_tab_frame)

        """
        buttons
        """
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttons)
