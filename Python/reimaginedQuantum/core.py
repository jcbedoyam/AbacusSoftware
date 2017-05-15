#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
*Required modules*
"""
import os
import serial
import codecs
from queue import Queue
from itertools import combinations
from threading import Thread, Timer
from importlib import import_module
from time import sleep, localtime, strftime, time, asctime
import serial.tools.list_ports as find_ports
#################
import numpy as np
#################

#################
from .channels import *
from .constants import *
from .exceptions import *
#################

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
    MESSAGE_TRIGGER = 1e-6 #: If queue is empty
    TEST_MESSAGE = [START_COMMUNICATION, READ_VALUE, 0x00,
               0x00, 0x00, END_COMMUNICATION]

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

    def checksum(self, hex_list):
        """ Implements a simple checksum to verify message integrity.

        Raises:
            CheckSumError(): in case checksum is wrong.
        """
        int_list = [int(value, 16) for value in hex_list]
        int_score = sum(int_list[2:-1])
        hex_score = "%04X"%int_score
        last_values = hex_score[2:]
        check = int(last_values, 16) + int(hex_list[-1], 16)
        if check != 0xff:
            raise CheckSumError()

    def send(self, content):
        """ Sends a message through the serial port.

        Raises:
            PySerialExceptions
        """
        # self.serial.flushOutput()
        self.serial.flushInput()
        self.serial.write(content)

    def read(self):
        """ Reads a message through the serial port.

        Returns:
            list: hexadecimal values decoded as strings.

        Raises:
            CommunicationError:
        """
        hexa = [codecs.encode(self.serial.read(1), "hex_codec").decode()]
        if hexa[0] != "7e":
            raise CommunicationError()
        hexa += [codecs.encode(self.serial.read(1), "hex_codec").decode()]
        N = int(hexa[1], 16)
        byte = codecs.encode(self.serial.read(N+1), "hex_codec").decode()
        byte = list(map(''.join, zip(*[iter(byte)]*2)))
        hexa += byte
        return hexa

    def receive(self):
        """ Organices information according to project requirements.

        Returns:
            list: each position on list is made up with a tuple containing
                channel and value in hexadecimal base.

        Raises:
            CheckSumError: if wrong checksum.
        """
        hexa = self.read()
        self.checksum(hexa) # checks if checksum is correct
        hexa = hexa[2:-1]
        ans = []
        n = int(len(hexa)/3) #signal comes in groups of three
        for i in range(n):
            channel = int(hexa[3*i], 16)
            value = hexa[3*i+1] + hexa[3*i+2]
            ans.append((channel, value))
        return ans

    def handle_queue(self):
        """ Permanent loop in charge of sending any message withing the queue
        one by one.

        Raises:
            Exception: any type of error withing serial.
        """
        while not self.stop:
            item = self.queue.get()
            conf, content, wait_for_answer = item
            answer = self.message_internal(content, wait_for_answer) # call function
            if wait_for_answer:
                self.answer[conf] = answer

    def message(self, content, wait_for_answer = False):
        """ Method to which different instances have access. Instances use this
        method in order to communicate a message 'content' to the serial port.
        The content of the message is added to the queue and waits for an answer
        inside a loop.

        Returns:
            list: of hexadecimal values.
        Raises:
            CommunicationError: if communication port is closed, and a answer is
            expected.
        """

        conf = np.random.random()
        self.queue.put((conf, content, wait_for_answer))
        if wait_for_answer:
            while not self.stop:
                if conf in self.answer:
                    value = self.answer.pop(conf)
                    return value
                sleep(1e-3)
            raise CommunicationError()
        else:
            return None

    def message_internal(self, content, wait_for_answer = False, tries = -1):
        """ Sends a message, and waits for answer.

        Returns:
            list: each postion on list is made up with a tuple containing
                channel and value in hexadecimal base.

        Raises:
            Exception: any type ocurred with during `bounce_timeout`.
        """

        if tries == -1:
            tries = self.bounce_timeout
        if wait_for_answer:
            for i in range(tries):
                try:
                    self.send(content)
                    return self.receive()
                except Exception as e:
                    pass
                if i == tries - 1:
                    self.stop = True
                    raise CommunicationError()
        else:
            self.send(content)
            return None

    def test(self):
        """ Tests whether or not the CommunicationPort corresponds to a ReimaginedQuantum one.

        Returns:
            boolean: True if it does, False otherwise.
        """
        try:
            self.message_internal(serial.to_bytes(self.TEST_MESSAGE),
                                    wait_for_answer = True, tries = 3)
            return True
        except Exception as e:
            return False

    def close(self):
        """ Closes the serial port."""
        self.serial.close()
        self.stop = True



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
            raise ExperimentError(str(e))
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
            message = self.construct_message(data = False)
            values = self.port.message(message, wait_for_answer = True)
            for i in range(self.number_detectors):
                begin_delay = 4*i
                delay = values[begin_delay: begin_delay + 4]
                sleep = values[begin_delay + 8: begin_delay + 12]
                value = delay + sleep
                self.detectors[i].set_timers_values(value)
            last = 8*(i+1)
            self.sampling_channel.read_values(values[last: 4 + last])
            self.coinWindow_channel.read_values(values[last+ 4:])
        except Exception as e:
            raise ExperimentError(str(e))

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

class RingBuffer():
    """
    Based on https://scimusing.wordpress.com/2013/10/25/ring-buffers-in-pythonnumpy/
    """
    global DELIMITER
    def __init__(self, rows, columns, output_file, fmt, delimiter = DELIMITER):
        self.data = np.zeros((rows, columns))
        self.index = 0
        self.empty = True
        self.output_file = output_file
        self.last_saved = 0
        self.format = fmt
        self.size = self.data.shape[0]
        self.total_movements = 0

    def extend(self, x):
        "adds array x to ring buffer"
        if self.empty:
            self.empty = False
        self.total_movements += 1
        x_index = (self.index + np.arange(x.shape[0])) % self.size
        self.data[x_index] = x
        self.index = x_index[-1] + 1

        if self.index == self.size and not self.empty:
            self.save()

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        idx = (self.index + np.arange(self.size)) %self.size
        return self.data[idx]

    def save(self):
        "Saves the buffer"
        from_index = self.size - self.index + self.last_saved
        self.last_saved = self.index
        data = self.get()[from_index%self.size:]
        with open(self.output_file, 'ab') as _file:
            np.savetxt(_file, data, fmt = self.format)

    def __getitem__(self, item):
        if self.total_movements > self.size:
            return self.get()
        else:
            return self.get()[self.size-self.index :]

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

def save_default(DEFAULT_CHANNELS = DEFAULT_CHANNELS, DEFAULT_DELAY = DEFAULT_DELAY,
            DEFAULT_SLEEP = DEFAULT_SLEEP, DEFAULT_SAMP = DEFAULT_SAMP,
            DEFAULT_COIN = DEFAULT_COIN, USER_EMAIL = USER_EMAIL, FILE_NAME = FILE_NAME,
            SEND_EMAIL = SEND_EMAIL):
    with open('default.py', 'w') as file:
        file.write('DEFAULT_CHANNELS=%d\n'%DEFAULT_CHANNELS)
        file.write('DEFAULT_DELAY=%d\n'%DEFAULT_DELAY)
        file.write('DEFAULT_SLEEP=%d\n'%DEFAULT_SLEEP)
        file.write('DEFAULT_SAMP=%d\n'%DEFAULT_SAMP)
        file.write('DEFAULT_COIN=%d\n'%DEFAULT_COIN)
        file.write("USER_EMAIL='%s'\n"%USER_EMAIL)
        file.write("FILE_NAME='%s'\n"%FILE_NAME)
        file.write("SEND_EMAIL=%s\n"%SEND_EMAIL)

def reload_default():
    global DEFAULT_CHANNELS, DEFAULT_DELAY, DEFAULT_SLEEP, DEFAULT_SLEEP, DEFAULT_COIN
    global USER_EMAIL, FILE_NAME, SEND_EMAIL
    import_module('reimaginedQuantum.constants')
