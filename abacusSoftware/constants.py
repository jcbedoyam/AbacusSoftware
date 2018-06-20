import sys
import os

__version__ = "1.2.4"

CURRENT_OS = sys.platform
DIRECTORY = os.path.dirname(sys.executable)
SETTINGS_PATH = os.path.join(DIRECTORY, "settings.py")

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

WINDOW_NAME = "Tausand Abacus"

DATA_REFRESH_RATE = 250 # fastest data refresh rate (ms)
CHECK_RATE = 250

BUFFER_ROWS = 10000

WIDGETS_NAMES = ["checkBox", "lineEdit", "comboBox", "spinBox"]
WIDGETS_GET_ACTIONS = ["self.%s.isChecked()", "self.%s.text()", "self.%s.currentText()", "self.%s.value()"]
WIDGETS_SET_ACTIONS = ["class_.%s.setChecked(%s)", "class_.%s.setText('%s')", "class_.%s.setCurrentIndex(class_.%s.findText('%s'))", "class_.%s.setValue(%d)"]
