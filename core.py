#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 11:56:54 2017

@author: juan
"""

import os
import sys
import serial
import codecs
import threading
from time import sleep, localtime, strftime, time
import serial.tools.list_ports as find_ports

BAUDRATE = 115200 #: Default baudrate for the serial port communication
TIMEOUT = 0.02 #: Maximum time without answer from the serial port
BOUNCE_TIMEOUT = 20 #: Number of times a specific transmition is tried
BASE_DELAY = 1e-9 #: Default channnel delay time (seconds)
BASE_SLEEP = 1e-9 #: Default channel sleep time (seconds)
BASE_SAMPLING = 1e-3 #: Default sampling time (seconds)
BASE_COINWIN = 1e-9 #: Default coincidence window (seconds)
DEFAULT_CHANNELS = 2 #: Default number of channels
MIN_DELAY = 0
MAX_DELAY = 200
STEP_DELAY = 5
DEFAULT_DELAY = 0
MIN_SLEEP = 0
MAX_SLEEP = 200
STEP_SLEEP = 5
DEFAULT_SLEEP = 0
DEFAULT_SAMP = 500
DEFAULT_TPLOT = 100
TABLE_YGROW = 100
VALUES_TO_SHOW = 80

if VALUES_TO_SHOW > TABLE_YGROW:
    VALUES_TO_SHOW = TABLE_YGROW

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
           'cuentasA_LSB': 24,
           'cuentasA_MSB': 25,
           'cuentasB_LSB': 26,
           'cuentasB_MSB': 27,
           'coincidencesAB_LSB': 28,
           'coincidencesAB_MSB': 29}

DEFAULT_STYLE = """
QProgressBar{
    border: 2px solid grey;
    border-radius: 5px;
    text-align: center
}

QProgressBar::chunk {
    width: 100px;
}
"""

COEFFS = ['ns', 'us', 'ms', 's']

CURRENT_OS = sys.platform
if CURRENT_OS == 'win32':
    import ctypes
    myappid = 'quantum.quantum.JuanBarbosa.01' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    
def matplotlib_import():
    """ Imports matplotlib and NumPy.
    
    Useful to be combined with threading processes.
    """
    global plt, FigureCanvas, NavigationToolbar, np
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import (
                            FigureCanvasQTAgg as FigureCanvas,
                            NavigationToolbar2QT as NavigationToolbar)

def matrix(y, x):
    """ Creates a python list with (x)x(y) dimentions.
    
    DEPRECATED.
    NumPy matrices are used insted.
    """
    mat = [['' for i in range(x)] for i in range(y)]
    return mat

def savetxt(file, matrix, delimiter = '\t', typ = float):
    """ Saves data to a text file.
    
    Used to save matrix contents to plain text files. 
    Depening whether or not matrix contains strings or floats
    uses np.savetxt function.
    """
    if typ is str:
        with open(file, 'a') as _file:
            text = delimiter.join(matrix)
            _file.write("%s\n"%text)
    else:
        with open(file, 'ab') as _file:
            np.savetxt(_file, matrix, fmt = '%.3f', delimiter = delimiter)

def loadtxt(file, delimiter = '\t'):
    rows = []
    with open(file, 'r')as file:
        for line in file:
            line = file.readline()
            line = line.split(delimiter)
            rows.append(line)
    return rows

def findport():
    ports_objects = list(find_ports.comports())
    ports = {}
    for i in range(len(ports_objects)):
        port = ports_objects[i]
        ports["%s (%s)"%(port.description, port.device)] = port.device 
    return ports

class serialPort():
    def __init__(self, port, parent=None):
        self.parent = parent
        self.port = port
        self.serial = None
        if self.port != '':
            self.serial = serial.Serial(port=port, baudrate=BAUDRATE, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS, timeout=TIMEOUT)
            
    def close(self):
        self.serial.close()
        
    def message(self, info, read = False, receive = False):
        def sender():            
            if type(info) is list:
                if not read:
                    value = "%04X"%info[2]
                    msb = int(value[:2], 16)
                    lsb = int(value[2:], 16)
                    encoded = [0x02, info[0], info[1], msb, lsb, 0x04]
                else:
                    check = hex(sum(info[1:]))[-2:]
                    check = 0xff - int(check, 16)
                    encoded = [0x7E] + info + [check]
    
                encoded = serial.to_bytes(encoded)
            else:
                encoded = info.encode()
            self.serial.write(encoded)      
        def receiver():
            hexa = [codecs.encode(self.serial.read(1), "hex_codec").decode()]
            ints = []
            if hexa[0] == '':
                raise Exception('Timeout: device does not answer.')
            if hexa[0] == '7e':
                while True:
                    byte = codecs.encode(self.serial.read(1), "hex_codec").decode()
                    if byte == '':
                        break
                    hexa.append(byte)
                    ints.append(int(byte, 16))
                check = int(("%02X"%sum(ints[1:-1]))[-2:], 16) + ints[-1]
                if check == 0xff:
                    hexa = hexa[2:-1]
                    ans = []
                    for i in range(int(len(hexa)/3)):
                        channel = int(hexa[3*i], 16)
                        value = hexa[3*i+1] + hexa[3*i+2]
                        ans.append([channel, value])
                    return ans                
        sender()          
        if receive:
            n = 0
            while n < BOUNCE_TIMEOUT:
                try:
                    return receiver()
                except Exception as e:
                    n += 1
                    sender()
                    if n < BOUNCE_TIMEOUT:
                        continue
                    raise Exception(e)                    
        else:
            return None
        

def numparser(base, num):
    first_order = int(base*num*1e9)
    micro, nano = divmod(first_order, 1000)
    unit, mili = divmod(int(micro/1000), 1000)
    if micro >= 1000:
        micro = 0
        
    return nano, micro, mili, unit
