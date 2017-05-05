#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 11:31:32 2017

@author: juan
"""

import sys
import GUI_images
from PyQt5 import QtCore, QtGui, QtWidgets

import re

from reimaginedQuantum import *

DELIMITER = "\t"

def heavy_import():
    """ Imports matplotlib and NumPy.

    Useful to be combined with threading processes.
    """
    global plt, FigureCanvas, NavigationToolbar, EngFormatter
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import (
                            FigureCanvasQTAgg as FigureCanvas,
                            NavigationToolbar2QT as NavigationToolbar)
    from matplotlib.ticker import EngFormatter


app = QtWidgets.QApplication(sys.argv)
splash_pix = QtGui.QPixmap(':/splash.png')
splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
progressBar = QtWidgets.QProgressBar(splash)
progressBar.setGeometry(250, 320, 100, 20)
#progressBar.setStyleSheet(DEFAULT_STYLE)
splash.show()
app.processEvents()
app.setWindowIcon(QtGui.QIcon(':/icon.png'))

if CURRENT_OS == 'win32':
    import ctypes
    myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

progressBar.setValue(15)
from mainwindow import Ui_MainWindow
progressBar.setValue(30)
from channels import Ui_Dialog
progressBar.setValue(50)

thread = Thread(target=heavy_import)
thread.setDaemon(True)
thread.start()
i = 50
while thread.is_alive():
    if i < 95:
        i += 1
        progressBar.setValue(i)
    sleep(0.2)

plt.rcParams.update({'font.size': 8})

#########################
#from mainwindow import Ui_MainWindow
#from channels import Ui_Dialog
#heavy_import()
#########################

class propertiesWindow(QtWidgets.QDialog, Ui_Dialog):
    """
        Defines the channel configuration dialog.
    """
    MIN_DELAY = 0
    MAX_DELAY = 200
    STEP_DELAY = 5
    DEFAULT_DELAY = 0
    MIN_SLEEP = 0
    MAX_SLEEP = 200
    STEP_SLEEP = 5
    DEFAULT_SLEEP = 0
    DEFAULT_CHANNELS = 2 #: Default number of channels

    global DELIMITER
    def __init__(self, parent=None):
        super(propertiesWindow, self).__init__(parent)
        self.setupUi(self)

        self.channel_spinBox.valueChanged.connect(self.creator)

        self.parent = parent
        self.current_n = 0
        self.number_channels = self.DEFAULT_CHANNELS
        self.widgets = []
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.update)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset)
        self.creator(self.channel_spinBox.value())
        self.error_ocurred = False
        self.last_time = ""

    def set_values(self, values):
        for i in range(self.number_channels):
            name = self.widgets[0][i].text()[:-1]
            if self.widgets[1][i].value() != values[i][0]: # delay
                print(self.widgets[1][i].value(), values[i][0])
                self.widgets[1][i].setValue(values[i][0])
                self.parent.save_param("%s (Delay)"%name, self.widgets[1][i].value(), 'ns')
            if self.widgets[2][i].value() != values[i][1]: # sleep
                self.widgets[2][i].setValue(values[i][1])
                self.parent.save_param("%s (Sleep)"%name, self.widgets[2][i].value(), 'ns')

    def creator(self, n):
        """
            creates the spinboxes and labels required by the user
        """
        funcs = [QtWidgets.QLabel, QtWidgets.QSpinBox, QtWidgets.QSpinBox]

        self.N = len(funcs)
        if len(self.widgets) == 0:
            self.widgets = [[] for i in range(self.N)]

        while self.current_n < n:
            for i in range(self.N):
                if i == 0:
                    widget = funcs[i]("Detector %s:"%chr(self.current_n + ord("A")))
                else:
                    widget = funcs[i]()
                    if i == 1:
                        widget.setMinimum(self.MIN_DELAY)
                        widget.setMaximum(self.MAX_DELAY)
                        widget.setSingleStep(self.STEP_DELAY)
                    else:
                        widget.setMinimum(self.MIN_SLEEP)
                        widget.setMaximum(self.MAX_SLEEP)
                        widget.setSingleStep(self.STEP_SLEEP)

                    widget.setCorrectionMode(QtWidgets.QAbstractSpinBox.CorrectToNearestValue)
                    widget.setKeyboardTracking(False)
                    widget.setProperty("value", 0)

                self.widgets[i].append(widget)
                self.gridLayout_2.addWidget(widget, self.current_n+1, i)
            self.current_n += 1
        self.delete(n, self.N)
        self.number_channels = n

    def send_data(self, error_capable = True):
        try:
            for i in range(self.number_channels):
                delay = self.widgets[1][i].value()
                sleep = self.widgets[2][i].value()
                self.parent.experiment.detectors[i].set_times(delay, sleep)
            self.error_ocurred = False
        except Exception as e:
            if error_capable:
                self.parent.errorWindow(e)
            else:
                raise e

    def update(self):
        """
            sends message with the updated information
        """
        try:
            self.parent.experiment = Experiment(self.parent.serial, self.number_channels)
            self.send_data(error_capable = False)
            self.channel_spinBox.setEnabled(False)
            self.saveParams()
            self.parent.start_experiment()
            self.error_ocurred = False
        except Exception as e:
            self.error_ocurred = True
            self.parent.errorWindow(e)

    def saveParams(self, delimiter = DELIMITER):
        delays = self.widgets[1]
        sleeps = self.widgets[2]
        for i in range(self.number_channels):
            name = self.widgets[0][i].text()[:-1]
            self.parent.save_param("%s (Delay)"%name, delays[i].value(), 'ns')
            self.parent.save_param("%s (Sleep)"%name, sleeps[i].value(), 'ns')

    def delete(self, n, N):
        """
            delets unneccesary rows of labels and spinboxes
        """
        while self.current_n > n:
            for i in range(N):
                widget = self.widgets[i][self.current_n-1]
                self.gridLayout_2.removeWidget(widget)
                widget.deleteLater()
                del self.widgets[i][self.current_n-1]
            self.current_n -= 1

    def reset(self):
        """
            sets everything to default
        """
        self.channel_spinBox.setValue(self.DEFAULT_CHANNELS)
        self.delete(self.DEFAULT_CHANNELS, self.N)
        for i in range(1, 3):
            value = self.DEFAULT_DELAY
            if i == 2:
                value = self.DEFAULT_SLEEP
            for j in range(self.current_n):
                self.widgets[i][j].setValue(value)

class RingBuffer():
    """
    Based on https://scimusing.wordpress.com/2013/10/25/ring-buffers-in-pythonnumpy/
    """
    global DELIMITER
    def __init__(self, rows, columns, output_file, fmt, delimiter = DELIMITER):
        self.data = np.zeros((rows, columns))
        self.index = 0
        self.empty = True
        self.output_file = output_file
        self.last_saved = 0
        self.format = fmt
        self.size = self.data.shape[0]
        self.total_movements = 0

    def extend(self, x):
        "adds array x to ring buffer"
        if self.empty:
            self.empty = False
        self.total_movements += 1
        x_index = (self.index + np.arange(x.shape[0])) % self.size
        self.data[x_index] = x
        self.index = x_index[-1] + 1

        if self.index == self.size and not self.empty:
            self.save()

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        idx = (self.index + np.arange(self.size)) %self.size
        return self.data[idx]

    def save(self):
        "Saves the buffer"
        from_index = self.size - self.index + self.last_saved
        self.last_saved = self.index
        data = self.get()[from_index%self.size:]
        with open(self.output_file, 'ab') as _file:
            np.savetxt(_file, data, fmt = self.format)

    def __getitem__(self, item):
        if self.total_movements > self.size:
            return self.get()
        else:
            return self.get()[self.size-self.index :]

class AutoSizeLabel(QtWidgets.QLabel):
    """
    from reclosedev at http://stackoverflow.com/questions/8796380/automatically-resizing-label-text-in-qt-strange-behaviour
    and Jean-Sébastien http://stackoverflow.com/questions/29852498/syncing-label-fontsize-with-layout-in-pyqt
    """
    MAX_CHARS = 25
    MAX_DIGITS = 7
    global CURRENT_OS
    def __init__(self, text, value):
        QtWidgets.QLabel.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.installEventFilter(self)
        self.initial = True
        self.font_name = "Monospace"
        if CURRENT_OS == "win32":
            self.font_name = "Courier New"
        self.setFont(QtGui.QFont(self.font_name))
        self.initial = False
        self.initial_font_size = 10
        self.font_size = 10
        self.MAX_TRY = 40
        self.height = self.contentsRect().height()
        self.width = self.contentsRect().width()
        self.name = text
        self.setText(self.stylish_text(text, value))
        self.set_font_size(self.font_size)

    def set_font_size(self, size):
        f = self.font()
        f.setPixelSize(size)
        self.setFont(f)

    def set_color(self, color):
        self.setStyleSheet('color: %s'%color)

    def stylish_text(self, text, value):
        n_text = len(text)
        n_value = len(value)
        N = n_text + n_value
        spaces = [" " for i in range(self.MAX_CHARS - N-1)]
        spaces = "".join(spaces)
        text = "%s: %s%s"%(text, spaces, value)
        return text

    def change_value(self, value):
        self.setText(self.stylish_text(self.name, value))

    def eventFilter(self, object, evt):
        if not self.initial:
            ty = evt.type()
            if ty == 97: # DONT KNOW WHY
                self.resizeEvent(evt)
                return False
            elif ty == 12:
                self.resizeEvent(evt)
                return False
        return True

    def resizeEvent(self, evt):
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
                    f.setPixelSize(max(self.font_size - 1, 1))
                    break
            self.setFont(f)
            self.height = height
            self.width = width

class Canvas(FigureCanvas):
    def __init__(self, figure):

        self.fig = figure
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class Axes(object):
    global EngFormatter
    def __init__(self, figure, canvas, axes, xmajor, ylabel, detectors):
        self.fig = figure
        self.points = []
        self.axes = axes
        self.ylimits = None
        self.status = False
        self.ylabel = ylabel
        self.canvas = canvas
        self.xmajor = xmajor
        self.background = None
        self.number_points = 0
        self.colors = {}
        self.labels = []
        self.xcoor = 0
        self.data = None

        self.init_lines(detectors)
        self.axes.set_ylabel(self.ylabel)
        self.size = self.get_size()

    def get_size(self):
        return self.axes.bbox.width, self.axes.bbox.height

    def init_lines(self, detectors):
        for detector in detectors:
            self.labels.append(detector.name)
            point = self.axes.plot([], [], "-o", ms=3, label = detector.name)[0]
            self.colors[detector.name] = point.get_color()
            self.points.append(point)
        self.number_points = len(self.points)
        self.ylimits = self.axes.get_ylim()
        self.axes.set_xlim(0, self.xmajor)
        self.axes.legend()
        self.axes.yaxis.set_major_formatter(EngFormatter())
        self.canvas.draw()
        self.set_background()

    def set_background(self):
        self.background = self.fig.canvas.copy_from_bbox(self.axes.bbox)

    def legend(self):
        self.axes.legend(self.points, self.labels, loc = 2)

    def change_status(self):
        self.status = all([last == now for (last, now) in \
                zip(self.ylimits, self.axes.get_ylim())])

    def update_plot(self):
        [self.points[i].set_data(self.xcoor, self.data[:, i+1]) for i in range(self.number_points)]

    def update_data(self, xcoor, data):
        max_ = []
        min_ = []
        self.xcoor = xcoor
        self.data = data
        self.change_status()
        for i in range(self.number_points):
            data_ = data[:, i+1]
            self.points[i].set_data(xcoor, data_)
            if self.status:
                max_.append(max(data_))
                min_.append(min(data_))
        if self.status:
            max_ = max(max_)*1.25
            min_ = min(min_)
            limits = self.axes.get_ylim()
            if(max_ > limits[1]\
               or min_ < limits[0]):
                self.axes.set_ylim(min_, max_)
                self.ylimits = self.axes.get_ylim()
                return True

        current_size = self.get_size()
        size_status = [abs(dim1 - dim2) > 1 for (dim1, dim2) in zip(self.size, current_size)]
        if not all(size_status):
            self.size = current_size
            return True
        return False

    def clean(self):
        self.axes.clear()

    def set_limits(self):
        self.axes.set_ylim(self.ylimits)
        self.axes.set_xlim(0, self.xmajor)
        self.axes.set_ylabel(self.ylabel)
        self.axes.yaxis.set_major_formatter(EngFormatter())
        self.legend()

    def draw_artist(self):
        [self.axes.draw_artist(line) for line in self.points]

    def blit(self):
        self.fig.canvas.blit(self.axes.bbox)

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """
        Defines the mainwindow.

    Constants
    """
    DEFAULT_SAMP = 500
    DEFAULT_TPLOT = 100
    DEFAULT_TCHECK = 1000
    DEFAULT_CURRENT = 200
    TABLE_YGROW = 100
    EXTENSION_DATA = '.dat'
    EXTENSION_PARAMS = '.txt'
    SUPPORTED_EXTENSIONS = {EXTENSION_DATA : 'Plain text data file (*.dat)', '.csv' : 'CSV data files (*.csv)'}

    global DELIMITER
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setupUi(self)
        self.output_name = self.save_line.text()
        self.extension = self.EXTENSION_DATA
        self.params_file = "%s_params%s"%(self.output_name[:-4], self.EXTENSION_PARAMS)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.DEFAULT_SAMP)
        self.plot_timer = QtCore.QTimer()
        if self.DEFAULT_SAMP > self.DEFAULT_TPLOT:
            timer = self.DEFAULT_SAMP
        else:
            timer = self.DEFAULT_TPLOT


        self.plot_timer.setInterval(timer)

        self.check_timer = QtCore.QTimer()
        self.check_timer.setInterval(self.DEFAULT_TCHECK)
        self.samp_spinBox.setValue(self.DEFAULT_SAMP)

        self.current_timer = QtCore.QTimer()
        if self.DEFAULT_SAMP > self.DEFAULT_CURRENT:
            timer = self.DEFAULT_SAMP
        else:
            timer = self.DEFAULT_CURRENT
        self.current_timer.setInterval(timer)
        """
        signals and events
        """
        self.port_box.installEventFilter(self)
        self.timer.timeout.connect(self.method_streamer)
        self.plot_timer.timeout.connect(self.update_plot)
        self.check_timer.timeout.connect(self.periodic_check)
        self.current_timer.timeout.connect(self.update_current_labels)
        self.save_button.clicked.connect(self.choose_file)
        self.stream_button.clicked.connect(self.method_streamer)
        self.channels_button.clicked.connect(self.channelsCaller)
        self.samp_spinBox.valueChanged.connect(self.method_sampling)
        self.coin_spinBox.valueChanged.connect(self.method_coinWin)
        self.port_box.currentIndexChanged.connect(self.select_serial)
#        self.save_line.editingFinished.connect(self.save_location)
        self.save_line.returnPressed.connect(self.save_location)
        self.ylength = self.table.rowCount()
        self.xlength = self.table.columnCount()

        self.data = None
        self.params_header = None
        """
        set
        """
        self.window = None
        self.serial = None
        self.port = None
        self.experiment = None
        self.ports = {}
        self.current_cell = 0
        self.last_row_saved = 0
        self.number_columns = 0
        self.format = None

        self.first_port = True
        """
        fig
        """
        self.fig = None

    def create_fig(self):
        self.fig, (ax_counts, ax_coins) = plt.subplots(2, sharex=True, facecolor='None', edgecolor='None')
        self.canvas = Canvas(self.fig)
        self.plot_layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas,
                self.plot_widget, coordinates=True)

        self.plot_layout.addWidget(self.toolbar)
        self.ax_counts = Axes(self.fig, self.canvas, ax_counts, self.TABLE_YGROW,
                              "Counts", self.experiment.detectors)
        self.ax_coins = Axes(self.fig, self.canvas, ax_coins, self.TABLE_YGROW,
                             "Coincidences", self.experiment.coin_channels)

        for i in range(self.experiment.number_detectors):
            self.current_labels[i].set_color(self.ax_counts.colors[self.experiment.detectors[i].name])
        for j in range(self.experiment.number_coins):
            self.current_labels[1+j+i].set_color(self.ax_coins.colors[self.experiment.coin_channels[j].name])

        self.canvas.mpl_connect('draw_event', self._draw_event)
        self.canvas.draw_idle()
        self.fig.set_tight_layout(True)

    def save_param(self, label, value, units):
        current_time = strftime("%H:%M:%S", localtime())
        if value == None:
            message = label
            if units == None:
                message = "%s %s%s\n"%(current_time, DELIMITER, label)
        else:
            message = "%s %s%s: %d %s\n"%(current_time, DELIMITER, label, value, units)
        with open(self.params_file, 'a') as file_:
            file_.write(message)

    def create_current_labels(self):
        self.current_labels = []
        for detector in self.experiment.detectors:
            name = detector.name
            label = AutoSizeLabel(name, "0")
            label.setObjectName("current_label_%s"%detector)
            self.verticalLayout_2.addWidget(label)
            self.current_labels.append(label)
        for coin in self.experiment.coin_channels:
            name = coin.name
            label = AutoSizeLabel(name, "0")
            label.setObjectName("current_label_%s"%detector)
            self.verticalLayout_2.addWidget(label)
            self.current_labels.append(label)

    def split_extension(self, text):
        try:
            name, ext = text.split('.')
            ext = ".%s"%ext
        except:
            name = text
            ext = ''

        if not ext in self.SUPPORTED_EXTENSIONS.keys() and ext != "":
            raise Exception("Current extension '%s' is not valid."%ext)

        return name, ext

    def reallocate_output(self, name, remove_old = False):
        params = "%s_params%s"%(name, self.EXTENSION_PARAMS)
        new = "%s%s"%(name, self.extension)
        if new != self.output_name and self.data != None:
            with open(new, "a") as file_:
                with open(self.output_name, "r") as old:
                    for line in old:
                        file_.write(line)

            with open(params, "a") as file_:
                with open(self.params_file, "r") as old:
                    for line in old:
                        file_.write(line)
            self.data.output_file = new
            self.include_params(self.output_name, self.params_file)
            if remove_old:
                os.remove(self.output_name)
                os.remove(self.params_file)
        self.output_name = new
        self.params_file = params

    def include_params(self, output, params, save = False, end = False):
        if self.data != None:
            if not self.data.empty:
                if save:
                    self.data.save()
                if end:
                    temp = "%sTEMP"%params
                    with open(temp, "w") as file:
                        file.write("##### PARAMETERS USED #####\n%s\n"%self.params_header)
                        with open(params, "r") as params_:
                            for line in params_:
                                file.write(line)
                    os.remove(params)
                    os.rename(temp, params)

    def save_location(self):
        new = self.save_line.text()
        try:
            name, ext = self.split_extension(new)
            if ext != '':
                self.extension = ext
            self.reallocate_output(name, remove_old = True)
        except Exception as e:
            self.save_line.setText(self.output_name)
            self.errorWindow(e)

    def eventFilter(self, source, event):
        """ Creates event to handle serial combobox opening.
        """
        if (event.type() == QtCore.QEvent.MouseButtonPress and source is self.port_box):
            self.serial_refresh()
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def serial_refresh(self):
        """ Loads serial port described at user combobox.
        """
        current_ports = findPort()
        n = 0
        for x in current_ports.items():
            if x in self.ports.items():
                n += 1
        if n != len(current_ports):
            self.port_box.clear()
            self.ports = current_ports
            for port in self.ports:
                self.port_box.addItem(port)
        self.port_box.setCurrentIndex(-1)

    def select_serial(self, index, error_capable = True):
        """ Selects port at index position of combobox.
        """
        if index != -1 and not self.first_port:
            new_port = self.port_box.itemText(index)
            try:
                new_port = self.ports[new_port]
            except:
                new_port = ''
            if new_port != '':
                if self.serial != None:
                    self.serial.close()
                    self.serial = None
                self.port = new_port
                try:
                    self.serial = CommunicationPort(self.port)
                    self.channels_button.setDisabled(False)
                    if self.window != None:
                        self.window.update()
                except Exception as e:
                    e = type(e)("Serial selection: %s"%str(e))
                    if error_capable:
                        self.errorWindow(e)
            else:
                self.widget_activate(True)

        self.first_port = False


    def widget_activate(self, status):
        """
        most of the tools will be disabled if there is no UART detected
        """
        self.samp_spinBox.setDisabled(status)
        self.coin_spinBox.setDisabled(status)
        self.channels_button.setDisabled(status)
        if status:
            self.stream_activate(status)

    def start_experiment(self):
        if self.format == None:
            self.stream_activate(False)
            self.create_table()
            self.header = np.zeros(self.number_columns, dtype=object)
            self.widget_activate(False)
            self.format = [r"%d" for i in range(self.number_columns)]
            self.format[0] = "%.3f"
            self.format = DELIMITER.join(self.format)
            self.data = RingBuffer(self.TABLE_YGROW, self.number_columns, self.output_name, self.format)
            self.create_current_labels()
            self.create_fig()

        if self.serial != None and self.window != None:
            if not self.window.error_ocurred:
                self.stream_activate(False)

    def stream_activate(self, status):
        self.stream_button.setDisabled(status)

    def create_table(self):
        self.number_columns = self.experiment.number_detectors + self.experiment.number_coins + 1
        self.table.setRowCount(self.TABLE_YGROW)
        self.table.setColumnCount(self.number_columns)
        self.table.setItem(0, 0, QtWidgets.QTableWidgetItem("Time (s)"))
        for i in range(self.experiment.number_detectors):
            self.table.setItem(0, i+1, QtWidgets.QTableWidgetItem(self.experiment.detectors[i].name))
        for j in range(self.experiment.number_coins):
            self.table.setItem(0, i+j+2, QtWidgets.QTableWidgetItem(self.experiment.coin_channels[j].name))

        headers = [self.table.item(0,i).text() for i in range(self.number_columns)]
        with open(self.output_name, 'a') as file_:
            text = DELIMITER.join(headers)
            file_.write("%s\n"%text)

    def choose_file(self):
        """
        user interaction with saving file
        """
        dlg = QtWidgets.QFileDialog()
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        nameFilters = [self.SUPPORTED_EXTENSIONS[extension] for extension in self.SUPPORTED_EXTENSIONS]
        dlg.setNameFilters(nameFilters)
        dlg.selectNameFilter(self.SUPPORTED_EXTENSIONS[self.extension])
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            try:
                extension = self.split_extension(name)[1]
                if extension == "":
                    name += self.extension
                self.save_line.setText(name)
                self.save_location()
            except Exception as e:
                self.errorWindow(e)

    def channelsCaller(self):
        """
        creates a property window to define number of channels
        """
        if self.window == None:
            ans1 = os.path.exists(self.output_name)
            ans2 = os.path.exists(self.params_file)
            if ans1 or ans2:
                QtWidgets.QMessageBox.warning(self, "File exists",
                    "The selected file already exists.\nData will be appended.")
            self.window = propertiesWindow(self)
        self.window.show()

    def periodic_check(self):
        try:
            self.experiment.periodic_check()
        except Exception as e:
            self.errorWindow(e)
        samp = self.experiment.get_sampling_value()
        coin = self.experiment.get_coinwin_value()
        if self.samp_spinBox.value() != samp:
            self.samp_spinBox.setValue(samp)
        if self.coin_spinBox.value() != coin:
            self.coin_spinBox.setValue(coin)

        values = self.experiment.get_detectors_timers_values()
        self.window.set_values(values)

    def start_clocks(self):
        self.timer.start()
        self.plot_timer.start()
        self.check_timer.start()
        self.current_timer.start()

    def stop_clocks(self):
        self.timer.stop()
        self.plot_timer.stop()
        self.check_timer.stop()
        self.current_timer.stop()

    def update_current_labels(self):
        for i in range(self.experiment.number_detectors):
            value = self.table.item(self.current_cell, i+1).text()
            self.current_labels[i].change_value(value)
        for j in range(self.experiment.number_coins):
            value = self.table.item(self.current_cell, j+i+2).text()
            self.current_labels[j+i+1].change_value(value)

    def method_streamer(self):
        try:
            if self.timer.isActive() and self.sender() == self.stream_button:
                self.stop_clocks()
                self.data.save()
                self.save_param("Streaming stoped.", None, None)
                self.stream_button.setStyleSheet("background-color: none")

            elif not self.timer.isActive():
                self.stream_button.setStyleSheet("background-color: green")
                self.window.send_data(error_capable = False)
                self.method_sampling(self.samp_spinBox.value(), error_capable = False)
                self.method_coinWin(self.coin_spinBox.value(), error_capable = False)
                self.save_param("Streaming started.", None, None)
                self.start_clocks()

            time_, detectors, coins = self.experiment.current_values()


            actual = self.table.rowCount()
            if (actual - self.current_cell) <= self.TABLE_YGROW:
                self.table.setRowCount(self.TABLE_YGROW + actual)

            if type(detectors) is list:
                if self.current_cell == 0:
                    self.init_time = time()
                    current_time = asctime(localtime())
                    self.params_header = "Reimagined Quantum experiment began at %s"%current_time
                time_ = time_ - self.init_time
                if time_ < 0:
                    time_ = 0
                values = [time_] + detectors + coins
                values = np.array(values)
                values = values.reshape((1, values.shape[0]))
                self.data.extend(values)
                for i in range(self.experiment.number_detectors):
                    value = "%d"%detectors[i]
                    cell = QtWidgets.QTableWidgetItem(value)
                    self.table.setItem(self.current_cell+1, i+1, cell)
                    cell.setFlags(QtCore.Qt.ItemIsEnabled)

                for j in range(self.experiment.number_coins):
                    value = "%d"%coins[j]
                    cell = QtWidgets.QTableWidgetItem(value)
                    self.table.setItem(self.current_cell+1, i+j+2, cell)
                    cell.setFlags(QtCore.Qt.ItemIsEnabled)

                cell = QtWidgets.QTableWidgetItem("%.3f"%time_)
                self.table.setItem(self.current_cell+1, 0, cell)
                self.table.scrollToItem(cell)
                self.current_cell += 1

        except Exception as e:
            self.errorWindow(e)

    def method_sampling(self, value, error_capable = True):
        self.timer.setInterval(value)
        if value > self.DEFAULT_TPLOT:
            self.plot_timer.setInterval(value)
        else:
            self.plot_timer.setInterval(self.DEFAULT_TPLOT)

        if value > self.DEFAULT_CURRENT:
            self.current_timer.setInterval(value)
        else:
            self.current_timer.setInterval(self.DEFAULT_CURRENT)
        try:
            self.experiment.set_sampling(value)
        except Exception as e:
            if error_capable:
                self.errorWindow(e)
            else:
                raise e

        self.save_param("Sampling Time", value, "ms")

    def method_coinWin(self, value, error_capable = True):
        try:
            self.experiment.set_coinWindow(value)
        except Exception as e:
            if error_capable:
                self.errorWindow(e)
            else:
                raise e
        self.save_param("Coincidence window", value, "ns")

    def _draw_event(self, *args):
        self.ax_coins.set_background()
        self.ax_counts.set_background()

    def update_plot(self):
        if self.current_cell > 1:
            data = self.data[:]
            times = np.arange(data.shape[0])
            ychanged1 = self.ax_counts.update_data(times, data)
            ychanged2 = self.ax_coins.update_data(times, data[:, self.experiment.number_detectors:])
            if ychanged1 or ychanged2:
                self.ax_coins.clean()
                self.ax_counts.clean()
                self.ax_coins.set_limits()
                self.ax_counts.set_limits()
                self.fig.canvas.draw()
                self.ax_coins.draw_artist()
                self.ax_counts.draw_artist()
                self.fig.canvas.flush_events()
            else:
                self.fig.canvas.restore_region(self.ax_coins.background)
                self.fig.canvas.restore_region(self.ax_counts.background)
                self.ax_coins.draw_artist()
                self.ax_counts.draw_artist()
                self.ax_counts.blit()
                self.ax_coins.blit()

    def errorWindow(self, error):
        self.stop_clocks()
        msg = QtWidgets.QMessageBox()
        error = str(error)
        if "write" in error or "Serial" in error:
            self.serial = None
            self.ports = {}

        self.serial_refresh()
        self.stream_button.setStyleSheet("background-color: none")

        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("An Error has ocurred.")
        msg.setInformativeText(str(error))
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec_()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Exit',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply ==QtWidgets.QMessageBox.Yes:
            self.include_params(self.output_name, self.params_file, save = True, end = True)
            event.accept()
        else:
            event.ignore()
#
# if __name__ == "__main__":
#    app = QtWidgets.QApplication(sys.argv)
#    splash_pix = QtGui.QPixmap(':/splash.png')
#    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
#    progressBar = QtWidgets.QProgressBar(splash)
#    progressBar.setGeometry(250, 320, 100, 20)
#    #progressBar.setStyleSheet(DEFAULT_STYLE)
#    splash.show()
#    app.processEvents()
#    app.setWindowIcon(QtGui.QIcon(':/icon.png'))
#
#    if CURRENT_OS == 'win32':
#        import ctypes
#        myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
#        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
#
#    progressBar.setValue(15)
#    from mainwindow import Ui_MainWindow
#    progressBar.setValue(30)
#    from channels import Ui_Dialog
#    progressBar.setValue(50)
#
#    thread = Thread(target=heavy_import)
#    thread.setDaemon(True)
#    thread.start()
#    i = 50
#    while thread.is_alive():
#        if i < 95:
#            i += 1
#            progressBar.setValue(i)
#        sleep(0.2)
#
#    plt.rcParams.update({'font.size': 8})
#
#    main = Main()
#    progressBar.setValue(100)
#    main.show()
#    splash.close()
#    sys.exit(app.exec_())

# main = Main()
# progressBar.setValue(100)
# main.show()
# splash.close()
# sys.exit(app.exec_())
