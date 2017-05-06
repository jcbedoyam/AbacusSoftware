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
from .exceptions import *
from time import sleep, localtime, strftime, time, asctime
import serial.tools.list_ports as find_ports
#################
import numpy as np
#################
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

READ_VALUE = 0x0e #: Reading operation signal
WRITE_VALUE = 0x0f #: Writing operation signal
START_COMMUNICATION = 0x02 #: Begin message signal
END_COMMUNICATION = 0x04 #: End of message
MAXIMUM_WRITING_TRIES = 20 #: Number of tries done to write a value

class Queue(object):
    """
    Implements a FIFO queue, two possible priorities are allowed.
    """
    def __init__(self):
        self.high_objects = []
        self.low_objects = []

    def put(self, item, priority = 0):
        if priority:
            self.high_objects.append(item)
        else:
            self.low_objects.append(item)

    def get(self):
        if self.high_objects:
            return self.high_objects.pop(0)
        elif self.low_objects:
            return self.low_objects.pop(0)
        return None

class CommunicationPort(object):
    """ Builds a serial port from pyserial.

    Implements multiple functions that will be used by different instances of the experiment.

    **Constants**
    """
    BAUDRATE = 115200 #: Default baudrate for the serial port communication
    TIMEOUT = 0.02 #: Maximum time without answer from the serial port
    BOUNCE_TIMEOUT = 20 #: Number of times a specific transmition is tried
    PARITY = serial.PARITY_NONE #: Message will not have any parity
    STOP_BITS = serial.STOPBITS_ONE #: Message contains only one stop bit
    BYTE_SIZE = serial.EIGHTBITS #: One byte = 8 bits
    MESSAGE_TRIGGER = 1e-3 #: If queue is empty
    def __init__(self, device, baudrate = BAUDRATE, timeout = TIMEOUT, bounce_timeout = BOUNCE_TIMEOUT):
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self.bounce_timeout = bounce_timeout
        self.serial = self.begin_serial()

        # Implements a Queue to send messages
        self.queue = Queue()
        self.stop = False
        self.answer = {}
        self.thread = Thread(target=self.handle_queue)
        self.thread.setDaemon(True)
        self.thread.start()

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

    # def checksum(self, hex_list):
    #     """ Implements a simple checksum to verify message integrity.
    #
    #     Raises:
    #         CheckSumError(): in case checksum is wrong.
    #     """
    #     int_list = [int(value, 16) for value in hex_list]
    #     int_score = sum(int_list[2:-1])
    #     hex_score = "%04X"%int_score
    #     last_values = hex_score[2:]
    #     check = int(last_values, 16) + int(hex_list[-1], 16)
    #     if check != 0xff:
    #         raise CheckSumError()

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

    # def send(self, content):
    #     """ Sends a message through the serial port.
    #
    #     Raises:
    #         PySerialExceptions
    #     """
    #     try:
    #         self.serial.write(content)
    #     except:
    #         self.serial.reset_input_buffer()
    #         raise CommunicationError()

    def send(self, content):
        """ Sends a message through the serial port.

        Raises:
            PySerialExceptions
        """
        self.serial.write(content)

    # def read(self):
    #     """ Reads a message through the serial port.
    #
    #     Returns:
    #         list: hexadecimal values decoded as strings.
    #
    #     Raises:
    #         CommunicationError:
    #     """
    #     hexa = [codecs.encode(self.serial.read(1), "hex_codec").decode()]
    #     if hexa[0] != "7e":
    #         self.serial.reset_output_buffer()
    #         raise CommunicationError()
    #     while True:
    #         byte = codecs.encode(self.serial.read(1), "hex_codec").decode()
    #         if byte == '':
    #             break
    #         hexa.append(byte)
    #     self.serial.flush()
    #     return hexa

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
            self.serial.flush()
            raise Exception(answer)
        while True:
            byte = codecs.encode(self.serial.read(1), "hex_codec").decode()
            if byte == '':
                break
            hexa.append(byte)
        return hexa

    def handle_queue(self):
        while not self.stop:
            item = self.queue.get()
            if item != None:
                conf, content, wait_for_answer = item
                answer = self.message_internal(content, wait_for_answer) # call function
                self.answer[conf] = answer
            else:
                sleep(self.MESSAGE_TRIGGER)
    #
    # def receive(self):
    #     """ Organices information according to project requirements.
    #
    #     Returns:
    #         list: each position on list is made up with a tuple containing
    #             channel and value in hexadecimal base.
    #
    #     Raises:
    #         CheckSumError: if wrong checksum.
    #     """
    #
    #     hexa = self.read()
    #     self.checksum(hexa) # checks if checksum is correct
    #     hexa = hexa[2:-1]
    #     ans = []
    #     n = int(len(hexa)/3) #signal comes in groups of three
    #     for i in range(n):
    #         channel = int(hexa[3*i], 16)
    #         value = hexa[3*i+1] + hexa[3*i+2]
    #         ans.append((channel, value))
    #     return ans

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
        conf = np.random.random()
        self.queue.put((conf, content, wait_for_answer))
        if wait_for_answer:
            while not self.stop:
                if conf in self.answer:
                    value = self.answer[conf]
                    del self.answer[conf]
                    return value
                sleep(self.MESSAGE_TRIGGER)
        else:
            return None
        # raise Exception("Port is closed.")

    # def message_internal(self, content, wait_for_answer = False):
    #     """ Sends a message, and waits for answer.
    #
    #     Returns:
    #         list: each postion on list is made up with a tuple containing
    #             channel and value in hexadecimal base.
    #
    #     Raises:
    #         Exception: any type ocurred with during `bounce_timeout`.
    #     """
    #     if wait_for_answer:
    #         for i in range(self.bounce_timeout):
    #             try:
    #                 self.send(content)
    #                 return self.receive()
    #             except Exception as e:
    #                 pass
    #             # sleep(self.MESSAGE_TRIGGER)
    #             if i == self.bounce_timeout - 1:
    #                 print(i)
    #                 # raise CommunicationError()
    #     else:
    #         self.send(content)
    #         return None

    def message_internal(self, content, wait_for_answer = False):
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
        """ Closes the serial port."""
        self.serial.close()
        self.stop = True

