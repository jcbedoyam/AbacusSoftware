import sys
from core import *
from PyQt5 import QtCore, QtGui, QtWidgets
app = QtWidgets.QApplication(sys.argv)
app.processEvents()

from mainwindow import Ui_MainWindow

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        
        self.setupUi(self)
        self.output_name = self.save_line.text()
        
        """
        signals and events
        """
        self.table.cellChanged.connect(self.table_change)
        self.refresh_button.clicked.connect(self.serial_refresh)
        self.save_button.clicked.connect(self.choose_file)
        self.terminal_line.editingFinished.connect(self.terminal_handler)
        
        self.ylength = self.table.rowCount()
        self.xlength = self.table.columnCount()

        self.data = matrix(self.ylength, self.xlength)
        
        """
        set
        """
        self.serial_refresh()
        self.terminal_text.ensureCursorVisible()
            
    def serial_refresh(self):
        self.ports = findport()
        for port in self.ports:
            self.port_box.addItem(port)
        self.port = self.port_box.currentText()
        self.serial = createSerial(self.port)
        if self.serial != None:
            self.terminal_line.setDisabled(False)
                
    def table_change(self, row, column):
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
            ans = sendmessage(self.serial, text)
            if ans != "":
                self.terminal_text.insertPlainText("[OUT] %s\n"%ans)
            
        self.terminal_text.moveCursor(QtGui.QTextCursor.End)        

main = Main()
main.show()
sys.exit(app.exec_())
