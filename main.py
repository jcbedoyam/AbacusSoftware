import sys
from core import *
from PyQt5 import QtCore, QtGui, QtWidgets

app = QtWidgets.QApplication(sys.argv)
app.processEvents()

from mainwindow import Ui_MainWindow
from channels import Ui_Dialog

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
        
    def creator(self, n):
        funcs = [QtWidgets.QLabel, QtWidgets.QSpinBox, QtWidgets.QSpinBox]
        
        N = len(funcs)
        if len(self.widgets) == 0:
            self.widgets = [[] for i in range(N)]
        
        while self.current_n < n:
            for i in range(N):
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
        self.delete(n)
                        
    def update(self):
        try:
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
                        self.parent.serial.message([0x0f, address, parsed[k]])
        except Exception as e:
            self.parent.errorWindow(e)
                
    def delete(self, n):
        while self.current_n > n:
            for i in range(N):
                widget = self.widgets[i][self.current_n-1]
                self.gridLayout_2.removeWidget(widget)
                widget.deleteLater()
                del self.widgets[i][self.current_n-1]
            self.current_n -= 1
                
    def reset(self):
        self.channel_spinBox.setValue(DEFAULT_CHANNELS)
        self.delete(DEFAULT_CHANNELS)
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
        self.timer = QtCore.QTimer()
        self.timer.setInterval(DEFAULT_SAMP)
        self.samp_spinBox.setValue(DEFAULT_SAMP)
        
        """
        signals and events
        """
        self.port_box.installEventFilter(self)
        self.timer.timeout.connect(self.method_streamer)
        self.table.cellChanged.connect(self.table_change)
        self.save_button.clicked.connect(self.choose_file)
        self.stream_button.clicked.connect(self.method_streamer)
        self.channels_button.clicked.connect(self.channelsCaller)
#        self.samp_spinBox.valueChanged.connect(self.timer.setInterval)
        self.samp_spinBox.valueChanged.connect(self.method_sampling)
        self.coin_spinBox.valueChanged.connect(self.method_coinWin)
        self.terminal_line.editingFinished.connect(self.terminal_handler)
        
        self.ylength = self.table.rowCount()
        self.xlength = self.table.columnCount()

        self.data = matrix(self.ylength, self.xlength)
        
        """
        set
        """
        self.window = None
        self.serial = None
        self.current_cell = 0
        self.serial_refresh()
        self.terminal_text.ensureCursorVisible()
                
    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and source is self.port_box):
            self.serial_refresh()            
        return QtWidgets.QWidget.eventFilter(self, source, event)
    
    def serial_refresh(self):
        try:
            self.port_box.clear()
            self.ports = findport()
            for port in self.ports:
                self.port_box.addItem(port)
            self.port = self.port_box.currentText()
            if self.port != '':
                self.serial = serialPort(self.port, self)
                self.widget_activate(False)
                if self.window != None:
                    self.window.update()
            else:
                self.widget_activate(True)
                if self.serial != None:
                    self.serial.close()
        except Exception as e:
            self.errorWindow(e)
        
    def widget_activate(self, status):
        self.terminal_line.setDisabled(status)
        self.samp_spinBox.setDisabled(status)
        self.coin_spinBox.setDisabled(status)
        self.channels_button.setDisabled(status)
        self.stream_button.setDisabled(status)
        
    def table_change(self, row, column):
        if self.ylength == row + 10:
            self.data += matrix(self.ylength, self.xlength)
        self.data[row][column] = self.table.item(row, column).text()
        savetxt(self.output_name, self.data, delimiter=',')        

    def choose_file(self):
        name = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data File", "", "CSV data files (*.csv)")[0]
        if name != '':
            self.output_name = name
            if self.output_name[-4:] != '.csv':
                self.output_name += '.csv'
            self.save_line.setText(self.output_name)
            
    def terminal_handler(self):
        text = self.terminal_line.text()
        self.terminal_line.setText('')
        if text != "" and self.serial != None:
            self.terminal_text.insertPlainText("[INPUT] %s\n"%text)
            ans = self.serial.message([0x0f, b'x24', text])
            if ans != "":
                self.terminal_text.insertPlainText("[OUT] %s\n"%ans)
            
        self.terminal_text.moveCursor(QtGui.QTextCursor.End)
        
    def channelsCaller(self):
        if self.window == None:
            self.window = propertiesWindow(self)
        self.window.show()
        
    def method_streamer(self):
        if self.timer.isActive() and self.sender() == self.stream_button:
            self.timer.stop()
        elif not self.timer.isActive():
            self.timer.start()
        first =  "cuentasA_LSB"
        address = ADDRESS[first]
        values = self.serial.message([0x0e, address, 0], receive = True)
        
        actual = self.table.rowCount() 
        if actual == self.current_cell + 10:
            self.table.setRowCount(self.ylength+actual) 
            
        try:
            for i in range(len(values)):
                if self.current_cell == 0:
                    for key, value in ADDRESS.items():
                        if value == values[i][0]:
                            break
                    self.table.setItem(0, i, QtWidgets.QTableWidgetItem(key))
                cell = QtWidgets.QTableWidgetItem("%d"%values[i][1])
                self.table.setItem(self.current_cell+1, i, cell)
                self.table.scrollToItem(cell)
                cell.setFlags(QtCore.Qt.ItemIsEnabled)
            self.current_cell += 1
        except Exception as e:
            self.errorWindow(e)
        
    def method_sampling(self, value):
        self.timer.setInterval(value)
        try:
            parsed = numparser(BASE_SAMPLING, value)
            for i in range(4):
                address = ADDRESS["samplingTime_%s"%COEFFS[i]]
                self.serial.message([0x0f, address, parsed[i]])
        except Exception as e:
            self.errorWindow(e)
        
    def method_coinWin(self, value):
        try:
            parsed = numparser(BASE_COINWIN, value)
            for i in range(4):
                address = ADDRESS["coincidenceWindow_%s"%COEFFS[i]]
                self.serial.message([0x0f, address, parsed[i]])
        except Exception as e:
            self.errorWindow(e)
            
    def errorWindow(self, error):
        msg = QtWidgets.QMessageBox()
        self.serial_refresh()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        
        msg.setText("An Error has ocurred.")
        msg.setInformativeText(str(error))
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec()

main = Main()
main.show()
sys.exit(app.exec_())
