#!/usr/bin/env python3
"""Trek2 Final Test Program."""

import logging
import os
import time

import tester
from share.sim_serial import SimSerial
from . import support
from . import limit
from ..console import Console, ConsoleCanTunnel


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
_CAN_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM10'}[os.name]
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
            ('PowerUp', self._step_power_up, None, True),
            ('TunnelOpen', self._step_tunnel_open, None, True),
            ('Display', self._step_display, None, True),
            ('Tank0', self._step_tank0, None, True),
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
        # Connection to the Serial-to-CAN Trek2 inside the fixture
        ser_can = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        ser_can.setPort(_CAN_PORT)
        # CAN Console tunnel driver
        self._tunnel = ConsoleCanTunnel(
            port=ser_can, local_id=16, target_id=32)
        # Trek2 Console driver (using the CAN Tunnel)
        self._trek2 = Console(port=self._tunnel)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._trek2)
        m = support.Measurements(s, self._limits)
        # Switch on the USB hub & Serial ports
        d.dcs_Vcom.output(12.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global d, s, m
        # Switch off the USB hub & Serial ports
        d.dcs_Vcom.output(0.0, output=False)
        m = None
        d = None
        s = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._trek2.close()     # This is called even upon unit failures
        d.reset()               # Reset Logical Devices

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        d.dcs_Vin.output(12.0, output=True)
        time.sleep(9)           # Wait for CAN binding to finish

    def _step_tunnel_open(self):
        """Open console tunnel."""
        self._trek2.open()
        self._trek2.echo(echo_enable=False) # No command echo
        self._trek2.send_delay(delay=0)     # No delay, so send as strings
        self._trek2.testmode(True)

    def _step_display(self):
        """Display tests."""
        MeasureGroup((m.ui_YesNoSeg, m.ui_YesNoBklight, ))
        self._trek2.testmode(False)

    def _step_tank0(self):
        """Tank tests - Empty."""
        self._trek2['CONFIG'] = 0x7E00      # Enable all 4 tanks
        self._trek2['TANK_SPEED'] = 1.0     # Update interval
        time.sleep(1)
        MeasureGroup(m.tank0)

    def _step_tank1(self):
        """Tank tests - 1 sensor."""
        d.rla_s1.set_on()
        time.sleep(1)
        MeasureGroup(m.tank1)

    def _step_tank2(self):
        """Tank tests - 2 sensors."""
        d.rla_s2.set_on()
        time.sleep(1)
        MeasureGroup(m.tank2)

    def _step_tank3(self):
        """Tank tests - 3 sensors."""
        d.rla_s3.set_on()
        time.sleep(1)
        MeasureGroup(m.tank3)