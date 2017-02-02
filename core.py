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
BAUDRATE = 9600
TIMEOUT = 0.2

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
    port = os.popen('./device.sh | grep UART').read()
    port = port.split(' ', 1)[0]
    return port

def createSerial(port):
    ser = None
    if port != '':
        ser = serial.Serial(port=port, baudrate=BAUDRATE, parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS, timeout=TIMEOUT)
    return ser

def sendmessage(ser, text):
    text = text.encode()
    ser.write(text + b'\n')
    return ser.readline().decode()[:-1]
