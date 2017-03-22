import sys
import GUI_images
from PyQt5 import QtCore, QtGui, QtWidgets

app = QtWidgets.QApplication(sys.argv)
splash_pix = QtGui.QPixmap(':/splash.png')
splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
progressBar = QtWidgets.QProgressBar(splash)
progressBar.setGeometry(250, 320, 100, 20)
#progressBar.setStyleSheet(DEFAULT_STYLE)
splash.show()
app.processEvents()
app.setWindowIcon(QtGui.QIcon(':/icon.png'))

from core import *
progressBar.setValue(15)
from mainwindow import Ui_MainWindow
progressBar.setValue(30)
from channels import Ui_Dialog
progressBar.setValue(50)

thread = threading.Thread(target=matplotlib_import)
thread.setDaemon(True)
thread.start()
i = 50
while thread.is_alive():
    if i < 95:
        i += 1
        progressBar.setValue(i)
    sleep(0.2)
from core import *
    
plt.rcParams.update({'font.size': 8})

class propertiesWindow(QtWidgets.QDialog, Ui_Dialog):
    """
        defines the channel configuration dialog
    """
    def __init__(self, parent=None):
        super(propertiesWindow, self).__init__(parent)
        self.setupUi(self)
        
        self.channel_spinBox.valueChanged.connect(self.creator)
        
        self.parent = parent
        self.current_n = 0
        self.widgets = []
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.update)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset)
        self.creator(self.channel_spinBox.value())
        self.last_time = ""
        
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
                    widget = funcs[i]("Channel %s: "%chr(self.current_n + ord("A")))
                else:
                    widget = funcs[i]()
                    if i == 1:
                        widget.setMinimum(MIN_DELAY)
                        widget.setMaximum(MAX_DELAY)
                        widget.setSingleStep(STEP_DELAY)
                    else:
                        widget.setMinimum(MIN_SLEEP)
                        widget.setMaximum(MAX_SLEEP)
                        widget.setSingleStep(STEP_SLEEP)
                        
                self.widgets[i].append(widget)
                self.gridLayout_2.addWidget(widget, self.current_n+1, i)
            self.current_n += 1    
        self.delete(n, self.N)
        
    def update(self):
        """
            sends message with the updated information
        """
        
        for i in range(1, 3):
            base = BASE_DELAY
            prefix = "delay" 
            if i == 2:
                base = BASE_SLEEP
                prefix = "sleepTime"
            for j in range(self.current_n):
                value = self.widgets[i][j].value()
                parsed = numparser(base, value)
                for k in range(4):
                    address = ADDRESS[prefix+"%s_%s"%(chr(ord('A')+i-1), COEFFS[k])]
                    try:
                        self.parent.serial.message([0x0f, address, parsed[k]])
                    except Exception as e:
                        self.parent.errorWindow(e)
        self.saveParams()
        
    def saveParams(self, delimiter = ","):
        current_time = strftime("%H:%M:%S", localtime())
        if self.last_time != current_time:
            self.last_time = current_time
            with open(self.parent.params_file, 'a') as f:
                f.write("%s\n"%self.last_time)
                for j in range(self.channel_spinBox.value()):
                    text = ""
                    for i in range(self.N):
                        widget = self.widgets[i][j]
                        if i == 0:
                            text += widget.text()
                        else:
                            if i == 1:
                                text += " %d ns"%widget.value()
                            else:
                                text += "%s %d ns"%(delimiter, widget.value())
                    f.write("%s\n"%text)        
                
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
        self.channel_spinBox.setValue(DEFAULT_CHANNELS)
        self.delete(DEFAULT_CHANNELS, self.N)
        for i in range(1, 3):
            value = DEFAULT_DELAY
            if i == 2:
                value = DEFAULT_SLEEP
            for j in range(self.current_n):
                self.widgets[i][j].setValue(value)
            
