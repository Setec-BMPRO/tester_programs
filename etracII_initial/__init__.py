#!/usr/bin/env python3
"""ETrac-II Initial Test Program."""

import os
import inspect
import logging

import tester
import share.programmer
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

_PIC_HEX = 'etracII-2A.hex'


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """ETrac-II Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, True),
            ('Load', self._step_load, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input DC and measure voltages."""
        self.fifo_push(((s.oVin, 13.0), (s.oVin2, 12.0),
                         (s.o5V, 5.0), ))
        t.pwr_up.run()

    def _step_program(self):
        """Program the PIC micro."""
        self._logger.info('Start PIC programmer')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        d.rla_Prog.set_on()
        pic = share.programmer.ProgramPIC(hexfile=_PIC_HEX,
                                          working_dir=folder,
                                          device_type='16F1828',
                                          sensor=s.oMirPIC,
                                          fifo=self._fifo)

        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        m.pgmPIC.measure()

    def _step_load(self):
        """Load and measure voltages."""
        self.fifo_push(((s.o5Vusb, 5.1), (s.oVbat, (8.45, 8.4)), ))
        t.load.run()