class Channel(object):
    """ Implements a channel, an object representation of a memory address.

    **Constants**
    """
    global ADDRESS, READ_VALUE, WRITE_VALUE, START_COMMUNICATION, END_COMMUNICATION
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.address = ADDRESS[name]
        self.hex_value = "x00"
        self.int_value = 0
        self.msb_value = 0
        self.lsb_value = 0

    def set_value(self, value):
        """ Writes and incoming int value to class attributes. """
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
            message = [START_COMMUNICATION, READ_VALUE, self.address,
                       0x00, 0x00, END_COMMUNICATION]
        else:
            message = [START_COMMUNICATION, WRITE_VALUE, self.address,
                       self.msb_value, self.lsb_value, END_COMMUNICATION]
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
        """ Updates values read from device.

        Returns:
            list of string hexadecimal values
        """
        answer = self.exchange_values(read)
        if read:
            self.read_value(answer)
        return answer

class TimerChannel(object):
    """ Implements a timer channel, an object representation of multiple memory addresses.

    Timer channels are a construction of four simple channels, each for every time unit.

    **Constants**
    """
    UNITS = ['ns', 'us', 'ms', 's'] #: Units contained in each channel.
    NUMBER_OF_CHANNELS = len(UNITS) #: Number of channels in a timer channel.
    global ADDRESS, READ_VALUE, WRITE_VALUE, START_COMMUNICATION, END_COMMUNICATION, MAXIMUM_WRITING_TRIES
    def __init__(self, prefix, port, base):
        self.prefix = prefix
        self.port = port
        self.base = base
        self.channels_names = ["%s_%s"%(prefix, unit) for unit in self.UNITS]
        self.channels = [Channel(name, port) for name in self.channels_names]
        self.first_address = self.channels[0].address
        self.last_address = self.channels[3].address
        self.value = 0 # in base
        self.values = [0, 0, 0, 0]

    def set_value(self, value):
        """ Writes an incoming integer value to memory, and parses it into time units.
        Information is passed down the tree.
        """
        self.value = value
        self.parse_to_units()
        [channel.set_value(value) for (channel, value) in zip(self.channels, self.values)]

    def read_values(self, values):
        """ Writes an incoming tuple of hexadecimal values to memory and constructs
        simple representation. """
        self.values = self.unnested_values(values)
        self.value = int((1e-9/self.base)*sum([self.values[i]*10**(3*i) for i in range(self.NUMBER_OF_CHANNELS)]))

    def unnested_values(self, values):
        """ Removes addresses from incoming hexadecimal values.

        Returns:
            list: each position contains an integer representation of a hexadecimal value.
        """
        return [int(value[1], 16) for value in values]

    def parse_to_units(self):
        """ Breaks a simple value representation to time units. """
        first_order = int(self.base*self.value*1e9)
        micro, nano = divmod(first_order, 1000)
        unit, mili = divmod(int(micro/1000), 1000)
        if micro >= 1000:
            micro = 0
        self.values = [nano, micro, mili, unit]

    def verify_values(self, values_to_verify):
        """ Verifies if incoming values are equal to the stored ones.

        Return:
            bool: True if they are the same, False otherwise.
        """
        n = sum([self.values[i] == values_to_verify[i] for i in range(self.NUMBER_OF_CHANNELS)])
        if n == self.NUMBER_OF_CHANNELS:
            return True
        else:
            return False

    def exchange_values(self, read = True):
        """ Exchanges information with device.

        If `read = True` means it will only send a message to device in order to get its answer.
        Otherwise the communication will try to write at the device.
        """
        return [channel.exchange_values(read) for channel in self.channels]

    def update_values(self, read = True):
        """ Updates current values with the device ones.

        Returns:
            int: current value estored at the timer channel.
        """
        answer = [channel.update_values(read) for channel in self.channels]
        if read:
            self.read_values(answer)
        return self.value

    def construct_message(self):
        """ Constructs the message to be send to the device to
        gather the values written in memory for all four channels.

        Returns:
            list: containing integer representations of hexadecimal values.
        """
        return [START_COMMUNICATION, READ_VALUE,
                self.first_address, 0x00, 0x04, END_COMMUNICATION]

    def check_values(self):
        """ Sends message and waits for answer, in which current device values are stored.
        Checks if those values are the same with the channel ones.

        Returns:
            bool: True if values are the same, False otherwise.
        """
        values = self.port.message(self.construct_message(), wait_for_answer = True)
        values = self.unnested_values(values)
        check = self.verify_values(values)
        return check

    def set_write_value(self, value):
        """ Sets the incoming value to the class attribute, writtes them to device.
        The process is done as many times are in `MAXIMUM_WRITING_TRIES`,
        if values are different raises and Exception.

        Raises:
            Exception: Maximum writting tries.
        """
        try:
            for i in range(MAXIMUM_WRITING_TRIES):
                self.set_value(value)
                self.update_values(False)
                if self.check_values():
                    break
            if i == MAXIMUM_WRITING_TRIES -1:
                raise Exception("Maximum writting tries.")
        except Exception as e:
            raise e

