import os
import smtplib
import __GUI_images__
from decouple import config
from email.mime.text import MIMEText
from reimaginedQuantum.constants import *
from PyQt5 import QtCore, QtGui, QtWidgets
from email.mime.multipart import MIMEMultipart
from __about__ import Ui_Dialog as Ui_Dialog_about
from __email__ import Ui_Dialog as Ui_Dialog_email
from __default__ import Ui_Dialog as Ui_Dialog_default
from reimaginedQuantum.core import save_default, reload_default

from default import *

class EmailWindow(QtWidgets.QDialog, Ui_Dialog_email):
    """
        Defines the email configuration dialog.
    """
    FROM = config('FROM')
    PASSWORD = config('PASSWORD')
    global USER_EMAIL, SEND_EMAIL
    def __init__(self, parent=None):
        super(EmailWindow, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.email = None
        self.valid = False
        if self.validate(USER_EMAIL):
            self.email = USER_EMAIL.replace(' ', '')
            self.lineEdit.setText(self.email)
            self.valid = True
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.update)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reset)

        message = "Reimagined Quantum will notify you in case a fatal error occurs.\n\n\
        Writing an email is completely optional.\n\
        For example: contact@tausand.com\n\n"
        message += "To stop poping up this screen go to Properties, Default and uncheck send email."
        self.message_label.setText(message)

    def validate(self, email):
        valid = False
        if email == None:
            return valid
        if '@' in email and '.' in email:
            valid = True
        return valid

    def update(self):
        email = self.lineEdit.text()
        valid = self.validate(email)
        if valid:
            if self.lineEdit.isEnabled():
                self.email = email.replace(' ', '')
                self.valid = True
                self.parent.default_window.email_lineEdit.setText(self.email)
                save_default(USER_EMAIL = self.email)
        else:
            if self.valid:
                self.lineEdit.setText(self.email)
            self.parent.errorWindow(Exception("'%s' is not a valid email."%email))

    def reset(self):
        email = self.lineEdit.text()
        valid = self.validate(email)

        if email != self.email:
            if self.valid:
                self.lineEdit.setText(self.email)
            else:
                self.lineEdit.setText('')
                self.email = None

    def send(self, message):
        if self.lineEdit.isEnabled():
            try:
                toaddr = self.email
                msg = MIMEMultipart()
                msg['From'] = self.FROM
                msg['To'] = toaddr
                msg['Subject'] = "Reimagined Quantum Failed"

                msg.attach(MIMEText(message, 'plain'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(self.FROM, self.PASSWORD)
                text = msg.as_string()
                server.sendmail(self.FROM, toaddr, text)
                server.quit()
            except Exception as e:
                print(e)

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
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.update)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.email_checkBox.stateChanged.connect(self.enable_email)

        if not SEND_EMAIL:
            self.email_checkBox.setChecked(False)

        self.set_ranges()
        self.set_values()

    def set_ranges(self):
        self.ndetectors_spinBox.setMinimum(MIN_CHANNELS)
        self.ndetectors_spinBox.setMaximum(MAX_CHANNELS)

        self.delay_spinBox.setMinimum(MIN_DELAY)
        self.delay_spinBox.setMaximum(MAX_DELAY)
        self.delay_spinBox.setSingleStep(STEP_DELAY)

        self.sleep_spinBox.setMinimum(MIN_SLEEP)
        self.sleep_spinBox.setMaximum(MAX_SLEEP)
        self.sleep_spinBox.setSingleStep(STEP_SLEEP)

        self.sampling_spinBox.setMinimum(MIN_SAMP)
        self.sampling_spinBox.setMaximum(MAX_SAMP)

        self.coincidence_spinBox.setMinimum(MIN_COIN)
        self.coincidence_spinBox.setMaximum(MAX_COIN)
        self.coincidence_spinBox.setSingleStep(STEP_COIN)

    def set_values(self):
        self.ndetectors_spinBox.setValue(DEFAULT_CHANNELS)
        self.delay_spinBox.setValue(DEFAULT_DELAY)
        self.sleep_spinBox.setValue(DEFAULT_SLEEP)
        self.sampling_spinBox.setValue(DEFAULT_SAMP)
        self.coincidence_spinBox.setValue(DEFAULT_COIN)
        self.email_lineEdit.setText(USER_EMAIL)
        self.file_lineEdit.setText(FILE_NAME)

    def enable_email(self, state):
        if state == 0:
            self.email_lineEdit.setDisabled(True)
            self.parent.email_window.lineEdit.setDisabled(True)
        else:
            self.email_lineEdit.setDisabled(False)
            self.parent.email_window.lineEdit.setDisabled(False)

    def confirm(self):
        message = 'In order to apply changes Reimagined Quantum needs to be restarted. \nBy clicking ok you agree to restart the application.'
        reply = QtWidgets.QMessageBox.question(self, 'Restart',
                         message, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            return True
        return False

    def update(self):
        answer = self.confirm()
        DEFAULT_CHANNELS = self.ndetectors_spinBox.value()
        DEFAULT_DELAY = self.delay_spinBox.value()
        DEFAULT_SLEEP = self.sleep_spinBox.value()
        DEFAULT_SAMP = self.sampling_spinBox.value()
        DEFAULT_COIN = self.coincidence_spinBox.value()
        USER_EMAIL = self.email_lineEdit.text()
        FILE_NAME = self.file_lineEdit.text()
        SEND_EMAIL = True
        if self.email_checkBox.checkState() == 0:
            SEND_EMAIL = False

        save_default(DEFAULT_CHANNELS, DEFAULT_DELAY, DEFAULT_SLEEP, DEFAULT_SAMP,
                                        DEFAULT_COIN, USER_EMAIL, FILE_NAME, SEND_EMAIL)

        if answer:
            self.parent.close()

    def reset(self):
        answer = self.confirm()
        if answer:
            reload_default()
            self.set_values()
            save_default()
            self.parent.close()

class AboutWindow(QtWidgets.QDialog, Ui_Dialog_about):
    def __init__(self, parent = None):
        super(AboutWindow, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent

        image = QtGui.QPixmap(':/splash.png')
        image = image.scaled(220, 220, QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(image)

        tausand = '<a href="https://www.tausand.com/"> https://www.tausand.com </a>'
        pages =  '<a href="https://jsbarbosa.github.io/reimagined-quantum"> https://jsbarbosa.github.io/reimagined-quantum </a>'
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
