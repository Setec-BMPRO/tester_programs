#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide import QtGui
from pydispatch import dispatcher
import logging

import Ui_start
import signals


class Start(QtGui.QFrame, Ui_start.Ui_start):

    """User Interface."""

    def __init__(self):
        super(Start, self).__init__()
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        dispatcher.connect(
            self._message,
            sender=signals.Thread.gui,
            signal=signals.MySignal.controller_message)
        self.setupUi(self)
        self.setWindowTitle('Program loading Window')
        self.textBrowser.append(
            'Type the correct hex file name for '
            'your program below and press "OK" to '
            'create a header file for the Arduino...\n')
        self.move(50, 200)
        self.text = None
        self.show()

    def accept(self):
        dispatcher.send(
            sender=signals.Thread.gui,
            signal=signals.MySignal.start_load_program,
            data=self.text)

    def OnChanged(self, text):
        self.text = text

    def _message(self, data):
        self.textBrowser.append(data)

    def reject(self):
        self.close()