class DataChannel(object):
    """ Implements a data channel, an object representation of multiple memory addresses.
    Timer channels are a construction of two simple channels, one for the Most Significant Bytes (MSB)
    and another for the Least Significant Bytes (LSB).

    **Constants**
    """
    SIGNIFICANT_BYTES = ["MSB", "LSB"] #: Significant bytes.
    NUMBER_OF_CHANNELS = len(SIGNIFICANT_BYTES) #: Number of channels in data channel.
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

    def get_value(self):
        """ Returns the current value.

        Returns:
            int: current value.
        """
        return self.value

    def read_values(self, values):
        """ Saves an incoming set of tuples containg the values of each channel.
        """
        self.hex_value = "".join([values[1][1], values[0][1]])
        self.value = int(self.hex_value, 16)
        self.values = [int(self.hex_value[:4], 16), int(self.hex_value[4:], 16)]

    def update_values(self):
        """ Sends a message to the device, the answer contains current device values.
        It then stores them with the help of `read_values(values)`.

        Returns:
            int: current value.
        """
        answer = self.port.message(self.construct_message(), wait_for_answer = True)
        self.read_values(answer)
        return self.value

    def construct_message(self):
        """ Constructs the message to be send to the device in order to get its current values.

        Returns:
            list: containing integer representations of hexadecimal values.
        """
        return [START_COMMUNICATION, READ_VALUE,
                self.channels[1].address, 0x00, 0x01, END_COMMUNICATION]

class Detector(object):
    """ Implements a detector, an object representation of multiple memory addresses.
    A detector is made of one data channel and two timer channels.

    **Constants**
    """
    BASE_DELAY = 1e-9 #: Default channnel delay time (seconds)
    BASE_SLEEP = 1e-9 #: Default channel sleep time (seconds)
    def __init__(self, identifier, port, data_interval = 100, timer_check_interval = 1000):
        self.identifier = identifier
        self.name = "Detector %s"%self.identifier
        self.port = port
        self.data_channel = DataChannel("counts%s"%self.identifier, self.port)
        self.delay_channel = TimerChannel("delay%s"%self.identifier, self.port, self.BASE_DELAY)
        self.sleep_channel = TimerChannel("sleepTime%s"%self.identifier, self.port, self.BASE_SLEEP)
        self.first_data_address = self.data_channel.channels[1].address
        self.first_timer_address = self.delay_channel.first_address
        self.current_data = 0

    def read_values(self, values):
        """ Reads incoming values at the data channel."""
        self.data_channel.read_values(values)

    def get_timer_values(self):
        """ Gets the values at each timer channel.

        Returns:
            tuple: each value in a position of the tuple..
        """
        return self.delay_channel.value, self.sleep_channel.value

    def get_value(self):
        """ Stores and returns the current value of the data channel.

        Returns:
            int: current value at the data channel.
        """
        self.current_data = self.data_channel.get_value()
        return self.current_data

    def update_data(self):
        """ Stores a fresh value of the data channel."""
        self.current_data = self.data_channel.update_values()

    def set_timers_values(self, values):
        """ Sets the incoming values in each timer channel."""
        self.delay_channel.read_values(values[:4])
        self.sleep_channel.read_values(values[4:])

    def set_delay(self, value):
        """ Saves the incoming value, writes it to device and verifies writing. """
        self.delay_channel.set_write_value(value)

    def set_sleep(self, value):
        self.sleep_channel.set_write_value(value)

    def set_times(self, delay, sleep):
        self.set_delay(delay)
        self.set_sleep(sleep)

