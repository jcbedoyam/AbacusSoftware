#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 11:19:25 2017

@author: juan
"""

"""
*Required modules*
"""
import os
import sys
import serial
import codecs
import threading
from time import sleep, localtime, strftime, time
import serial.tools.list_ports as find_ports


"""
*Global constants*
"""


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
           'coincidencesAB_MSB': 29}

class communication_port(object):
    """
    Constants
    """
    BAUDRATE = 115200 #: Default baudrate for the serial port communication
    TIMEOUT = 0.02 #: Maximum time without answer from the serial port
    BOUNCE_TIMEOUT = 20 #: Number of times a specific transmition is tried
    PARITY = serial.PARITY_NONE #: Message will not have any parity
    STOP_BITS = serial.STOPBITS_ONE #: Message contains only one stop bit
    BYTE_SIZE = serial.EIGHTBITS #: One byte = 8 bits
    
    def __init__(self, device, baudrate = BAUDRATE, timeout = TIMEOUT, bounce_timeout = BOUNCE_TIMEOUT):
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self.bounce_timeout = bounce_timeout
        self.serial = self.begin_serial()
        
    def begin_serial(self):
        """ Initializes pyserial instance.
        
        Returns:
            pyserial.serial object
            
        Raises:
            PermissionError: user is not allowed to use port.
            SerialException: if it could not open port
        """
        return serial.Serial(port=self.device, baudrate=self.baudrate, parity=self.PARITY,
                                        stopbits=self.STOP_BITS,
                                        bytesize=self.BYTE_SIZE, timeout=self.TIMEOUT)
        
    def checksum(self, hex_list):
        """ Implements a simple checksum to verify message integrity.
        
        Returns:
            bool: The return value. True for success, False otherwise. 
        """
        int_list = [int(value, 16) for value in hex_list]
        int_score = sum(int_list[2:-1])
        hex_score = "%04X"%int_score
        last_values = hex_score[2:]
        check = int(last_values, 16) + int(hex_list[-1], 16)
        if check == 0xff:
            return True
        else:
            return False
        
    def send(self, content):
        """ Sends a message through the serial port.
        
        Raises:
            PySerialExceptions
        """
        self.serial.write(content)
        
    def read(self):
        """ Reads a message through the serial port.
        
        Returns:
            list: hexadecimal values decoded as strings.
        
        Raises:
            Exception: Noisy answer, or timeout.
        """
        hexa = [codecs.encode(self.serial.read(1), "hex_codec").decode()]
        if hexa[0] != "7e":
            answer = "Timeout: noisy answer '%s'"%hexa[0]
            if hexa[0] == "":
                answer = 'Timeout: device does not answer.'
            raise Exception(answer)
        while True:
            byte = codecs.encode(self.serial.read(1), "hex_codec").decode()
            if byte == '':
                break
            hexa.append(byte)
        return hexa
        
    def receive(self):
        """ Organices information according to project requirements.
        
        Returns:
            list: each position on list is made up with a tuple containing
                channel and value in hexadecimal base.
        
        Raises:
            Exception: if wrong checksum.
        """
        
        hexa = self.read()
        if self.checksum(hexa):
            hexa = hexa[2:-1]
            ans = []
            n = int(len(hexa)/3) #signal comes in groups of three
            for i in range(n):
                channel = int(hexa[3*i], 16)
                value = hexa[3*i+1] + hexa[3*i+2]
                ans.append((channel, value))
            return ans
        else:
            raise Exception("Message corrupted. Incorrect checksum.")

    def message(self, content, wait_for_answer = False):
        """ Sends a message, and waits for answer.
        
        Returns:
            list: each postion on list is made up with a tuple containing
                channel and value in hexadecimal base.
                
        Raises:
            Exception: any type ocurred with during `bounce_timeout`.
        """
        self.send(content)
        if wait_for_answer:
            for i in range(self.bounce_timeout):
                try:
                    return self.receive()
                except Exception as ex:
                    try:
                        self.send(content)
                    except Exception as ex:
                        pass
                    if i == self.bounce_timeout - 1:
                        raise ex
        else:
            return None
                
class channel(object):
    """
    Constants
    """
    READ_VALUE = 0x0e #: Reading operation signal
    WRITE_VALUE = 0x0f #: Writing operation signal
    START_COMMUNICATION = 0x02 #: Begin message signal
    END_COMMUNICATION = 0x04 #: End of message
    
    global ADDRESS
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.address = ADDRESS[name]
        self.hex_value = None
        self.int_value = None
        self.msb_value = None
        self.lsb_value = None
        
    def set_value(self, value):
        """ Writes and incoming int value to class attributes."""
        self.int_value = value
        self.hex_value = "%04X"%value
        self.split_value()
        
    def split_value(self):
        """ Updates the most/least significant byte."""
        self.msb_value = int(self.hex_value[:2], 16)
        self.lsb_value = int(self.hex_value[2:], 16)
        
    def read_value(self, hex_list):
        """ Reads a `hex_list` and updates class attributes values."""
        self.hex_value = hex_list[0][1]
        self.int_value = int(self.hex_value, 16)
        self.split_value()
        
    def construct_message(self, read = False):
        """ Construcs a message with project requirements.
        
        Returns:
            list: list of bytes containing channel info.
        """
        if read:
            message = [self.START_COMMUNICATION, self.READ_VALUE, self.address,
                       0x00, 0x00, self.END_COMMUNICATION]
        else:
            message = [self.START_COMMUNICATION, self.WRITE_VALUE, self.address,
                       self.msb_value, self.lsb_value, self.END_COMMUNICATION]
        return serial.to_bytes(message)
    
    def verify_values(self, hex_list):
        """ Verifies if current values have changed.
        
        Returns:
            bool: The return value. True if values are the same, False otherwise.
        """
        if self.hex_value == hex_list[0][1]:
            return True
        else:
            return False
        
    def exchange_values(self, read = True):
        """ Exchanges values from computer to utility.
        
        Returns: can return None, or a list containing a `hex_list`                
        """ 
        message = self.construct_message(read)
        return self.port.message(message, wait_for_answer = read)
            
    def update_values(self, read = True):
        answer = self.exchange_values(read)
        if read:
            self.read_value(answer)
            
class timer_channel(object):
    """
    Constants
    """
    UNITS = ['ns', 'us', 'ms', 's']
    NUMBER_OF_CHANNELS = len(UNITS)
    global ADDRESS
    def __init__(self, prefix, port, base):
        self.prefix = prefix
        self.port = port
        self.base = base
        self.channels_names = ["%s_%s"%(prefix, unit) for unit in self.UNITS]
        self.channels = [channel(name, port) for name in self.channels_names]
        self.value = None # in seconds
        self.values = None
        
    def set_values(self, value):
        self.value = value
        self.parse_to_units()
        
    def read_values(self, values):
        value = sum([values[i]*10**(3*i) for i in range(self.NUMBER_OF_CHANNELS)])
        print(value)
            
        
    def parse_to_units(self):
        first_order = int(self.base*self.value*1e9)
        micro, nano = divmod(first_order, 1000)
        unit, mili = divmod(int(micro/1000), 1000)
        if micro >= 1000:
            micro = 0
        self.values = [nano, micro, mili, unit]
        
    def verify_values(self, values_to_verify):
        n = sum([self.values[i] == values_to_verify[i] for i in range(self.NUMBER_OF_CHANNELS)])
        if n == self.NUMBER_OF_CHANNELS:
            return True
        else:
            return False
        
    def exchange_values(self, read = True):
        return [channel.exchange_values(read) for channel in self.channels]
            
port = communication_port("/dev/ttyUSB0")
delayA = timer_channel("delayA", port, BASE_DELAY)
values = delayA.exchange_values(read = True)
print(delayA.read_values(values))