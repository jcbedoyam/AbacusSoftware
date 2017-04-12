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
from itertools import combinations
from threading import Thread, Timer
from time import sleep, localtime, strftime, time
import serial.tools.list_ports as find_ports


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

class CommunicationPort(object):
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
                except Exception as ex1:
                    try:
                        self.send(content)
                    except Exception as ex2:
                        pass
                    if i == self.bounce_timeout - 1:
                        raise ex1
        else:
            return None
        
    def close(self):
        self.serial.close()
                
class Channel(object):
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
        self.hex_value = "x00"
        self.int_value = 0
        self.msb_value = 0
        self.lsb_value = 0
        
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
        return answer
            
class TimerChannel(object):
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
        self.channels = [Channel(name, port) for name in self.channels_names]
        self.value = 0 # in base
        self.values = [0, 0, 0, 0]
        
    def set_value(self, value):
        self.value = value
        self.parse_to_units()
        [channel.set_value(value) for (channel, value) in zip(self.channels, self.values)]
        
    def read_values(self, values):
        self.values = self.unnested_values(values)
        self.value = int(self.base*sum([self.values[i]*10**(3*i) for i in range(self.NUMBER_OF_CHANNELS)]))
        
    def unnested_values(self, values):
        return [int(value[0][1],16) for value in values]
        
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
    
    def update_values(self, read = True):
        answer = [channel.update_values(read) for channel in self.channels]
        if read:
            self.read_values(answer)
        return self.value
    
    def check_values(self):
        values = self.exchange_values()
        values_unnested = self.unnested_values(values)
        answer = self.verify_values(values_unnested)
        if not answer:
            self.read_values(values)
            return self.prefix, int(self.value/self.base)
        else:
            return None
        
class DataChannel(object):
    """
    Constants
    """
    SIGNIFICANT_BYTES = ["MSB", "LSB"]
    NUMBER_OF_CHANNELS = len(SIGNIFICANT_BYTES)
    global ADDRESS
    def __init__(self, prefix, port):
        letters = prefix.strip()
        letters = [letter for letter in letters if letter.isupper()]
        pos = len(prefix.split(letters[0])[0])
        self.name = "%s %s"%(prefix[:pos].title(), prefix[pos:])
        self.prefix = prefix
        self.port = port
        self.channels_names = ["%s_%s"%(prefix, sig) for sig in self.SIGNIFICANT_BYTES]
        self.channels = [Channel(name, port) for name in self.channels_names]
        self.hex_value = "0x00"
        self.value = 0
        self.values = [0, 0]
        
    def set_value(self, value):
        self.value = value
        self.split_value()
        [channel.set_value(value) for (channel, value) in zip(self.channels, self.values)]
    
    def split_value(self):
        self.hex_value = "%08X"%self.value
        self.values = [int(self.hex_value[:4], 16), int(self.hex_value[4:], 16)]
        
    def read_values(self, values):
        self.hex_value = "".join([value[0][1] for value in values])
        self.value = int(self.hex_value, 16)
        self.values = [int(self.hex_value[:4], 16), int(self.hex_value[4:], 16)]
        
    def exchange_values(self):
        return [channel.exchange_values(True) for channel in self.channels]
    
    def update_values(self):
        answer = [channel.update_values(True) for channel in self.channels]
        self.read_values(answer)
        return self.value

class FunctionTimer(object):
    def __init__(self, interval, function, *args):
        self._timer = None
        self.interval = interval
        self.function = function
        self.is_running = False
        self.args = args

    def _run(self):
        self.is_running = False
        self.start()
        try:
            self.function(*self.args)
        except Exception as e:
            if not "noisy answer" in str(e):
                self.stop()
                raise e

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
        
class Detector(object):
    """
    Constants
    """
    BASE_DELAY = 1e-9 #: Default channnel delay time (seconds)
    BASE_SLEEP = 1e-9 #: Default channel sleep time (seconds)
    def __init__(self, identifier, port, data_interval = 100, timer_check_interval = 1000):
        self.identifier = identifier
        self.name = "Detector %s"%self.identifier
        self.port = port
        self.data_interval = data_interval/1000 # in miliseconds
        self.timer_check_interval = timer_check_interval/1000
        self.data_channel = DataChannel("counts%s"%self.identifier, self.port)
        self.delay_channel = TimerChannel("delay%s"%self.identifier, self.port, self.BASE_DELAY)
        self.sleep_channel = TimerChannel("sleepTime%s"%self.identifier, self.port, self.BASE_SLEEP)
        
        self.time_timer = FunctionTimer(self.timer_check_interval, self.check_times)
        self.data_timer = FunctionTimer(self.data_interval, self.update_data)
        
        self.current_data = 0
        
    def update_data(self):
        self.current_data = self.data_channel.update_values()
        return self.current_data
    
    def check_values(self, channel):
        return channel.check_values()
#        values = channel.exchange_values()
#        values = channel.unnested_values(values)
#        check = channel.verify_values(values)
#        return check
        
    def check_times(self):
        check_delay = self.check_values(self.delay_channel)
        check_sleep = self.check_values(self.sleep_channel)
        ans = []
        if check_delay != None:
            ans += [check_delay]
        if check_sleep != None:
            ans += [check_sleep]
        return ans
        
    def start_timers(self, interval):
        pass
    
    def set_delay(self, value):
        self.delay_channel.set_value(value)
        self.delay_channel.update_values(read = False)
        
    def set_sleep(self, value):
        self.sleep_channel.set_value(value)
        self.sleep_channel.update_values(read = False)
        
    def set_times(self, delay, sleep):
        self.set_delay(delay)
        self.set_sleep(sleep)

