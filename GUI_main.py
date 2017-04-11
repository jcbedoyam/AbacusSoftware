#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 11:31:32 2017

@author: juan
"""

import sys
import GUI_images
from PyQt5 import QtCore, QtGui, QtWidgets

app = QtWidgets.QApplication(sys.argv)
splash_pix = QtGui.QPixmap(':/splash.png')
splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
progressBar = QtWidgets.QProgressBar(splash)
progressBar.setGeometry(250, 320, 100, 20)
#progressBar.setStyleSheet(DEFAULT_STYLE)
splash.show()
app.processEvents()
app.setWindowIcon(QtGui.QIcon(':/icon.png'))

from reimagined-quantum import *
progressBar.setValue(15)
from mainwindow import Ui_MainWindow
progressBar.setValue(30)
from channels import Ui_Dialog
progressBar.setValue(50)

thread = Thread(target=matplotlib_import)
thread.setDaemon(True)
thread.start()
i = 50
while thread.is_alive():
    if i < 95:
        i += 1
        progressBar.setValue(i)
    sleep(0.2)
from core import *
from matplotlib.ticker import EngFormatter
    
plt.rcParams.update({'font.size': 8})
