#!/usr/bin/env python3
"""Trek2 Initial Test Program."""

import os
import inspect
import serial
import logging

import tester
import share.programmer
import share.trek2
import share.isplpc
import share.mock_serial
from . import support
from . import limit


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt':    'COM2',
             }[os.name]

_ARM_BIN = 'Trek2_1.0.102.bin'

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """Trek2 Initial Test Program."""

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
            ('TestArm', self._step_test_arm, None, True),
            ('CanBus', self._step_canbus, None, True),
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
        try:
            self._arm_ser.close()
        except:
            pass
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
        self.fifo_push(((s.oVin, 12.0), (s.o3V3, 3.3), ))
        t.pwr_up.run()

    def _step_program(self):
        """Program the ARM device."""
        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        # Start the ARM programmer
        self._logger.info('Start ARM programmer')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        ser = serial.Serial(port=_ARM_PORT, baudrate=115200)
        ser.flush()
        # Program the device (LPC1549 has internal CRC, so no need for verify)
        pgm = share.isplpc.Programmer(
            ser, bindata, erase_only=False, verify=False, crpmode=False)
        try:
            pgm.program()
            s.oMirARM.store(0)
        except share.isplpc.ProgrammingError:
            s.oMirARM.store(1)
        ser.close()

        m.pgmARM.measure()
        # Reset BOOT to ARM
        d.rla_boot.set_off()

    def _step_test_arm(self):
        """Test the ARM device."""
        self.fifo_push(
            ((s.oSnEntry, ('A1429050001', )), (s.oBkLght, (4.0, 0)),  ))

        sernum = m.ui_SnEntry.measure()[1][0]
        hwver = (1, 0, '')
        if self._fifo:
            self._arm_ser = share.mock_serial.MockSerial()
        else:
            self._arm_ser = serial.Serial(
                port=_ARM_PORT, baudrate=115200, timeout=0.1)
        _armdev = share.trek2.Console(self._arm_ser)
        # Reset micro.
        d.rla_reset.pulse(0.1)
        if self._fifo:
            self._arm_ser.putch('50 0 X!', preflush=2)
        _armdev.action('50 0 X!')
        if self._fifo:
            self._arm_ser.putch('0 X?', preflush=2)
            self._arm_ser.put(b'50%')
        _armdev.action('0 X?')
        _armdev.defaults(hwver, sernum)

    def _step_canbus(self):
        """Test the Can Bus."""