class Experiment(object):
    """
    Constants
    """
    BASE_SAMPLING = 1e-3 #: Default sampling time (seconds)
    BASE_COINWIN = 1e-9 #: Default coincidence window (seconds)
    
    def __init__(self, port, number_detectors = 2):
        self.port = port
        self.number_detectors = number_detectors
        self.detector_identifiers = [chr(i + ord('A')) for i in range(self.number_detectors)]
        self.coins_identifiers = self.get_combinations()
        self.number_coins = len(self.coins_identifiers)
        self.detector_dict = {self.detector_identifiers[i]: i for i in range(self.number_detectors)}
        self.coins_dict = {self.coins_identifiers[i]: i for i in range(self.number_coins)}
        self.detectors = [Detector(identifier, self.port) for identifier in self.detector_identifiers]
        self.coin_channels = [DataChannel("coincidences%s"%identifier, self.port) for identifier in self.coins_identifiers]
        
        self.sampling_channel = TimerChannel("samplingTime", port, self.BASE_SAMPLING)
        self.coinWindow_channel = TimerChannel("coincidenceWindow", port, self.BASE_COINWIN)
        
    
    def current_values(self):
        detector_values = [detector.update_data() for detector in self.detectors]
        coin_values = [coin.update_values() for coin in self.coin_channels]
        return time(), detector_values, coin_values
    
    def set_sampling(self, value):
        self.sampling_channel.set_value(value)
        self.sampling_channel.update_values(False)
        
    def set_coinWindow(self, value):
        self.coinWindow_channel.set_value(value)
        self.coinWindow_channel.update_values(False)
        
    def measure_N_points(self, detector_identifiers, interval, N_points, print_ = True):
        if detector_identifiers != []:
            coins_identifiers = {}
            if len(detector_identifiers) > 1:
                for detector in detector_identifiers:
                    if detector in self.detector_dict:
                        for key in self.coins_dict:
                            if (detector in key) and (not key in coins_identifiers):
                               coins_identifiers[key] = self.coins_dict[key]
                    else:
                        raise Exception("The following detector is not withing our experiment: %s."%detector)
                        
            detectors = [self.detectors[self.detector_dict[identifier]] for identifier in detector_identifiers]
            coins = [self.coin_channels[coins_identifiers[key]] for key in coins_identifiers]
            
        else:
            detectors = self.detectors
            coins = self.coin_channels
        
        n_detectors = len(detectors)
        n_coins = len(coins)
        
        data_detectors = np.zeros((N_points, n_detectors))
        data_coins = np.zeros((N_points, n_coins))
        times = np.zeros(N_points)
        for i in range(N_points):
            for j in range(n_detectors):
                data_detectors[i, j] = detectors[j].update_data()
            for k in range(n_coins):
                data_coins[i, k] = coins[k].update_values()
            if i == 0:
                initial_time = time()
                times[i] = 0
            else:
                times[i] = time() - initial_time
            if print_:
                print(times[i], data_detectors[i], data_coins[i])
            sleep(interval)
            
        return times, data_detectors, data_coins

    def get_combinations(self):
        letters = "".join(self.detector_identifiers)
        coins = []
        for i in range(1, self.number_detectors):
            coins += list(combinations(letters, i+1))
            
        return ["".join(values) for values in coins]
    
    def check_values(self):
        values1 = self.sampling_channel.check_values()
        values2 = self.coinWindow_channel.check_values()
        values = []
        for detector in self.detectors:
            values += detector.check_times()
        if values1 != None:
            values += [values1]
        if values2 != None:
            values += [values2]
        return values

CURRENT_OS = sys.platform
    

def findPort():
    global CURRENT_OS
    ports_objects = list(find_ports.comports())
    ports = {}
    for i in range(len(ports_objects)):
        port = ports_objects[i]
        if CURRENT_OS == "win32":
            ports["%s"%port.description] = port.device 
        else:
            ports["%s (%s)"%(port.description, port.device)] = port.device
    return ports
    
if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt
    
    port = CommunicationPort("/dev/ttyUSB0")
    exp = Experiment(port, 2)
    time, detectors, coins = exp.measure_N_points(["A", "B"], 0.0, 50, print_ = False)
    
    fig, axes = plt.subplots(2, sharex = True)
    
    # DETECTORS
    n = detectors.shape[1]
    if n == 1:
        axes[0].plot(time, detectors, "-o", label = "%s"%exp.detectors[0].name)
    else:
        for i in range(n):
            axes[0].plot(time, detectors[:, i], "-o", label = "%s"%exp.detectors[i].name)
            
    # COINCIDENCES
    n = coins.shape[1]
    if n == 1:
        axes[1].plot(time, coins, "-o", label = "%s"%exp.coin_channels[0].prefix)
    else:
        for i in range(n):
            axes[1].plot(time, detectors[:, i], "-o", label = "%s"%exp.coin_channels[i].prefix)
    for ax in axes:
        ax.legend()
        ax.set_ylabel("Counts")
    
    plt.show()