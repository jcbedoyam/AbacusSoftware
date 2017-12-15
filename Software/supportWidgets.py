class Table(QtWidgets.QTableWidget):
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