class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    """
        defines the mainwindow
    """
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        
        self.setupUi(self)
        self.output_name = self.save_line.text()
        self.params_file = "%s.params"%self.output_name[:-4]
        self.timer = QtCore.QTimer()
        self.timer.setInterval(DEFAULT_SAMP)
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.setInterval(DEFAULT_TPLOT)
        self.samp_spinBox.setValue(DEFAULT_SAMP)
        
        """
        signals and events
        """
        self.port_box.installEventFilter(self)
        self.timer.timeout.connect(self.method_streamer)
        self.plot_timer.timeout.connect(self.update_plot)
        self.table.cellChanged.connect(self.table_change)
        self.save_button.clicked.connect(self.choose_file)
        self.stream_button.clicked.connect(self.method_streamer)
        self.channels_button.clicked.connect(self.channelsCaller)
        self.samp_spinBox.valueChanged.connect(self.method_sampling)
        self.coin_spinBox.valueChanged.connect(self.method_coinWin)
        self.terminal_line.editingFinished.connect(self.terminal_handler)
        
        self.ylength = self.table.rowCount()
        self.xlength = self.table.columnCount()

        self.data = None#matrix(self.ylength, self.xlength)
        self.data_empty = True  # DEPRECATED
        self.file_changed = False
        self.header = None
        
        """
        set
        """
        self.window = None
        self.serial = None
        self.port = None
        self.ports = {}
        self.current_cell = 0
        self.last_row_saved = 0
        self.serial_refresh()
        self.terminal_text.ensureCursorVisible()
        
        """
        fig
        """
        
        self.fig, (self.ax_counts, self.ax_coins) = plt.subplots(2, sharex=True, facecolor='None',edgecolor='None')
        self.canvas = FigureCanvas(self.fig)
        self.plot_layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, 
                self.plot_widget, coordinates=True)
        self.plot_layout.addWidget(self.toolbar)
        
        self.ax_counts.set_ylabel("Counts")
        self.ax_coins.set_ylabel("Coincidences")
        self.ax_coins.set_xlabel("Time")
        self.fig.tight_layout()
        
        self.count_points = None
        self.coin_points = None
        self.count_index = []
        self.coin_index = []
        
                
    def eventFilter(self, source, event):
        """
        creates event to handle serial combobox opening
        """
        if (event.type() == QtCore.QEvent.MouseButtonPress and source is self.port_box):
            self.serial_refresh()            
        return QtWidgets.QWidget.eventFilter(self, source, event)
    
    def serial_refresh(self):
        """
        loads serial port described at user combobox
        """
        try:
            if self.serial == None:
                self.port_box.clear()
            current_ports = findport()
            n = 0
            for x in current_ports.items():
                if x in self.ports.items():
                    n += 1
            if n != len(current_ports):
                self.port_box.clear()
                self.ports = current_ports
                for port in self.ports:
                    self.port_box.addItem(port)
                
            new_port = self.port_box.currentText()
            try:
                new_port = self.ports[new_port]
            except:
                new_port = ''
            if new_port != '':
                if self.serial != None:
                    self.serial.close()
                self.port = new_port
                self.serial = serialPort(self.port, self)
                self.widget_activate(False)
                if self.window != None:
                    self.window.update()
            else:
                self.widget_activate(True)                
        except Exception as e:
            e = type(e)("Serial refresh: "+str(e))
            self.errorWindow(e)
        
    def widget_activate(self, status):
        """
        most of the tools will be disabled if there is no UART detected
        """
        self.terminal_line.setDisabled(status)
        self.samp_spinBox.setDisabled(status)
        self.coin_spinBox.setDisabled(status)
        self.channels_button.setDisabled(status)
        if status:
            self.stream_activate(status)

    def stream_activate(self, status):
        self.stream_button.setDisabled(status)
        
    def table_change(self, row, column):
        """
            saves 
        """
        if row == 0:
            self.header[column] = self.table.item(row, column).text()
        else:
            m_row = row - 1
            if m_row >= TABLE_YGROW :
                m_row = -1
                if column == 0:
                    self.data = np.roll(self.data, -1, axis = 0)
            self.data[m_row, column] = float(self.table.item(row, column).text())
        if self.current_cell == 1 and column == 0:
            savetxt(self.output_name, self.header, typ = str)
