import os
import smtplib
# import config
# from config import get_password
import __GUI_images__
from email.mime.text import MIMEText
from reimaginedQuantum.constants import *
from PyQt5 import QtCore, QtGui, QtWidgets
from email.mime.multipart import MIMEMultipart
from __about__ import Ui_Dialog as Ui_Dialog_about
from __default__ import Ui_Dialog as Ui_Dialog_default
from reimaginedQuantum.core import save_default, reload_default

from default import *

class Email():
    def __init__(self, email):
        self.address = None
        self.update(email)

    def validate(self, email):
        valid = False
        if email == None:
            return valid
        if '@' in email and '.' in email:
            valid = True
        return valid

    def clean(self, email):
        return email.replace(' ', '')

    def update(self, email):
        email = self.clean(email)
        valid = self.validate(email)
        if valid:
            self.address = email
        else:
            raise(Exception("'%s' is not a valid email."%email))

    def send(self, message):
        pass
        # try:
        #     toaddr = self.address
        #     msg = MIMEMultipart()
        #     msg['From'] = self.FROM
        #     msg['To'] = toaddr
        #     msg['Subject'] = "Reimagined Quantum Failed"
        #
        #     msg.attach(MIMEText(message, 'plain'))
        #
        #     server = smtplib.SMTP('smtp.gmail.com', 587)
        #     server.starttls()
        #
        #     server.login(self.FROM, get_password())
        #     text = msg.as_string()
        #     server.sendmail(self.FROM, toaddr, text)
        #     server.quit()
        # except Exception as e:
        #     pass

class DefaultWindow(QtWidgets.QDialog, Ui_Dialog_default):
    global FILE_NAME, USER_EMAIL
    global DEFAULT_SAMP, DEFAULT_COIN, MIN_SAMP, MAX_SAMP, \
            MIN_COIN, MAX_COIN, STEP_COIN
    global DEFAULT_CHANNELS, MIN_CHANNELS, MAX_CHANNELS
    global MIN_DELAY, MAX_DELAY, STEP_DELAY, DEFAULT_DELAY
    global MIN_SLEEP, MAX_SLEEP, STEP_SLEEP, DEFAULT_SLEEP

    def __init__(self, parent = None):
        super(DefaultWindow, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.LOCAL_NAMES = None
        self.LOCAL_CONSTANTS = {}
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.update)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.email_checkBox.stateChanged.connect(self.enable_email)

        if not SEND_EMAIL:
            self.email_checkBox.setChecked(False)

        self.local_constants()
        self.set_ranges()
        self.set_values()


    def local_constants(self):
        self.LOCAL_NAMES = ['FILE_NAME', 'USER_EMAIL', 'DEFAULT_SAMP',
                'DEFAULT_COIN', 'MIN_SAMP', 'MAX_SAMP', 'MIN_COIN', 'MAX_COIN',
                'STEP_COIN', 'DEFAULT_CHANNELS', 'MIN_CHANNELS', 'MAX_CHANNELS',
                'MIN_DELAY', 'MAX_DELAY', 'STEP_DELAY', 'DEFAULT_DELAY',
                'MIN_SLEEP', 'MAX_SLEEP', 'STEP_SLEEP', 'DEFAULT_SLEEP']

        for name in self.LOCAL_NAMES:
            value = eval(name)
            self.LOCAL_CONSTANTS[name] = value
            if type(value) != str:
                instruction = 'self.%s = %s'%(name, str(value))
            else:
                instruction = "self.%s = '%s'"%(name, value)
            exec(instruction)

    def set_ranges(self):
        self.ndetectors_spinBox.setMinimum(self.MIN_CHANNELS)
        self.ndetectors_spinBox.setMaximum(self.MAX_CHANNELS)

        self.delay_spinBox.setMinimum(self.MIN_DELAY)
        self.delay_spinBox.setMaximum(self.MAX_DELAY)
        self.delay_spinBox.setSingleStep(self.STEP_DELAY)

        self.sleep_spinBox.setMinimum(self.MIN_SLEEP)
        self.sleep_spinBox.setMaximum(self.MAX_SLEEP)
        self.sleep_spinBox.setSingleStep(self.STEP_SLEEP)

        self.sampling_spinBox.setMinimum(self.MIN_SAMP)
        self.sampling_spinBox.setMaximum(self.MAX_SAMP)

        self.coincidence_spinBox.setMinimum(self.MIN_COIN)
        self.coincidence_spinBox.setMaximum(self.MAX_COIN)
        self.coincidence_spinBox.setSingleStep(self.STEP_COIN)

    def set_values(self):
        self.ndetectors_spinBox.setValue(self.DEFAULT_CHANNELS)
        self.delay_spinBox.setValue(self.DEFAULT_DELAY)
        self.sleep_spinBox.setValue(self.DEFAULT_SLEEP)
        self.sampling_spinBox.setValue(self.DEFAULT_SAMP)
        self.coincidence_spinBox.setValue(self.DEFAULT_COIN)
        self.email_lineEdit.setText(self.USER_EMAIL)
        self.file_lineEdit.setText(self.FILE_NAME)

    def enable_email(self, state):
        if state == 0:
            self.email_lineEdit.setDisabled(True)
        else:
            self.email_lineEdit.setDisabled(False)

    def update(self):
        self.DEFAULT_CHANNELS = self.ndetectors_spinBox.value()
        self.DEFAULT_DELAY = self.delay_spinBox.value()
        self.DEFAULT_SLEEP = self.sleep_spinBox.value()
        self.DEFAULT_SAMP = self.sampling_spinBox.value()
        self.DEFAULT_COIN = self.coincidence_spinBox.value()
        self.USER_EMAIL = self.email_lineEdit.text()
        self.FILE_NAME = self.file_lineEdit.text()
        self.SEND_EMAIL = True
        if self.email_checkBox.checkState() == 0:
            self.SEND_EMAIL = False

        for name in self.LOCAL_NAMES:
            self.LOCAL_CONSTANTS[name] = eval('self.%s'%name)

        save_default(self.LOCAL_CONSTANTS)
        self.parent.update_constants(self.LOCAL_CONSTANTS)

    def reset(self):
        reload_default()
        self.local_constants()
        self.set_values()
        save_default(None)

class AboutWindow(QtWidgets.QDialog, Ui_Dialog_about):
    def __init__(self, parent = None):
        super(AboutWindow, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent

        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(220, 220, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(image)

        tausand = '<a href="https://www.tausand.com/"> https://www.tausand.com </a>'
        pages =  '<a href="https://tausand-dev.github.io/ReimaginedQuantum"> https://tausand-dev.github.io/ReimaginedQuantum </a>'
        message = "Reimagined Quantum is a suite of tools build to ensure your experience with Tausand's light detectors becomes simplified."
        self.message_label.setText(message)
        self.visit_label = QtWidgets.QLabel()
        self.github_label = QtWidgets.QLabel()
        self.pages_label = QtWidgets.QLabel()

        self.visit_label.setText("Visit us at: %s "%tausand)
        self.github_label.setText("More information on Reimagined Quantum implementation can be found at: %s"%pages)
        self.verticalLayout.addWidget(self.visit_label)
        self.verticalLayout.addWidget(self.github_label)

        self.visit_label.linkActivated.connect(self.open_link)
        self.github_label.linkActivated.connect(self.open_link)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def open_link(self, link):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))
