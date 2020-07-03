import os
import abacusSoftware.constants as constants
import pyAbacus as abacus
from PyQt5 import QtGui

def timeInUnitsToMs(time):
    value = 0
    if 'ms' in time:
        value = int(time.replace(' ms', ''))
    elif 's' in time:
        value = float(time.replace(' s', ''))
        value = int(1000 * value)
    return value

def setSamplingComboBox(comboBox, values = abacus.constants.SAMPLING_VALUES, default_value = abacus.constants.SAMPLING_DEFAULT_VALUE):
    comboBox.clear()

    model = comboBox.model()
    for row in values:
        if row < 1000:
            item = QtGui.QStandardItem("%d ms" % row)
        elif row < 10000:
            item = QtGui.QStandardItem("%.1f s" % (row / 1000))
        else:
            item = QtGui.QStandardItem("%d s" % (row / 1000))
        # if row < abacus.SAMP_CUTOFF:
        #     item.setBackground(QtGui.QColor('red'))
        #     item.setForeground(QtGui.QColor('white'))
        model.appendRow(item)
    if default_value < 1000: unit = "ms"
    else: unit = "s"; value = default_value // 1000
    comboBox.setCurrentIndex(comboBox.findText("%d %s"%(value, unit)))

def setCoincidenceSpinBox(spinBox, value = abacus.constants.COINCIDENCE_WINDOW_DEFAULT_VALUE):
    spinBox.setMinimum(abacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE)
    spinBox.setMaximum(abacus.constants.COINCIDENCE_WINDOW_MAXIMUM_VALUE)
    spinBox.setSingleStep(abacus.constants.COINCIDENCE_WINDOW_STEP_VALUE)
    spinBox.setValue(value)
    
def setDelaySpinBox(spinBox, value = abacus.constants.DELAY_DEFAULT_VALUE):
    spinBox.setMinimum(abacus.constants.DELAY_MINIMUM_VALUE)
    spinBox.setMaximum(abacus.constants.DELAY_MAXIMUM_VALUE)
    spinBox.setSingleStep(abacus.constants.DELAY_STEP_VALUE)
    spinBox.setValue(value)    

def setSleepSpinBox(spinBox, value = abacus.constants.SLEEP_DEFAULT_VALUE):
    spinBox.setMinimum(abacus.constants.SLEEP_MINIMUM_VALUE)
    spinBox.setMaximum(abacus.constants.SLEEP_MAXIMUM_VALUE)
    spinBox.setSingleStep(abacus.constants.SLEEP_STEP_VALUE)
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
                    exec("constants.%s" % line)
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
                    try: #if the element does not exist, skip. Example: sleep_C in a 2ch device
                        exec(action%(att, val)) 
                    except:
                        pass
                            
                else:
                    try: #if the element does not exist, skip. Example: sleep_C in a 2ch device
                        exec(action%(att, att, val))
                    except:
                        pass

def findDocuments():
    if constants.CURRENT_OS == "win32":
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
        buf = buf.value
    else:
        buf = os.path.expanduser("~")
    return buf
