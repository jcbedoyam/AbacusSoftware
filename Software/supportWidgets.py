import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QTableWidgetItem
from PyAbacus.constants import CURRENT_OS

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
