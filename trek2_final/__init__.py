#!/usr/bin/env python3
"""Trek2 Final Test Program."""

import logging
import time
import os

import tester
from . import support
from . import limit
import share.trek2


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
_CAN_PORT = {'posix': '/dev/ttyUSB0',
             'nt':    'COM10',
             }[os.name]
# Trek2 unit CAN Bus ID
_TREK2_ID = 32

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Trek2 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, False),
            ('Tunnel', self._step_tunnel, None, True),
            ('CanBus', self._step_canbus, None, False),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Connection to the Serial-to-CAN Trek2 inside the fixture
#        ser_can = share.sim_serial.SimSerial(
#            simulation=self._fifo, baudrate=115200, timeout=0.1)
        ser_can = share.sim_serial.SimSerial(
            simulation=False, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        ser_can.setPort(_CAN_PORT)
        # CAN Console tunnel driver
        self._tunnel = share.trek2.ConsoleCanTunnel(
            port=ser_can, local_id=16, target_id = 32)
        # Trek2 Console driver (using the CAN Tunnel)
        self._trek2 = share.trek2.Console(port=self._tunnel)

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

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(((s.oVin, 12.0), ))
        t.pwr_up.run()

    def _step_tunnel(self):
        """Open console tunnel."""
        self._trek2.open()

        self._trek2['SwVer']

        self._trek2.close()

    def _step_canbus(self):
        """Test the CAN Bus."""
        self.fifo_push(
            ((s.oCANBIND, 0x10000000), (s.oCANID, ('RRQ,16,0,7', )), ))
        m.trek2_can_bind.measure(timeout=5)
        time.sleep(1)   # Let junk CAN messages come in
        if self._fifo:
            self._trek2.puts('0x10000000\r\n', preflush=1)
        self._trek2.can_mode(True)
        m.trek2_can_id.measure()
