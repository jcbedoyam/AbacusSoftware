from __channels__ import Ui_Dialog
from reimaginedQuantum.core import *
from reimaginedQuantum.constants import *
from PyQt5 import QtCore, QtGui, QtWidgets

from importlib.machinery import SourceFileLoader
SourceFileLoader("default", DEFAULT_PATH).load_module()

from default import *

class WidgetLine(object):
    """
        Defines a single widget line in the PropertiesWindow.
    """
    global MIN_DELAY, MAX_DELAY, STEP_DELAY
    global MIN_SLEEP, MAX_SLEEP, STEP_SLEEP
    def __init__(self, identifier, parent, delay_value, sleep_value):
        self.parent = parent
        self.identifier = identifier
        self.delay_value = delay_value
        self.sleep_value = sleep_value
        self.allowUpdate_delay = True
        self.allowUpdate_sleep = True

        self.name = "Detector %s"%self.identifier
        self.widget = QtWidgets.QWidget(self.parent.groupBox)
        self.label = QtWidgets.QLabel("%s:"%self.name)
        self.delay_spinBox = QtWidgets.QSpinBox()
        self.sleep_spinBox = QtWidgets.QSpinBox()
        self.__init_spinBoxes__()
        self.__init_layout__()

    def __init_spinBoxes__(self):
        self.delay_spinBox.setMinimum(MIN_DELAY)
        self.delay_spinBox.setMaximum(MAX_DELAY)
        self.delay_spinBox.setSingleStep(STEP_DELAY)

        self.sleep_spinBox.setMinimum(MIN_SLEEP)
        self.sleep_spinBox.setMaximum(MAX_SLEEP)
        self.sleep_spinBox.setSingleStep(STEP_SLEEP)

        self.__init_corrections__(self.delay_spinBox)
        self.__init_corrections__(self.sleep_spinBox)

        self.updateValues()

        self.delay_spinBox.valueChanged.connect(self.handleDelay)
        self.sleep_spinBox.valueChanged.connect(self.handleSleep)

    def __init_corrections__(self, widget):
        widget.setCorrectionMode(QtWidgets.QAbstractSpinBox.CorrectToNearestValue)
        widget.setKeyboardTracking(False)

    def __init_layout__(self):
        layout = QtWidgets.QHBoxLayout(self.widget)
        layout.addWidget(self.label)
        layout.addWidget(self.delay_spinBox)
        layout.addWidget(self.sleep_spinBox)
        self.widget.setLayout(layout)
        self.parent.verticalLayoutDetectors.addWidget(self.widget)

    def handleDelay(self, value):
        self.delay_value = value
        self.allowUpdate_delay = False

    def handleSleep(self, value):
        self.sleep_value = value
        self.allowUpdate_sleep = False

    def setValues(self, delay_sleep_value, save = True):
        """ Verifies if incomming values are different to stored ones.

        If they are different than older ones, saves the incoming one
        in the params file. It also updates the spinBox values.
        """
        delay_value, sleep_value = delay_sleep_value
        update = False
        if delay_value != self.delay_value and self.allowUpdate_delay:
            self.delay_value = delay_value
            if save:
                self.parent.parent.saveParam("%s (Delay)"%self.name,
                                        self.delay_spinBox.value(), 'ns')
            update = True
        if sleep_value != self.sleep_value and self.allowUpdate_sleep:
            self.sleep_value = sleep_value
            if save:
                self.parent.parent.saveParam("%s (Sleep)"%self.name,
                                        self.sleep_spinBox.value(), 'ns')
            update = True

        if update:
            self.updateValues()

    def allowUpdate(self):
        self.allow_update_delay = True
        self.allow_update_sleep = True

    def reset(self):
        """ Sets delay_value and sleep_value to the default ones. It also updates
        them to the spinboxes.
        """
        self.delay_value = DEFAULT_DELAY
        self.sleep_value = DEFAULT_SLEEP
        self.updateValues()

    def updateValues(self):
        """ Updates the spinBox values, from the attributes.
        """
        self.delay_spinBox.setValue(self.delay_value)
        self.sleep_spinBox.setValue(self.sleep_value)

