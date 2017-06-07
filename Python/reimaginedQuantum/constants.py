#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import getpass
from .specialfolders import *

CURRENT_OS = sys.platform

ADDRESS = {'delayA_ns': 0,
           'delayA_us': 1,
           'delayA_ms': 2,
           'delayA_s': 3,
           'delayB_ns': 4,
           'delayB_us': 5,
           'delayB_ms': 6,
           'delayB_s': 7,
           'sleepTimeA_ns': 8,
           'sleepTimeA_us': 9,
           'sleepTimeA_ms': 10,
           'sleepTimeA_s': 11,
           'sleepTimeB_ns': 12,
           'sleepTimeB_us': 13,
           'sleepTimeB_ms': 14,
           'sleepTimeB_s': 15,
           'samplingTime_ns': 16,
           'samplingTime_us': 17,
           'samplingTime_ms': 18,
           'samplingTime_s': 19,
           'coincidenceWindow_ns': 20,
           'coincidenceWindow_us': 21,
           'coincidenceWindow_ms': 22,
           'coincidenceWindow_s': 23,
           'countsA_LSB': 24,
           'countsA_MSB': 25,
           'countsB_LSB': 26,
           'countsB_MSB': 27,
           'coincidencesAB_LSB': 28,
           'coincidencesAB_MSB': 29} #: Memory addresses

DELIMITER = "\t"

READ_VALUE = 0x0e #: Reading operation signal
WRITE_VALUE = 0x0f #: Writing operation signal
START_COMMUNICATION = 0x02 #: Begin message signal
END_COMMUNICATION = 0x04 #: End of message
MAXIMUM_WRITING_TRIES = 20 #: Number of tries done to write a value

"""
propertiesWindow
"""
MIN_DELAY = 0 #: Minimum delay time value.
MAX_DELAY = 200 #: Maximum delay time value.
STEP_DELAY = 5 #: Increase ratio on the delay time value.
DEFAULT_DELAY = 100 #: Default delay time value (ns).
MIN_SLEEP = 0 #: Minimum sleep time value.
MAX_SLEEP = 200 #: Maximum sleep time value.
STEP_SLEEP = 5 #: Increase ratio on the sleep time value.
DEFAULT_SLEEP = 25 #: Default sleep time value (ns).

DEFAULT_CHANNELS = 2 #: Default number of channels
MIN_CHANNELS = 2 #: Minimum number of channels
MAX_CHANNELS = 8 #: Maximum number of channels
"""
main
"""
MIN_SAMP = 20
MAX_SAMP = 1000000
DEFAULT_SAMP = 50

MIN_COIN = 5
MAX_COIN = 1000000
DEFAULT_COIN = 5
STEP_COIN = 5

FILE_NAME = 'Output.dat'
if CURRENT_OS == "win32":
    FILE_NAME = "%s\%s"%(get_path(FOLDERID.Documents).replace("Default", getpass.getuser()), FILE_NAME)

USER_EMAIL = ''
SEND_EMAIL = True

TABLE_YGROW = 100

"""
Constant to save
"""
DEFAULT_TO_SAVE = ['DEFAULT_CHANNELS', 'DEFAULT_DELAY', 'DEFAULT_SLEEP', 'DEFAULT_SAMP',
                                'DEFAULT_COIN', 'USER_EMAIL', 'FILE_NAME', 'SEND_EMAIL']

if CURRENT_OS == "win32":
    _path = get_path(FOLDERID.LocalAppData).replace("Default", getpass.getuser())
    DEFAULT_PATH = "%s\ReimaginedQuantum\default.py"%_path
else:
    DEFAULT_PATH = "default.py"
