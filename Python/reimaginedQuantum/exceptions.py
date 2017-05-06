class CommunicationError(Exception):
    def __init__(self, message = "Fatal Error. An error ocurred at the communication port. \
     Port is either closed or disconnected."):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class CheckSumError(Exception):
    def __init__(self, message = "An error ocurred while doing check sum."):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message

class ExperimentError(Exception):
    def __init__(self, message = "An error ocurred in the experiment."):
        self.message = message
    def __repr__(self):
        return self.message
    def __str__(self):
        return self.message
