import os
import sys
import pyAbacus as abacus

__version__ = "1.4.0"

CURRENT_OS = sys.platform
DIRECTORY = os.path.dirname(sys.executable)
SETTINGS_PATH = os.path.join(DIRECTORY, "settings.py")
LOGFILE_PATH = "logfile.txt"
# LOGFILE_PATH = os.path.join(DIRECTORY, "logfile.txt")

if abacus.constants.DEBUG:
    print("SETTINGS PATH ON:", SETTINGS_PATH)

SETTING_FILE_EXISTS = False

BREAKLINE = "\n"
if CURRENT_OS == "win32":
    BREAKLINE = "\r\n"

EXTENSION_DATA = '.dat'
PARAMS_SUFFIX = "_settings"
FILE_PREFIX = "abacusdata"
EXTENSION_PARAMS = PARAMS_SUFFIX + '.txt'
SUPPORTED_EXTENSIONS = {'.dat': 'Plain text data file (*.dat)', '.csv' : 'CSV data files (*.csv)'}

DELIMITER = ","
DELIMITERS = [",", ";", "Tab", "Space"]

PARAMS_HEADER = "##### SETTINGS FILE #####" + BREAKLINE + "Tausand Abacus session began at %s"

CONNECT_EMPTY_LABEL = "No devices found.\nYou might verify the device is conected, turned on, and not being\nused by other software. Also verify the driver is correctly installed."
CONNECT_LABEL = "Please select one of the available ports: "

WINDOW_NAME = "Tausand Abacus Sofware %s"%__version__

DATA_REFRESH_RATE = 250 # fastest data refresh rate (ms)
CHECK_RATE = 250

BUFFER_ROWS = 10000

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#8c564b",
        "#e377c2", "#7f7f7f", "#bcdb22", "#14becf"]

WIDGETS_NAMES = ["checkBox", "lineEdit", "comboBox", "spinBox"]
WIDGETS_GET_ACTIONS = ["self.%s.isChecked()", "self.%s.text()", "self.%s.currentText()", "self.%s.value()"]
WIDGETS_SET_ACTIONS = ["class_.%s.setChecked(%s)", "class_.%s.setText('%s')", "class_.%s.setCurrentIndex(class_.%s.findText('%s'))", "class_.%s.setValue(%d)"]

NUMBER_OF_TRIES = 10

ICON = None

IS_LIGHT_THEME = False
