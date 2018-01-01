import sys

CURRENT_OS = sys.platform

BREAKLINE = "\n"
if CURRENT_OS == "win32":
    BREAKLINE = "\r\n"

EXTENSION_DATA = '.dat'
EXTENSION_PARAMS = '_settings.txt'
SUPPORTED_EXTENSIONS = {EXTENSION_DATA : 'Plain text data file (*.dat)', '.csv' : 'CSV data files (*.csv)'}

PARAMS_HEADER = "##### SETTINGS FILE #####" + BREAKLINE + "Tausand Abacus session began at %s"

CONNECT_EMPTY_LABEL = "No devices found.\nYou might verify the device is conected, turned on, and not being\nused by other software. Also verify the driver is correctly installed."
CONNECT_LABEL = "Please select one of the available ports: "

WINDOW_NAME = "Tausand Abacus"

DATA_REFRESH_RATE = 250 # fastest data refresh rate (ms)
CHECK_RATE = 250

BUFFER_ROWS = 100

__version__ = "1.1.1"