#        if (self.ylength - row) <= TABLE_YGROW:
#            self.ylength += TABLE_YGROW
#            self.data += matrix(TABLE_YGROW, self.xlength)
#            if not self.data_empty:
#                savetxt(self.output_name, self.data, delimiter='\t') 
#        if row >= 0 and column >= 0:
#            self.data[row, column] = self.table.item(row, column).text()
#            self.data[row][column] = self.table.item(row, column).text()
        self.file_changed = True
        self.data_empty = False
            
    def choose_file(self):
        """
        user interaction with saving file
        """
        name = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data File", "", "CSV data files (*.csv)")[0]
        if name != '':
            self.output_name = name
            if self.output_name[-4:] != '.csv':
                self.output_name += '.csv'
            self.save_line.setText(self.output_name)
            self.params_file = "%s.params"%self.output_name[:-4]
            
    def terminal_handler(self):
        """
        terminal interactions
        ### DEPRECATED
        """
        try:
            text = self.terminal_line.text()
            self.terminal_line.setText('')
            if text != "" and self.serial != None:
                self.terminal_text.insertPlainText("[INPUT] %s\n"%text)
                receive = False
                if text[:5] == "read ":
                    receive = True
                    text = text[5:]
                ans = self.serial.message(text, receive=receive)
                if ans != None:
                    self.terminal_text.insertPlainText("[OUT] %s\n"%ans)
                
            self.terminal_text.moveCursor(QtGui.QTextCursor.End)
        except Exception as e:
            self.errorWindow(e)
        
    def channelsCaller(self):
        """
        creates a property window to define number of channels
        """
        if self.window == None:
            self.window = propertiesWindow(self)
        self.window.show()
        self.stream_activate(False)
        N = self.window.current_n
        self.data = np.zeros((TABLE_YGROW, N + 2))
        self.header = np.zeros(N+2, dtype= object)
        
    def method_streamer(self):
        try:
            last_row = self.current_cell%TABLE_YGROW
            if self.timer.isActive() and self.sender() == self.stream_button:
                self.timer.stop()
                self.plot_timer.stop()
                if self.current_cell > TABLE_YGROW:
                    savetxt(self.output_name, self.data[self.last_row_saved:])
                else:
                    savetxt(self.output_name, self.data[self.last_row_saved:last_row])
                self.last_row_saved = last_row
                self.stream_button.setStyleSheet("background-color: none")
                
            elif not self.timer.isActive():
                self.stream_button.setStyleSheet("background-color: green")
                self.timer.start()
                self.plot_timer.start()
                
            first =  "cuentasA_LSB"
            address = ADDRESS[first]
            values = self.serial.message([0x0e, address, 6], receive = True)
            actual = self.table.rowCount() 
            if (actual - self.current_cell) <= TABLE_YGROW:
                self.table.setRowCount(TABLE_YGROW + actual)
            if last_row == 0 and not self.data_empty:
                    savetxt(self.output_name, self.data[self.last_row_saved:])
                    self.last_row_saved = last_row
                
            if type(values) is list:
                if self.current_cell == 0:
                    self.init_time = time()
                cell = QtWidgets.QTableWidgetItem("%.3f"%(time()-self.init_time))
                self.table.setItem(self.current_cell+1, 0, cell)
                self.table.scrollToItem(cell)
                for i in range(int(len(values)/2)):
                    if self.current_cell == 0:
                        for key, value in ADDRESS.items():
                            if value == values[i*2][0]:
                                break
                        self.table.setItem(0, i+1, QtWidgets.QTableWidgetItem(key[:-4]))
                        self.table.setItem(0, 0, QtWidgets.QTableWidgetItem("Time (s)"))
                    value = "%d"%int("%02X"%values[2*i][1], 16)#+"%02X"%values[2*i+1][1]), 16)
                    cell = QtWidgets.QTableWidgetItem(value)
                    self.table.setItem(self.current_cell+1, i+1, cell)
                    cell.setFlags(QtCore.Qt.ItemIsEnabled)
                self.current_cell += 1
                self.current_label.setText("value")
