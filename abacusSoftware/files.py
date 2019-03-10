import os
import numpy as np
from time import localtime, strftime

import abacusSoftware.constants as constants

class File(object):
    def __init__(self, name, header = None):
        self.name = name
        self.header = header
        self.lines_written = 0

    def checkFileExists(self, name = None):
        if name == None:
            name = self.name
        if os.path.isfile(name):
            raise FileExistsError()

    def isEmpty(self):
        if self.lines_written > 0:
            return False
        return True

    def write(self, data):
        with open(self.name, "a") as file:
            if self.header != None:
                file.write(self.header + constants.BREAKLINE)
                self.header = None

            file.write(data + constants.BREAKLINE)
            self.lines_written += 1

    def npwrite(self, data, fmt):
        if self.header != None:
            with open(self.name, "a") as file:
                file.write(self.header + constants.BREAKLINE)
                self.header = None
        with open(self.name, 'ab') as f:
            np.savetxt(f, data, fmt=fmt, newline=constants.BREAKLINE)
        self.lines_written += data.shape[0]

    def changeName(self, name):
        # self.checkFileExists(name)
        if not self.isEmpty():
            os.rename(self.name, name)
        self.name = name

    def updateHeader(self, header = constants.DELIMITER.join(["Time (s)", "Counts A", "Counts B", "Coincidences AB"])):
        if self.header != None:
            self.header = header

    def delete(self):
        try:
            os.remove(self.name)
        except Exception as e:
            print(e)

class ResultsFiles(object):
    def __init__(self, prefix, data_extention, time):
        self.prefix = prefix
        self.data_extention = data_extention
        self.data_name = self.prefix + self.data_extention
        self.params_name = self.prefix + constants.EXTENSION_PARAMS

        self.data_file = File(name = self.data_name, header = constants.DELIMITER.join(["Time (s)", "Counts A", "Counts B", "Coincidences AB"]))
        self.params_file = File(name = self.params_name, header = constants.PARAMS_HEADER%time)

    def changeName(self, prefix, data_extention):
        self.data_file.changeName(prefix + data_extention)
        self.params_file.changeName(prefix + constants.EXTENSION_PARAMS)

    def getNames(self):
        return self.data_file.name, self.params_file.name

    def areEmpty(self):
        return self.data_file.isEmpty() & self.params_file.isEmpty()

    def writeData(self, text):
        self.data_file.write(text)

    def writeParams(self, text):
        current_time = strftime("%H:%M:%S", localtime())
        text = "%s, %s"%(current_time, text)
        self.params_file.write(text)

    def checkFilesExists(self):
        self.data_file.checkFileExists()
        self.params_file.checkFileExists()

class RingBuffer():
    """
    Based on https://scimusing.wordpress.com/2013/10/25/ring-buffers-in-pythonnumpy/
    """
    def __init__(self, rows, columns, combinations, file = None):
        self.data = np.zeros((rows, columns))
        self.index = 0
        self.file = file
        self.combinations = combinations
        self.data_fmt = ["%.3f"] + ["%d" for i in range(columns - 1)]
        self.fmt = constants.DELIMITER.join(self.data_fmt)
        self.size = self.data.shape[0]
        self.total_movements = 0
        self.last_saved = 0
        self.header_list = ["Time (s)", "ID"] + ["Counts %s"%letter for letter in self.combinations]
        self.header = constants.DELIMITER.join(self.header_list)

    def clear(self):
        self.index = 0
        self.total_movements = 0
        self.last_saved = 0

    def isEmpty(self):
        if self.last_saved == 0: return True
        return False

    def updateDelimiter(self, delimiter):
        self.fmt = delimiter.join(self.data_fmt)
        self.header = delimiter.join(self.header_list)
        if self.file != None:
            self.file.updateHeader(header = self.header)

    def extend(self, x):
        "adds array x to ring buffer"
        self.total_movements += 1
        x_index = (self.index + np.arange(x.shape[0])) % self.size
        self.data[x_index] = x
        self.index = x_index[-1] + 1
        if self.index == self.size:
            self.save()

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        idx = (self.index + np.arange(self.size)) %self.size
        return self.data[idx]

    def setFile(self, file):
        self.file = file
        self.file.updateHeader(self.header)

    def save(self):
        "Saves the buffer"
        if (self.file != None) and (self.index != self.last_saved):
            from_index = self.size - self.index + self.last_saved
            self.last_saved = self.index
            data = self.get()[from_index%self.size:]
            self.file.npwrite(data, self.fmt)
        else:
            print("No file has been specified.")

    def __getitem__(self, item):
        if self.total_movements > self.size:
            return self.get()
        else:
            return self.get()[self.size-self.index :]
