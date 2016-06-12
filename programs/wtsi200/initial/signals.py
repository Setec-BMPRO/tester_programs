#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PyDispatcher message sender and signal classes.

Use class singletons to ensure unique signals.

"""

class _Signal(object):

    """Used to represent signal values."""

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return self._name


# SENDERS = Which thread the message comes from.
class Thread(object):

    """Pseudo enumerated type for available senders."""

    gui = _Signal('Thread.gui')

# SIGNALS = What signal it is.
class _MySignal(_Signal):

    """User Interaction request signals"""

    def __init__(self, name):
        super(_MySignal, self).__init__(name)
        self.start_load_program = name + '.start_load_program'
        self.controller_load_program = name + '.controller_load_program'
        self.worker_message = name + '.worker_message'
        self.controller_message = name + '.controller_message'

MySignal = _MySignal('UiRequest')
