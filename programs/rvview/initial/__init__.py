#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVVIEW Initial Test Program."""

from functools import wraps
import logging
import tester
import share
from . import support
from . import limit

INI_LIMIT = limit.DATA


def teststep(func):
    """Decorator to add arguments to the test step calls."""
    @wraps(func)
    def new_func(self):
        return func(self, self.logdev, self.meas)
    return new_func


class Initial(tester.TestSequence):

    """RVVIEW Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.phydev = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.sernum = None
        self.rvview = None

    def open(self):
        """Prepare for testing."""
        self.logdev = support.LogicalDevices(self.phydev, self.fifo)
        self.rvview = self.logdev.rvview
        self.sensors = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensors, self.limits)
        # Power to fixture Comms circuits.
        self.logdev.dcs_vcom.output(9.0, True)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep(
                'Program', self.logdev.programmer.program, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('Display', self._step_display),
            tester.TestStep('CanBus', self._step_canbus),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self.logdev.dcs_vcom.output(0.0, False)
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.rvview = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @teststep
    def _step_power_up(self, dev, mes):
        """Apply input voltage and measure voltages."""
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_SnEntry)
        dev.dcs_vin.output(limit.VIN_SET, True)
        tester.MeasureGroup((mes.dmm_vin, mes.dmm_3V3), timeout=5)

    @teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Reset the device, set HW version & Serial number.

        """
        self.rvview.open()
        self.rvview.brand(limit.ARM_HW_VER, self.sernum, dev.rla_reset)
        mes.arm_swver.measure()

    @teststep
    def _step_display(self, dev, mes):
        """Test the LCD.

        Put device into test mode.
        Check all segments and backlight.

        """
        self.rvview.testmode(True)
        tester.MeasureGroup(
            (mes.ui_YesNoOn, mes.dmm_BkLghtOn, mes.ui_YesNoOff,
             mes.dmm_BkLghtOff),
            timeout=5)
        self.rvview.testmode(False)

    @teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes.arm_can_bind.measure(timeout=10)
        self.rvview.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self.rvview['CAN'] = limit.CAN_ECHO
        echo_reply = dev.rvview_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self.sensors.mir_can.store(echo_reply)
        mes.rx_can.measure()