class PropertiesWindow(QtWidgets.QDialog, Ui_Dialog):
    """
        Defines the channel configuration dialog.
    """

    global DELIMITER, DEFAULT_CHANNELS, MIN_CHANNELS, MAX_CHANNELS
    global DEFAULT_DELAY, DEFAULT_SLEEP
    def __init__(self, parent=None):
        super(PropertiesWindow, self).__init__(parent)
        self.setupUi(self)

        self.parent = parent
        self.current_n = 0
        self.LOCAL_NAMES = None
        self.LOCAL_CONSTANTS = {}
        self.local_constants()
        self.number_channels = self.DEFAULT_CHANNELS
        self.channel_spinBox.setMaximum(self.MAX_CHANNELS)
        self.channel_spinBox.setMinimum(self.MIN_CHANNELS)
        self.channel_spinBox.setValue(self.number_channels)

        self.channel_spinBox.valueChanged.connect(self.creator)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.update)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset)

        widget = QtWidgets.QWidget(self.groupBox)
        layout = QtWidgets.QHBoxLayout(widget)
        detectors_label = QtWidgets.QLabel("Detectors")
        delay_label = QtWidgets.QLabel("Delay time (ns)")
        sleep_label = QtWidgets.QLabel("Sleep time (ns)")

        layout.addWidget(detectors_label)
        layout.addWidget(delay_label)
        layout.addWidget(sleep_label)
        widget.setLayout(layout)

        self.verticalLayoutDetectors.addWidget(widget)

        self.widgets = []
        self.creator(self.number_channels)
        self.error_ocurred = False
        self.last_time = ""

    def local_constants(self):
        self.LOCAL_NAMES = ['DELIMITER', 'DEFAULT_CHANNELS', 'MIN_CHANNELS',
                    'MAX_CHANNELS', 'DEFAULT_DELAY', 'DEFAULT_SLEEP']

        for name in self.LOCAL_NAMES:
            value = eval(name)
            self.LOCAL_CONSTANTS[name] = value
            if type(value) != str:
                instruction = 'self.%s = %s'%(name, str(value))
            else:
                instruction = "self.%s = '%s'"%(name, value)
            exec(instruction)

    def updateConstants(self, constants, save = True):
        for name in self.LOCAL_NAMES:
            if name in constants:
                value = constants[name]
                self.LOCAL_CONSTANTS[name] = value
                if type(value) != str:
                    instruction = 'self.%s = %s'%(name, str(value))
                else:
                    instruction = "self.%s = '%s'"%(name, value)
                exec(instruction)

        self.channel_spinBox.setValue(self.DEFAULT_CHANNELS)
        values = [(self.DEFAULT_DELAY, self.DEFAULT_SLEEP) for i in range(self.DEFAULT_CHANNELS)]
        self.setValues(values, save)

    def setValues(self, values, save = True):
        """ Updates the incoming values to the spinboxes.

        Args:
            values (list): list of tuples, each position of the list
            has the values of delay and sleep time for a channel.
        """
        for i in range(self.number_channels):
            self.widgets[i].setValues(values[i], save)

    def creator(self, n):
        """
            Creates the spinboxes and labels required by the user
        """

        if n > self.current_n:
            self.widgets += [None]*(n-self.current_n)
        while self.current_n < n:
            self.widgets[self.current_n] = WidgetLine(chr(self.current_n \
                                           + ord("A")), self, self.DEFAULT_DELAY,
                                           self.DEFAULT_SLEEP)
            self.current_n += 1
        self.delete(n)
        self.number_channels = n

    def sendData(self):
        for i in range(self.number_channels):
            delay = self.widgets[i].delay_value
            sleep = self.widgets[i].sleep_value
            self.parent.experiment.detectors[i].set_times(delay, sleep)

    def update(self):
        """
            Sends a message with the updated information
        """
        try:
            self.parent.experiment = Experiment(self.parent.serial, self.number_channels)
            self.sendData()
            self.channel_spinBox.setEnabled(False)
            self.saveParams()
            self.parent.startExperiment()
            for widget in self.widgets:
                self.widget.allowUpdate()

        except Exception as e:
            if type(e) == CommunicationError or type(e) == ExperimentError:
                self.error_ocurred = True
                self.parent.errorWindow(e)

    def saveParams(self, delimiter = DELIMITER):
        for widget in self.widgets:
            self.parent.saveParam("%s (Delay)"%widget.name, widget.delay_value, 'ns')
            self.parent.saveParam("%s (Sleep)"%widget.name, widget.sleep_value, 'ns')

    def delete(self, n):
        """
            Delets unneccesary rows of labels and spinboxes
        """
        while self.current_n > n:
            widget = self.widgets[self.current_n - 1].widget
            self.verticalLayoutDetectors.removeWidget(widget)
            widget.deleteLater()
            del self.widgets[self.current_n - 1]
            self.current_n -= 1

    def reset(self):
        """
            Sets every detector to the default values
        """
        self.channel_spinBox.setValue(self.DEFAULT_CHANNELS)
        for i in range(self.number_channels):
            self.widgets[i].reset()


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

    def createLabels(self, detectors, coincidences):
        for detector in detectors:
            name = detector.name
            label = AutoSizeLabel(name, "0")
            self.layout.addWidget(label)
            self.labels.append(label)

        for coin in coincidences:
            name = coin.name
            label = AutoSizeLabel(name, "0")
            self.layout.addWidget(label)
            self.labels.append(label)

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
        for (i, label) in enumerate(self.labels):
            label.resize()
            sizes[i] = label.font_size
        size = max(sizes)
        for label in self.labels:
            label.setFontSize(size)
