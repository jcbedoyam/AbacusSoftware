import os
import abacusSoftware.constants as constants
import pyAbacus as abacus
from PyQt5 import QtGui

def timeInUnitsToMs(time):
    value = 0
    if 'ms' in time:
        value = int(time.replace('ms', ''))
    elif 's' in time:
        value = int(time.replace('s', ''))*1000
    return value

def setSamplingComboBox(comboBox, value = abacus.DEFAULT_SAMP):
    comboBox.clear()

    model = comboBox.model()
    for row in abacus.SAMP_VALUES:
        item = QtGui.QStandardItem(row)
        if timeInUnitsToMs(row) < abacus.SAMP_CUTOFF:
            item.setBackground(QtGui.QColor('red'))
            item.setForeground(QtGui.QColor('white'))
        model.appendRow(item)

    comboBox.setCurrentIndex(comboBox.findText(value))

def setCoincidenceSpinBox(spinBox, value = abacus.DEFAULT_COIN):
    spinBox.setMinimum(abacus.MIN_COIN)
    spinBox.setMaximum(abacus.MAX_COIN)
    spinBox.setSingleStep(abacus.STEP_COIN)
    spinBox.setValue(value)

def setDelaySpinBox(spinBox, value = abacus.DEFAULT_DELAY):
    spinBox.setMinimum(abacus.MIN_DELAY)
    spinBox.setMaximum(abacus.MAX_DELAY)
    spinBox.setSingleStep(abacus.STEP_DELAY)
    spinBox.setValue(value)

def setSleepSpinBox(spinBox, value = abacus.DEFAULT_SLEEP):
    spinBox.setMinimum(abacus.MIN_SLEEP)
    spinBox.setMaximum(abacus.MAX_SLEEP)
    spinBox.setSingleStep(abacus.STEP_SLEEP)
    spinBox.setValue(value)

def findWidgets(class_, widget):
    return [att for att in dir(class_) if widget in att]

def unicodePath(path):
    return path.replace("\\", "/")

def readConstantsFile():
    if os.path.exists(constants.SETTINGS_PATH):
        with open(constants.SETTINGS_PATH) as file:
            for line in file:
                try:
                    exec("constants.%s"%line)
                except SyntaxError as e:
                    pass
        constants.SETTING_FILE_EXISTS = True
    else:
        print("Settings file not found at: %s"%constants.SETTINGS_PATH)

def updateConstants(class_):
    for (name, action) in zip(constants.WIDGETS_NAMES, constants.WIDGETS_SET_ACTIONS):
        attributes = findWidgets(class_, name)
        for att in attributes:
            if att in dir(constants):
                val = eval("constants.%s"%att)
                if name != "comboBox":
                    exec(action%(att, val))
                else:
                    exec(action%(att, att, val))

def findDocuments():
    if constants.CURRENT_OS == "win32":
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
        buf = buf.value
    else:
        buf = os.path.expanduser("~")
    return buf
