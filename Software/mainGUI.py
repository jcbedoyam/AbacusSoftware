#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import __GUI_images__
from __mainwindow__ import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from reimaginedQuantum import *

import subprocess

DEFAULT_EXIST = True

if not os.path.exists(DEFAULT_PATH):
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
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from plotting import Axes, NavigationToolbar

if CURRENT_OS == 'win32':
    import ctypes
    myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class Table(QtWidgets.QTableWidget):
    TABLE_SIZE = 100000

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

    def createTable(self):
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

    def getLastRow(self, column):
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
    global MIN_COIN, MAX_COIN, STEP_COIN, DEFAULT_CHANNELS, FILE_NAME, USER_EMAIL, SEND_EMAIL, USE_DATETIME
    global DEFAULT_EXIST, CURRENT_OS, USE_DATETIME
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setupUi(self)
        try:
            name, ext = self.splitExtension(FILE_NAME)
            name += ext
        except Exception as e:
            from reimaginedQuantum.constants import FILE_NAME as name

        self.LOCAL_NAMES = None
        self.LOCAL_CONSTANTS = {}
        self.local_constants()
        self.output_name = name
        if USE_DATETIME:
            name, ext = self.splitExtension(self.output_name)
            self.output_name = "%s%s%s"%(name, strftime("%Y%m%d_%H%M"), ext)
        self.save_line.setText(self.output_name)
        # else:
        #     self.save_line.setText(self.output_name)
        self.extension = self.EXTENSION_DATA
        self.params_file = "%s_params%s"%(self.output_name[:-4], self.EXTENSION_PARAMS)

        params_header = "Reimagined Quantum session began at %s"%asctime(localtime())

        with open(self.params_file, "a") as file:
            file.write("##### PARAMETERS USED #####\n%s\n"%params_header)
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
        self.plot_timer.setInterval(self.DEFAULT_TPLOT)
        # if self.DEFAULT_SAMP > self.DEFAULT_TPLOT:
        #     timer = self.DEFAULT_SAMP
        # else:
        #     timer = self.DEFAULT_TPLOT
        #
        # self.plot_timer.setInterval(timer)

        self.check_timer = QtCore.QTimer()
        self.check_timer.setInterval(self.DEFAULT_TCHECK)
        self.samp_spinBox.setValue(self.DEFAULT_SAMP)

        self.current_timer = QtCore.QTimer()
        self.current_timer.setInterval(self.DEFAULT_CURRENT)
        # half = 0.5*self.DEFAULT_SAMP
        # if half > self.DEFAULT_CURRENT:
        #     timer = half
        # else:
        #     timer = self.DEFAULT_CURRENT
        # self.current_timer.setInterval(timer)
        """
        signals and events
        """
        self.port_box.installEventFilter(self)
        self.timer.timeout.connect(self.methodStreamer)
        self.plot_timer.timeout.connect(self.updatePlot)
        self.check_timer.timeout.connect(self.periodicCheck)
        self.current_timer.timeout.connect(self.updateCurrentLayout)
        self.save_button.clicked.connect(self.chooseFile)
        self.stream_button.clicked.connect(self.methodStreamer)
        self.channels_button.clicked.connect(self.detectorsWindowCaller)
        self.samp_spinBox.valueChanged.connect(self.methodSampling)
        self.coin_spinBox.valueChanged.connect(self.methodCoinWin)
        self.port_box.currentIndexChanged.connect(self.selectSerial)
        self.save_line.setDisabled(True)

        self.table = Table(self)
        self.horizontalLayout_3.addWidget(self.table)
        self.ylength = self.table.rowCount()
        self.xlength = self.table.columnCount()

        """
        menu bar
        """
        self.actionChannels.setDisabled(True)
        self.actionDefault_properties.triggered.connect(self.defaultWindowCaller)
        self.actionChannels.triggered.connect(self.detectorsWindowCaller)
        self.actionAbout.triggered.connect(self.aboutWindowCaller)
        self.actionSave_as_2.triggered.connect(self.chooseFile)
        self.actionExit.triggered.connect(self.close)

        if CURRENT_OS == "win32":
            self.menuHelp.addSeparator()
            self.actionUninstall = QtWidgets.QAction(self)
            self.actionUninstall.setText("Uninstall")
            self.menuHelp.addAction(self.actionUninstall)

            self.actionUninstall.triggered.connect(self.uninstall)

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
        self.current_layout = CurrentLabels(self.tab_current)

        self.currently_saving_fig = False
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
            self.defaultWindowCaller()

    def center(self):
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = 0.5*(screen.width() - widget.width())
        y = 0.5*(screen.height() - widget.height())
        self.move(x, y)

    def uninstall(self):
        parent = os.path.dirname(DEFAULT_PATH)
        install_location = os.path.join(parent, "install_location.dat")
        
        try:
            with open(install_location) as file_:
                path = file_.readline()
            commands = [os.path.join(path, "uninstaller.exe")]
            subprocess.Popen(commands)
            self.close()
        except WindowsError:
            e = Exception("Please start program as administrator.")
            self.errorWindow(e)

        except Exception as e:
            self.errorWindow(e)


    def local_constants(self):
        self.LOCAL_NAMES = ['DELIMITER', 'DEFAULT_SAMP', 'DEFAULT_COIN', 'MIN_SAMP',
                'MAX_SAMP', 'TABLE_YGROW', 'MIN_COIN', 'MAX_COIN', 'STEP_COIN',
                'DEFAULT_CHANNELS', 'FILE_NAME', 'USER_EMAIL', 'SEND_EMAIL', 'USE_DATETIME']

        for name in self.LOCAL_NAMES:
            try:
                value = eval(name)
                self.LOCAL_CONSTANTS[name] = value
                if type(value) != str:
                    instruction = 'self.%s = %s'%(name, str(value))
                else:
                    instruction = "self.%s = '%s'"%(name, value)
                exec(instruction)
            except NameError as e:
                save_default(None)
                DEFAULT_EXIST = False
                self.errorWindow(e)

    def updateConstants(self, constants):
        for name in self.LOCAL_NAMES:
            if name in constants:
                value = constants[name]
                self.LOCAL_CONSTANTS[name] = value
                if type(value) != str:
                    instruction = 'self.%s = %s'%(name, str(value))
                else:
                    instruction = "self.%s = '%s'"%(name, value)
                exec(instruction)

        if self.default_window.time_checkBox.isChecked():
            name, ext = self.splitExtension(self.FILE_NAME)
            self.save_line.setText("%s%s%s"%(name, strftime("%Y%m%d_%H%M"), ext))
        else:
            self.save_line.setText(self.FILE_NAME)
        self.saveLocation()

        self.samp_spinBox.setValue(self.DEFAULT_SAMP)
        self.coin_spinBox.setValue(self.DEFAULT_COIN)
        save = True
        if not DEFAULT_EXIST and not self.default_constants:
            save = False
            self.default_constants = True
        self.detectors_window.updateConstants(constants, save)

    def createFig(self):
        self.fig, (ax_counts, ax_coins) = plt.subplots(2, sharex=True, facecolor='None', edgecolor='None')
        self.canvas = FigureCanvas(self.fig)
        self.plot_layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.plot_widget, self)

        self.plot_layout.addWidget(self.toolbar)
        self.ax_counts = Axes(self.fig, self.canvas, ax_counts, self.TABLE_YGROW,
                              "Counts", self.experiment.detectors)
        self.ax_coins = Axes(self.fig, self.canvas, ax_coins, self.TABLE_YGROW,
                             "Coincidences", self.experiment.coin_channels)

        n_detectors = self.experiment.number_detectors
        colors = [self.ax_counts.colors[detector.name] for detector in self.experiment.detectors] + \
                [self.ax_coins.colors[coin.name] for coin in self.experiment.coin_channels]

        self.current_layout.setColors(colors)

        self.canvas.mpl_connect('draw_event', self._draw_event)
        # self.canvas.draw_idle()
        self.fig.set_tight_layout(True)

    def saveParam(self, label, value, units):
        current_time = strftime("%H:%M:%S", localtime())
        if value == None:
            message = label
            if units == None:
                message = "%s %s%s\n"%(current_time, self.DELIMITER, label)
        else:
            message = "%s %s%s: %d %s\n"%(current_time, self.DELIMITER, label, value, units)
        try:
            with open(self.params_file, 'a') as file_:
                file_.write(message)
        except Exception as e:
            raise SavingError(str(e))


    def splitExtension(self, text):
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

    def reallocateOutput(self, name, remove_old = False):
        params = "%s_params%s"%(name, self.EXTENSION_PARAMS)
        new = "%s%s"%(name, self.extension)
        if new != self.output_name and self.data != None:
            try:
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
            except Exception as e:
                raise SavingError(str(e))

        self.output_name = new
        self.params_file = params

    def includeParams(self, output, params, save = False, end = False):
        if self.data != None:
            if not self.data.empty:
                if save:
                    self.data.save()
            elif end:
                try:
                    os.remove(self.params_file)
                    os.remove(self.output_name)
                except:
                    pass
        elif end:
            file = open(self.params_file, 'r')
            lines = file.readlines()
            if 2 == len(lines):
                file.close()
                os.remove(self.params_file)
            else:
                file.close()


    def saveLocation(self):
        new = self.save_line.text()
        try:
            name, ext = self.splitExtension(new)
            if ext != '':
                self.extension = ext
            self.reallocateOutput(name, remove_old = True)
        except Exception as e:
            self.save_line.setText(self.output_name)
            self.errorWindow(e)

    def eventFilter(self, source, event):
        """ Creates event to handle serial combobox opening.
        """
        if (event.type() == QtCore.QEvent.MouseButtonPress and source is self.port_box):
            self.serialRefresh()
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def serialRefresh(self):
        """ Loads serial port described at user combobox.
        """
        current_ports = findPort()

        if self.serial != None:
            if self.serial.isOpenend:
                for port in self.ports:
                    if self.port in port:
                        current_ports[port] = self.port

        n = 0
        for x in current_ports.items():
            if x in self.ports.items():
                n += 1
        if n != len(current_ports) or n == 0:
            self.port_box.clear()
            self.ports = current_ports
            for port in self.ports:
                self.port_box.addItem(port)
        self.port_box.setCurrentIndex(-1)

    def selectSerial(self, index, error_capable = True):
        """ Selects port at index position of combobox.
        """
        if index != -1 and not self.first_port:
            new_port = self.port_box.itemText(index)
            try:
                new_port = self.ports[new_port]
            except:
                new_port = ''
            if new_port != '':
                self.port = new_port
                if self.serial != None:
                    try:
                        self.serial.close()
                    except CommunicationError:
                        pass
                    try:
                        self.serial.update_serial(self.port)
                        self.channels_button.setDisabled(False)
                        self.actionChannels.setDisabled(False)
                    except:
                        pass
                else:
                    try:
                        self.serial = CommunicationPort(self.port)
                        self.channels_button.setDisabled(False)
                        self.actionChannels.setDisabled(False)
                    except Exception as e:
                        e = type(e)("Serial selection: %s"%str(e))
                        if error_capable:
                            self.errorWindow(e)
            else:
                self.widgetActivate(True)

        self.first_port = False


    def widgetActivate(self, status):
        """
        most of the tools will be disabled if there is no UART detected
        """
        self.samp_spinBox.setDisabled(status)
        self.coin_spinBox.setDisabled(status)
        self.channels_button.setDisabled(status)
        self.actionChannels.setDisabled(status)
        self.streamActivate(status)

    def startExperiment(self):
        if self.format == None:
            self.streamActivate(False)
            self.createTable()
            self.header = np.zeros(self.table.number_columns, dtype=object)
            self.widgetActivate(False)
            self.format = [r"%d" for i in range(self.table.number_columns)]
            self.format[0] = "%.3f"
            self.format = self.DELIMITER.join(self.format)
            self.data = RingBuffer(TABLE_YGROW, self.table.number_columns, self.output_name, self.format)
            self.current_layout.createLabels(self.experiment.detectors, self.experiment.coin_channels)
            self.createFig()

        if self.serial != None:
            if not self.detectors_window.error_ocurred:
                self.widgetActivate(False)

    def streamActivate(self, status):
        self.stream_button.setDisabled(status)

    def createTable(self):
        self.table.createTable()
        with open(self.output_name, 'a') as file_:
            text = self.DELIMITER.join(self.table.headers)
            file_.write("%s\n"%text)

    def fileDialog(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        nameFilters = [self.SUPPORTED_EXTENSIONS[extension] for extension in self.SUPPORTED_EXTENSIONS]
        dlg.setNameFilters(nameFilters)
        dlg.selectNameFilter(self.SUPPORTED_EXTENSIONS[self.extension])
        if dlg.exec_():
            return dlg.selectedFiles()[0]
        return None

    def chooseFile(self):
        """
        user interaction with saving file
        """
        name = self.fileDialog()
        if name != None:
            try:
                extension = self.splitExtension(name)[1]
                if extension == "":
                    name += self.extension
                self.save_line.setText(name)
                self.saveLocation()
            except Exception as e:
                self.errorWindow(e)

    def detectorsWindowCaller(self):
        """
        creates a property window to define number of channels
        """
        if not self.file_exists_warning:
            if os.path.exists(r'%s'%self.output_name):
                QtWidgets.QMessageBox.warning(self, "File exists",
                    "The selected file already exists.\nData will be appended.")
            self.file_exists_warning = True
        self.detectors_window.show()

    def defaultWindowCaller(self):
        self.default_window.show()

    def aboutWindowCaller(self):
        self.about_window.show()

    def periodicCheck(self):
        try:
            self.experiment.periodicCheck()
        except Exception as e:
            self.errorWindow(e)
        samp = self.experiment.get_sampling_value()
        coin = self.experiment.get_coinwin_value()
        if self.samp_spinBox.value() != samp:
            self.samp_spinBox.setValue(samp)
        if self.coin_spinBox.value() != coin:
            self.coin_spinBox.setValue(coin)

        values = self.experiment.get_detectors_timers_values()
        self.detectors_window.setValues(values)

    def startClocks(self):
        self.timer.start()
        self.plot_timer.start()
        self.check_timer.start()
        self.current_timer.start()

    def stopClocks(self):
        self.timer.stop()
        self.plot_timer.stop()
        self.check_timer.stop()
        self.current_timer.stop()

    def updateCurrentLayout(self):
        for i in range(self.experiment.number_detectors):
            self.current_layout.changeValue(i, value = self.table.getLastRow(i+1))
        for j in range(self.experiment.number_coins):
            self.current_layout.changeValue(j+i+1, value = self.table.getLastRow(j+i+2))

    def methodStreamer(self):
        try:
            if self.timer.isActive() and self.sender() == self.stream_button:
                self.stopClocks()
                self.data.save()
                self.saveParam("Streaming stoped.", None, None)
                self.stream_button.setStyleSheet("background-color: none")

            elif not self.timer.isActive():
                self.stream_button.setStyleSheet("background-color: green")
                self.detectors_window.sendData()
                self.methodSampling(self.samp_spinBox.value(), error_capable = False)
                self.methodCoinWin(self.coin_spinBox.value(), error_capable = False)
                self.saveParam("Streaming started.", None, None)
                self.startClocks()

            time_, detectors, coins = self.experiment.current_values()

            if type(detectors) is list:
                if self.table.current_cell == 0:
                    self.init_time = time()

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

    def methodSampling(self, value, error_capable = True):
        self.timer.setInterval(value)
        # if value > self.DEFAULT_TPLOT:
        #     self.plot_timer.setInterval(value)
        # else:
        #     self.plot_timer.setInterval(self.DEFAULT_TPLOT)

        # half = 0.5*value
        # if half > self.DEFAULT_CURRENT:
        #     self.current_timer.setInterval(half)
        # else:
        #     self.current_timer.setInterval(self.DEFAULT_CURRENT)
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
            self.saveParam("Sampling Time", value, "ms")

    def methodCoinWin(self, value, error_capable = True):
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
            self.saveParam("Coincidence window", value, "ns")

    def _draw_event(self, *args):
        if self.currently_saving_fig:
            pass
        else:
            self.ax_coins.set_background()
            self.ax_counts.set_background()

    def includeLines(self):
        self.ax_coins.includeLines()
        self.ax_counts.includeLines()

    def fullPlot(self):
        self.ax_coins.clean()
        self.ax_counts.clean()
        self.ax_coins.set_limits()
        self.ax_counts.set_limits()
        self.fig.canvas.draw()
        self.ax_coins.draw_artist()
        self.ax_counts.draw_artist()
        # self.fig.canvas.flush_events()

    def restorePlot(self):
        self.fig.canvas.restore_region(self.ax_coins.background)
        self.fig.canvas.restore_region(self.ax_counts.background)
        self.ax_coins.draw_artist()
        self.ax_counts.draw_artist()
        self.ax_counts.blit()
        self.ax_coins.blit()

    def updateDataPlot(self, data, times):
        ychanged1 = self.ax_counts.update_data(times, data)
        ychanged2 = self.ax_coins.update_data(times, data[:, self.experiment.number_detectors:])
        if (ychanged1 or ychanged2) and not self.currently_saving_fig:
            self.fullPlot()
        else:
            self.restorePlot()

    def updatePlot(self):
        if self.table.current_cell > 1:
            data = self.data[:]
            times = np.arange(data.shape[0])
            if not self.ax_coins.isDataNone() and not self.ax_coins.isDataNone():
                if not np.array_equal(data, self.ax_counts.data) \
                            or not np.array_equal(data[:, self.experiment.number_detectors:], self.ax_coins.data):
                    self.updateDataPlot(data, times)

            else:
                self.updateDataPlot(data, times)

    def errorWindow(self, error):
        error_text = str(error)
        message = None

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)

        if type(error) == CommunicationError or type(error) == ExperimentError:
            self.stopClocks()
            self.serial.close()
            self.ports = {}
            self.serialRefresh()
            self.widgetActivate(True)
            self.stream_button.setStyleSheet("background-color: red")
            msg.setIcon(QtWidgets.QMessageBox.Critical)

        if type(error) != SavingError:
            self.saveParam(error_text, None, None)
        msg.setText('An Error has ocurred.\n%s'%error_text)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec_()

    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Exit',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.includeParams(self.output_name, self.params_file, save = True, end = True)
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