class Experiment(object):
    """
    Constants
    """
    BASE_SAMPLING = 1e-3 #: Default sampling time (seconds)
    BASE_COINWIN = 1e-9 #: Default coincidence window (seconds)
    global READ_VALUE, WRITE_VALUE, START_COMMUNICATION, END_COMMUNICATION
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

    def construct_message(self, data = True):
        if data:
            number = "%08X"%(2*(self.number_detectors + self.number_coins))
            first = self.detectors[0].first_data_address
        else:
            number = "%08X"%(self.coinWindow_channel.last_address - self.detectors[0].first_timer_address +1)
            first = self.detectors[0].first_timer_address

        msb = int(number[:4], 16)
        lsb = int(number[4:], 16)
        return [START_COMMUNICATION, READ_VALUE, first,
                msb, lsb, END_COMMUNICATION]

    def current_values(self):
        ans = self.port.message(self.construct_message(), wait_for_answer = True)
        detector_values = []
        coin_values = []
        try:
            for i in range(self.number_detectors):
                self.detectors[i].read_values(ans[2*i:2*i+2])
                detector_values.append(self.detectors[i].get_value())
            for j in range(self.number_coins):
                self.coin_channels[j].read_values(ans[2*(i+j+1):2*(i+j+1)+2])
                coin_values.append(self.coin_channels[j].get_value())
        except Exception as e:
            raise e
        return time(), detector_values, coin_values

    def set_sampling(self, value):
        self.sampling_channel.set_write_value(value)

    def set_coinWindow(self, value):
        self.coinWindow_channel.set_write_value(value)

    def get_sampling_value(self):
        return self.sampling_channel.value

    def get_coinwin_value(self):
        return self.coinWindow_channel.value

    def get_detectors_timers_values(self):
        return [detector.get_timer_values() for detector in self.detectors]

    def get_combinations(self):
        letters = "".join(self.detector_identifiers)
        coins = []
        for i in range(1, self.number_detectors):
            coins += list(combinations(letters, i+1))

        return ["".join(values) for values in coins]

    def periodic_check(self):
        try:
            values = self.port.message(self.construct_message(data = False), wait_for_answer = True)
            for i in range(self.number_detectors):
                last = 8*(i+1)
                self.detectors[i].set_timers_values(values[8*i:last])
            self.sampling_channel.read_values(values[last:4+last])
            self.coinWindow_channel.read_values(values[last+4:])
        except Exception as e:
            raise e

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
                        raise ExperimentError("The following detector is not withing our experiment: %s."%detector)

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

#if __name__ == "__main__":
#    import numpy as np
#    import matplotlib.pyplot as plt
#
#    port = CommunicationPort("/dev/ttyUSB0")
#    exp = Experiment(port, 2)
#    time, detectors, coins = exp.measure_N_points(["A", "B"], 0.0, 50, print_ = False)
#
#    fig, axes = plt.subplots(2, sharex = True)
#
#    # DETECTORS
#    n = detectors.shape[1]
#    if n == 1:
#        axes[0].plot(time, detectors, "-o", label = "%s"%exp.detectors[0].name)
#    else:
#        for i in range(n):
#            axes[0].plot(time, detectors[:, i], "-o", label = "%s"%exp.detectors[i].name)
#
#    # COINCIDENCES
#    n = coins.shape[1]
#    if n == 1:
#        axes[1].plot(time, coins, "-o", label = "%s"%exp.coin_channels[0].prefix)
#    else:
#        for i in range(n):
#            axes[1].plot(time, detectors[:, i], "-o", label = "%s"%exp.coin_channels[i].prefix)
#    for ax in axes:
#        ax.legend()
#        ax.set_ylabel("Counts")
#
#    plt.show()
