import os
from time import asctime, localtime

from constants import PARAMS_HEADER, EXTENSION_PARAMS

class File(object):
    def __init__(self, name, header = None):
        self.name = name
        self.header = header

        self.lines_written = 0

        self.checkFileExists(name)

    def checkFileExists(self, name):
        if os.path.isfile(name):
            raise FileExistsError()

    def isEmpty(self):
        if self.lines_written > 0:
            return False
        return True

    def write(self, data):
        with open(self.name, "a") as file:
            if self.header != None:
                file.write(self.header)
                self.header = None

            file.write(data)
            self.lines_written += 1

    def changeName(self, name):
        self.checkFileExists(name)
        if not self.isEmpty():
            os.rename(self.name, name)
        self.name = name

    def __del__(self):
        if not self.isEmpty():
            try: os.remove(self.name)
            except Exception as e: print(e)

class ResultsFiles(object):
    def __init__(self, prefix, data_extention):
        self.prefix = prefix
        self.data_extention = data_extention
        self.data_name = self.prefix + self.data_extention
        self.params_name = self.prefix + EXTENSION_PARAMS

        self.data_file = File(name = self.data_name)

        self.params_file = File(name = self.params_name, header = PARAMS_HEADER%asctime(localtime()))

    def changeName(self, prefix, data_extention):
        self.data_file.changeName(prefix + data_extention)
        self.params_file.changeName(prefix + EXTENSION_PARAMS)

    def getNames(self):
        return self.data_file.name, self.params_file.name

    def areEmpty(self):
        return self.data_file.isEmpty() & self.params_file.isEmpty()
