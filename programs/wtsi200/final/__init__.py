#!/usr/bin/e nv python3
"""WTSI200 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Final(tester.TestSequence):

    """WTSI200 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerOn', self._step_power_on, None, True),
            ('Tank1', self._step_tank1, None, True),
            ('Tank2', self._step_tank2, None, True),
            ('Tank3', self._step_tank3, None, True),
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
        s = support.Sensors(d)
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
        self._devices.interface.reset()
        d.error_check()

    def _step_power_on(self):
        """Power up with 12V and measure level1 for all tanks."""
        self.fifo_push(((s.oTankLevels, ((3.25, 3.25, 3.25),)), ))
        t.pwr_on.run()

    def _step_tank1(self):
        """Vary levels for tank1 and measure."""
        self.fifo_push(
            ((s.oTankLevels,
             ((2.4, 3.25, 3.25), (1.7, 3.25, 3.25), (0.25, 3.25, 3.25),)), ))
        t.tank1.run()

    def _step_tank2(self):
        """Vary levels for tank2 and measure."""
        self.fifo_push(
            ((s.oTankLevels,
             ((3.25, 2.4, 3.25), (3.25, 1.7, 3.25), (3.25, 0.25, 3.25),)), ))
        t.tank2.run()

    def _step_tank3(self):
        """Vary levels for tank3 and measure."""
        self.fifo_push(
            ((s.oTankLevels,
             ((3.25, 3.25, 2.4), (3.25, 3.25, 1.7), (3.25, 3.25, 0.25),)), ))
        t.tank3.run()
