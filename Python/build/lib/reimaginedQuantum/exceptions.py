class CommunicationError(Exception):
    """ An error ocurred at the communication port. """
    def __init__(self, message = "An error ocurred at the communication port."):
        self.message = message
    def __repr__(self):
        return self.message

class CheckSumError(Exception):
    """ An error ocurred while doing check sum. """
    def __init__(self, message = "An error ocurred while doing check sum."):
        self.message = message
    def __repr__(self):
        return self.message

class ExperimentError(Exception):
    """ An error ocurred in the experiment. """
    def __init__(self, message = "An error ocurred in the experiment."):
        self.message = message
    def __repr__(self):
        return self.message