#                self.update_plot()
        except Exception as e:
            self.errorWindow(e)
            
    def method_sampling(self, value):
        self.timer.setInterval(value)
        if value > DEFAULT_TPLOT:
            self.plot_timer.setInterval(value)
        else:
            self.plot_timer.setInterval(DEFAULT_TPLOT)
        try:
            parsed = numparser(BASE_SAMPLING, value)
            for i in range(4):
                address = ADDRESS["samplingTime_%s"%COEFFS[i]]
                self.serial.message([0x0f, address, parsed[i]])
        except Exception as e:
            self.errorWindow(e)
            
        savetxt(self.params_file, ["Sampling Time: %d ms"%value], typ = str)
        
    def method_coinWin(self, value):
        try:
            parsed = numparser(BASE_COINWIN, value)
            for i in range(4):
                address = ADDRESS["coincidenceWindow_%s"%COEFFS[i]]
                self.serial.message([0x0f, address, parsed[i]])
        except Exception as e:
            self.errorWindow(e)
        savetxt(self.params_file, ["Coincidence window: %d ns"%value], typ = str)
            
    def update_plot(self):
        if self.coin_points == None and self.count_points == None:
            self.count_points = []
            self.coin_points = []
            for (i, column) in enumerate(self.header):
                if 'cuentas' in column:
                    point = self.ax_counts.plot([],[], "-o", ms=3, label = column)[0]
                    self.count_points.append(point)
                    self.count_index.append(i)
                elif 'coin' in column:
                    point = self.ax_coins.plot([],[], "-o", ms=3, label = column)[0]
                    self.coin_points.append(point)
                    self.coin_index.append(i)
            self.ax_counts.legend(loc = 2)
            self.ax_coins.legend(loc = 2)
            
            
        if self.current_cell > 2:
            max_count = []
            min_count = []
            max_coin = []
            min_coin = []
            if self.current_cell < TABLE_YGROW:
                until = self.current_cell
            else:
                until = TABLE_YGROW
#            times = [float(self.data[j][0])  for j in range(1, self.current_cell)]
            times = self.data[:until, 0]
            for (i, index) in enumerate(self.count_index):
#                data = [int(self.data[j][index]) for j in range(1, self.current_cell)]
                data = self.data[:until, index]
                max_count.append(max(data))
                min_count.append(min(data))
                self.count_points[i].set_data(times, data)
            for (i, index) in enumerate(self.coin_index):
#                data = [int(self.data[j][index]) for j in range(1, self.current_cell)]
                data = self.data[:until, index]
                max_coin.append(max(data))
                min_coin.append(min(data))
                self.coin_points[i].set_data(times, data)
            max_count = max(max_count)
            min_count = min(min_count)
            max_coin = max(max_coin)
            min_coin = min(min_coin)
            if max_count*1.25 > self.ax_counts.get_ylim()[1] or min_count*0.75 < self.ax_counts.get_ylim()[0]:
                self.ax_counts.set_ylim(min_count, max_count*1.25)
            self.ax_counts.set_ylim(min_count, max_count)
            self.ax_coins.set_ylim(min_coin, max_coin)
            if self.current_cell > 80:
                self.ax_counts.set_xlim(times[-80], times[-1])
                self.ax_coins.set_xlim(times[-80], times[-1])
            else:
                self.ax_counts.set_xlim(0, times[-1])
                self.ax_coins.set_xlim(0, times[-1])
            self.canvas.draw()
        
    def errorWindow(self, error):
        msg = QtWidgets.QMessageBox()
        error = str(error)
        if "write" in error or "Serial" in error:
            self.serial = None
            self.ports = {}
        self.timer.stop()
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
            if self.file_changed:
                savetxt(self.output_name, self.data[self.current_cell%TABLE_YGROW:], delimiter='\t')
                with open(self.output_name, "a") as file:
                    file.write("##### PARAMETERS USED #####\n")
                    with open(self.params_file, "r") as params:
                        for line in params:
                            file.write(line)
                try:
                    os.remove(self.params_file)
                except:
                    pass
            event.accept()
        else:
            event.ignore()
            
main = Main()
progressBar.setValue(100)
main.show()
splash.close()
sys.exit(app.exec_())
