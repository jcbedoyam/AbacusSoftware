class ExtentionError(Exception):
    """ File Error. Extention is not valid. """

    def __init__(self, message = "File Error. Extention is not valid."):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message
