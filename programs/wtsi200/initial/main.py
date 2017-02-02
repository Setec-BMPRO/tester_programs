#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtGui
from pydispatch import dispatcher
import logging
import gui
import worker
import signals


class Controller():
    """
    Controller class keeps track of all dispatcher broadcasts
    """
    def __init__(self):
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        for sig, fun in (
                (signals.MySignal.start_load_program, self._load_program),
                (signals.MySignal.worker_message, self._message),
                ):
            dispatcher.connect(fun, sender=signals.Thread.gui, signal=sig)

    def _load_program(self, data):
        dispatcher.send(
            sender=signals.Thread.gui,
            signal=signals.MySignal.controller_load_program,
            data=data)

    def _message(self, data):
        dispatcher.send(
            sender=signals.Thread.gui,
            signal=signals.MySignal.controller_message,
            data=data)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        level=logging.DEBUG)
    w = worker.Worker()
    c = Controller()
    app = QtGui.QApplication(sys.argv)
    s = gui.Start()
    sys.exit(app.exec_())
