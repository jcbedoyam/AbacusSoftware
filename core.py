#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 11:56:54 2017

@author: juan
"""

import os
import serial
import time

"""
constants
"""
BAUDRATE = 115200
TIMEOUT = 0.2
BASE_DELAY = 1e-9
BASE_SLEEP = 1e-9
BASE_SAMPLING = 1e-3
BASE_COINWIN = 1e-9
DEFAULT_CHANNELS = 2
MIN_DELAY = 0
MAX_DELAY = 200
STEP_DELAY = 5
DEFAULT_DELAY = 0
MIN_SLEEP = 0
MAX_SLEEP = 200
STEP_SLEEP = 5
DEFAULT_SLEEP = 0

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

COEFFS = ['ns', 'us', 'ms', 's']

def matrix(y, x):
    mat = [['' for i in range(x)] for i in range(y)]
    return mat

def savetxt(file, matrix, delimiter = '\t'):
    with open(file, 'w') as file:
        for row in matrix:
            text = delimiter.join(row)
            file.write(text+'\n')

def loadtxt(file, delimiter = '\t'):
    rows = []
    with open(file, 'r')as file:
        for line in file:
            line = file.readline()
            line = line.split(delimiter)
            rows.append(line)
    return rows

def findport():
    multiple = os.popen('./device.sh | grep UART').read().split('\n')
    ports = []
    for port in multiple:
        if port != '':
            ports.append(port.split(' ', 1)[0])
    return ports

class serialPort():
    def __init__(self, port, parent=None):
        self.parent = parent
        self.port = port
        self.serial = None
        if self.port != '':
            self.serial = serial.Serial(port=port, baudrate=BAUDRATE, parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS, timeout=TIMEOUT)
            
    def close(self):
        self.serial.close()
        
    def message(self, info, read = False):
        if type(info) is list:
            if not read:
                value = "%04X"%info[2]
                msb = int(value[:2], 16)
                lsb = int(value[2:], 16)
                encoded = [0x02, info[0], info[1], msb, lsb, 0x04]
            else:
                check = "%02X"%sum(info[1:])
                encoded = [0x7E, info, int(check, 16)]
                encoded = [val for sublist in encoded for val in sublist]
                print(encoded)

            encoded = serial.to_bytes(encoded)
        else:
            encoded = info.encode()
            
        self.serial.write(encoded)
        
        if read:
            return self.serial.readline().decode()[:-1]
        else:
            return None

def numparser(base, num):
    first_order = int(base*num*1e9)
    micro, nano = divmod(first_order, 1000)
    unit, mili = divmod(int(micro/1000), 1000)
    if micro >= 1000:
        micro = 0
        
    return nano, micro, mili, unit
