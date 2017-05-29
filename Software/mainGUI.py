#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import __GUI_images__
from __mainwindow__ import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets

from reimaginedQuantum import *

DEFAULT_EXIST = True
if not os.path.exists('default.py'):
    save_default(None)
    DEFAULT_EXIST = False

from menuBar import *
from propertiesWindow import *

def heavy_import():
    """ Imports matplotlib and NumPy.

    Useful to be combined with threading processes.
    """
    global plt, FigureCanvas, NavigationToolbar, EngFormatter, Axes
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import (
                            FigureCanvasQTAgg as FigureCanvas,
                            NavigationToolbar2QT as NavigationToolbar)
    from plotting import Axes

if CURRENT_OS == 'win32':
    import ctypes
    myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class Table(QtWidgets.QTableWidget):
    TABLE_SIZE = 200

    global DELIMITER, TABLE_YGROW
    def __init__(self, parent = None):
        QtWidgets.QTableWidget.__init__(self)
        self.parent = parent
        self.setEnabled(True)
        self.setDragEnabled(True)
        self.setRowCount(0)
        self.setColumnCount(0)
        self.horizontalHeader().setSortIndicatorShown(False)
        self.verticalHeader().setDefaultSectionSize(16)
        self.verticalHeader().setMinimumSectionSize(16)
        self.verticalHeader().setSortIndicatorShown(False)

        self.number_columns = 0
        self.current_cell = 0
        self.detectors = 0
        self.coincidences = 0
        self.header = [None]
        self.ylength = self.rowCount()
        self.xlength = self.columnCount()

    def create_table(self):
        experiment = self.parent.experiment

        self.setRowCount(TABLE_YGROW)
        self.detectors = experiment.number_detectors
        self.coincidences = experiment.number_coins
        self.number_columns = self.detectors + self.coincidences + 1

        self.setColumnCount(self.number_columns)
        self.headers = [None]*self.number_columns
        self.headers[0] = 'Time (s)'
        for i in range(self.detectors):
            self.headers[i+1] = experiment.detectors[i].name
        for j in range(self.coincidences):
            self.headers[i+j+2] = experiment.coin_channels[j].name

        self.setHorizontalHeaderLabels(self.headers)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def get_last_row(self, column):
        return self.item((self.current_cell-1)%self.TABLE_SIZE, column).text()

    def clean(self):
        self.clearContents()

    def include(self, time_, detectors, coins):
        actual = self.rowCount()
        if (actual - self.current_cell) <= TABLE_YGROW and actual < self.TABLE_SIZE:
            self.setRowCount(TABLE_YGROW + actual)
            self.resizeRowsToContents()

        if self.current_cell%self.TABLE_SIZE == 0 and self.current_cell//self.TABLE_SIZE != 0:
            self.clean()

        if type(detectors) is list:
            for i in range(self.detectors):
                value = "%d"%detectors[i]
                cell = QtWidgets.QTableWidgetItem(value)
                self.setItem(self.current_cell%self.TABLE_SIZE, i+1, cell)
                cell.setFlags(QtCore.Qt.ItemIsEnabled)

            for j in range(self.coincidences):
                value = "%d"%coins[j]
                cell = QtWidgets.QTableWidgetItem(value)
                self.setItem(self.current_cell%self.TABLE_SIZE, i+j+2, cell)
                cell.setFlags(QtCore.Qt.ItemIsEnabled)

            cell = QtWidgets.QTableWidgetItem("%.3f"%time_)
            self.setItem(self.current_cell%self.TABLE_SIZE, 0, cell)
            self.scrollToItem(cell)
            self.current_cell += 1

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """
        Defines the mainwindow.

    Constants
    """

    DEFAULT_TPLOT = 100 #: Minimum time to update plot
    DEFAULT_TCHECK = 1000 #: Minimum time to check values in device
    DEFAULT_CURRENT = 200 #: Minimum time to update current labels
    EXTENSION_DATA = '.dat'
    EXTENSION_PARAMS = '.txt'
    SUPPORTED_EXTENSIONS = {EXTENSION_DATA : 'Plain text data file (*.dat)', '.csv' : 'CSV data files (*.csv)'}

    global DELIMITER, DEFAULT_SAMP, DEFAULT_COIN, MIN_SAMP, MAX_SAMP, TABLE_YGROW
    global MIN_COIN, MAX_COIN, STEP_COIN, DEFAULT_CHANNELS, FILE_NAME, USER_EMAIL, SEND_EMAIL
    global DEFAULT_EXIST, CURRENT_OS
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setupUi(self)
        try:
            name, ext = self.split_extension(FILE_NAME)
            name += ext
        except Exception as e:
            from reimaginedQuantum.constants import FILE_NAME as name

        self.LOCAL_NAMES = None
        self.LOCAL_CONSTANTS = {}
        self.local_constants()
        self.output_name = name
        self.save_line.setText(self.output_name)
        self.extension = self.EXTENSION_DATA
        self.params_file = "%s_params%s"%(self.output_name[:-4], self.EXTENSION_PARAMS)

        self.samp_spinBox.setMinimum(self.MIN_SAMP)
        self.samp_spinBox.setMaximum(self.MAX_SAMP)
        self.coin_spinBox.setMinimum(self.MIN_COIN)
        self.coin_spinBox.setMaximum(self.MAX_COIN)
        self.coin_spinBox.setSingleStep(self.STEP_COIN)

        self.samp_spinBox.setValue(self.DEFAULT_SAMP)
        self.coin_spinBox.setValue(self.DEFAULT_COIN)

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
        self.channels_button.clicked.connect(self.detectors_window_caller)
        self.samp_spinBox.valueChanged.connect(self.method_sampling)
        self.coin_spinBox.valueChanged.connect(self.method_coinWin)
        self.port_box.currentIndexChanged.connect(self.select_serial)
        self.save_line.editingFinished.connect(self.save_location)

        self.table = Table(self)
        self.horizontalLayout_3.addWidget(self.table)
        self.ylength = self.table.rowCount()
        self.xlength = self.table.columnCount()

        """
        menu bar
        """
        self.actionDefault_properties.triggered.connect(self.default_window_caller)
        self.actionAbout.triggered.connect(self.about_window_caller)

        self.data = None
        self.params_header = None
        """
        set
        """
        self.detectors_window = PropertiesWindow(self)
        self.default_window = DefaultWindow(self)
        self.about_window = AboutWindow()

        self.serial = None
        self.port = None
        self.experiment = None
        self.ports = {}
        self.last_row_saved = 0
        self.number_columns = 0
        self.format = None
        self.file_exists_warning = False
        self.default_constants = False

        self.first_port = True
        """
        fig
        """
        self.fig = None
        self.center()

        """
        email check
        """
        self.temp = Table(self)

        if not DEFAULT_EXIST:
            self.default_window_caller()

    def center(self):
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = 0.5*(screen.width() - widget.width())
        y = 0.5*(screen.height() - widget.height())
        self.move(x, y)

    def local_constants(self):
        self.LOCAL_NAMES = ['DELIMITER', 'DEFAULT_SAMP', 'DEFAULT_COIN', 'MIN_SAMP',
                'MAX_SAMP', 'TABLE_YGROW', 'MIN_COIN', 'MAX_COIN', 'STEP_COIN',
                'DEFAULT_CHANNELS', 'FILE_NAME', 'USER_EMAIL', 'SEND_EMAIL']

        for name in self.LOCAL_NAMES:
            value = eval(name)
            self.LOCAL_CONSTANTS[name] = value
            if type(value) != str:
                instruction = 'self.%s = %s'%(name, str(value))
            else:
                instruction = "self.%s = '%s'"%(name, value)
            exec(instruction)

    def update_constants(self, constants):
        for name in self.LOCAL_NAMES:
            if name in constants:
                value = constants[name]
                self.LOCAL_CONSTANTS[name] = value
                if type(value) != str:
                    instruction = 'self.%s = %s'%(name, str(value))
                else:
                    instruction = "self.%s = '%s'"%(name, value)
                exec(instruction)

        self.save_line.setText(self.FILE_NAME)
        self.save_location()

        self.samp_spinBox.setValue(self.DEFAULT_SAMP)
        self.coin_spinBox.setValue(self.DEFAULT_COIN)
        save = True
        if not DEFAULT_EXIST and not self.default_constants:
            save = False
            self.default_constants = True
        self.detectors_window.update_constants(constants, save)

    def create_fig(self):
        self.fig, (ax_counts, ax_coins) = plt.subplots(2, sharex=True, facecolor='None', edgecolor='None')
        self.canvas = FigureCanvas(self.fig)
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
                message = "%s %s%s\n"%(current_time, self.DELIMITER, label)
        else:
            message = "%s %s%s: %d %s\n"%(current_time, self.DELIMITER, label, value, units)
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
        if text == '':
            raise Exception("Name is empty.")

        return name, ext

    def reallocate_output(self, name, remove_old = False):
        params = "%s_params%s"%(name, self.EXTENSION_PARAMS)
        new = "%s%s"%(name, self.extension)
        if new != self.output_name and self.data != None:
            with open(new, "a") as file_:
                with open(self.output_name, "r") as old:
                    for line in old:
                        file_.write(line)
            self.data.output_file = new
            if remove_old:
                os.remove(self.output_name)
            if params != self.params_file:
                with open(params, "a") as file_:
                    with open(self.params_file, "r") as old:
                        for line in old:
                            file_.write(line)
                if remove_old:
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
            elif end:
                os.remove(self.params_file)
                os.remove(self.output_name)


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
        if n != len(current_ports) or n == 0:
            self.port_box.clear()
            self.ports = current_ports
            for port in self.ports:
                try:
                    if CURRENT_OS != 'win32':
                        if CommunicationPort(self.ports[port]).test():
                            self.port_box.addItem(port)
                        CommunicationPort.close()
                    else:
                        self.port_box.addItem(port)
                except:
                    pass

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
                    try:
                        self.serial.close()
                    except CommunicationError:
                        pass
                    self.serial = None
                self.port = new_port
                try:
                    self.serial = CommunicationPort(self.port)

                    self.channels_button.setDisabled(False)
                    # if self.detectors_window != None:
                    # #     self.detectors_window.update()
                    # self.detectors_window.update()
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
        # if status:
        self.stream_activate(status)

    def start_experiment(self):
        if self.format == None:
            self.stream_activate(False)
            self.create_table()
            self.header = np.zeros(self.table.number_columns, dtype=object)
            self.widget_activate(False)
            self.format = [r"%d" for i in range(self.table.number_columns)]
            self.format[0] = "%.3f"
            self.format = self.DELIMITER.join(self.format)
            self.data = RingBuffer(TABLE_YGROW, self.table.number_columns, self.output_name, self.format)
            self.create_current_labels()
            self.create_fig()

        if self.serial != None:
            if not self.detectors_window.error_ocurred:
                self.widget_activate(False)

    def stream_activate(self, status):
        self.stream_button.setDisabled(status)

    def create_table(self):
        self.table.create_table()
        with open(self.output_name, 'a') as file_:
            text = self.DELIMITER.join(self.table.headers)
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

    def detectors_window_caller(self):
        """
        creates a property window to define number of channels
        """
        if not self.file_exists_warning:
            ans1 = os.path.exists(r'%s'%self.output_name)
            ans2 = os.path.exists(r'%s'%self.params_file)
            if ans1 or ans2:
                QtWidgets.QMessageBox.warning(self, "File exists",
                    "The selected file already exists.\nData will be appended.")
            self.file_exists_warning = True
        self.detectors_window.show()

    def default_window_caller(self):
        self.default_window.show()

    def about_window_caller(self):
        self.about_window.show()

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
        self.detectors_window.set_values(values)

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
            value = self.table.get_last_row(i+1)
            self.current_labels[i].change_value(value)
        for j in range(self.experiment.number_coins):
            value = self.table.get_last_row(j+i+2)
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
                self.detectors_window.send_data()
                self.method_sampling(self.samp_spinBox.value(), error_capable = False)
                self.method_coinWin(self.coin_spinBox.value(), error_capable = False)
                self.save_param("Streaming started.", None, None)
                self.start_clocks()

            time_, detectors, coins = self.experiment.current_values()

            if type(detectors) is list:
                if self.table.current_cell == 0:
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

                self.table.include(time_, detectors, coins)

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
            if 'None' in str(e):
                pass
            else:
                if error_capable:
                    self.errorWindow(e)
                else:
                    raise e
        if self.default_constants or DEFAULT_EXIST:
            self.save_param("Sampling Time", value, "ms")

    def method_coinWin(self, value, error_capable = True):
        try:
            self.experiment.set_coinWindow(value)
        except Exception as e:
            if 'None' in str(e):
                pass
            else:
                if error_capable:
                    self.errorWindow(e)
                else:
                    raise e
        if self.default_constants or DEFAULT_EXIST:
            self.save_param("Coincidence window", value, "ns")

    def _draw_event(self, *args):
        self.ax_coins.set_background()
        self.ax_counts.set_background()

    def update_plot(self):
        if self.table.current_cell > 1:
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
        error_text = str(error)
        message = None

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        if type(error) == CommunicationError or type(error) == ExperimentError:
            self.stop_clocks()
            self.serial = None
            self.serial_refresh()
            self.widget_activate(True)
            self.stream_button.setStyleSheet("background-color: red")
            msg.setIcon(QtWidgets.QMessageBox.Critical)

            # if self.email_window != None:
            #     current_time = strftime("%H:%M:%S", localtime())
            #     message = """ An error ocurred at %s.
            #
            #     Error reads:
            #         %s
            #     """%(current_time, error_text)
            #     message += "\nReimagined Quantum."

        self.save_param(error_text, None, None)
        msg.setText('An Error has ocurred.\n%s'%error_text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec_()
        if message != None:
            self.email_window.send(message)

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Exit',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.include_params(self.output_name, self.params_file, save = True, end = True)
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
   app = QtWidgets.QApplication(sys.argv)
   splash_pix = QtGui.QPixmap(':/splash.png')
   splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
   progressBar = QtWidgets.QProgressBar(splash)
   progressBar.setGeometry(250, 320, 100, 20)
   splash.show()
   app.processEvents()
   app.setWindowIcon(QtGui.QIcon(':/icon.png'))

   if CURRENT_OS == 'win32':
       import ctypes
       myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
       ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

   progressBar.setValue(15)

   thread = Thread(target = heavy_import)
   thread.setDaemon(True)
   thread.start()
   i = 15
   while thread.is_alive():
       if i < 95:
           i += 1
           progressBar.setValue(i)
       sleep(0.1)

   plt.rcParams.update({'font.size': 8})

   main = Main()
   progressBar.setValue(100)
   main.show()
   splash.close()
   sys.exit(app.exec_())
