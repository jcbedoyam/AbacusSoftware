#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class CommunicationError(Exception):
    """ Fatal Error. An error ocurred at the communication port.
Port is either closed or disconnected. """

    def __init__(self, message = "Fatal Error. An error ocurred at the communication port. \
 Port is either closed or disconnected."):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class CheckSumError(Exception):
    """ An error ocurred while doing check sum. """

    def __init__(self, message = "An error ocurred while doing check sum."):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class ExperimentError(Exception):
    """ An error ocurred while in the experiment. """

    def __init__(self, message = "An error ocurred in the experiment."):
        self.message = message
    def __repr__(self):
        return self.message
    def __str__(self):
        return self.message


class SavingError(Exception):
    """ An error ocurred while saving. """

    def __init__(self, message = "An error ocurred while saving."):
        self.message = message
    def __repr__(self):
        return self.message
    def __str__(self):
        return self.message
