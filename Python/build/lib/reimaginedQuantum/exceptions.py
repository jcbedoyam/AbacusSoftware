class CommunicationError(Exception):
    message = "An error ocurred at the communication port."
    def __init__(self, *message):
        self.message = message
    def __repr__(self):
        return self.message

class CheckSumError(Exception):
    message = "An error ocurred while doing check sum."
    def __init__(self, *message):
        self.message = message
    def __repr__(self):
        return self.message

class ExperimentError(Exception):
    message = "An error ocurred in the experiment."
    def __init__(self, *message):
        self.message = message
    def __repr__(self):
        return self.message
