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
# Software image filename
_ARM_BIN = 'Trek2_1.0.102.bin'
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
_HW_VER = (1, 0, '')

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
        self._arm_ser = None
        self._trek2 = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._trek2 = share.trek2.Console()
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits, self._trek2)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._trek2 = None
        self._arm_ser.close()
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
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        try:
            ser = serial.Serial(port=_ARM_PORT, baudrate=115200)
            ser.flush()
            # Program the device (LPC1549 has internal CRC for verification)
            pgm = share.isplpc.Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=False)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except share.isplpc.ProgrammingError:
                s.oMirARM.store(1)
        finally:
            ser.close()
        m.pgmARM.measure()
        # Reset BOOT to ARM
        d.rla_boot.set_off()

    def _step_test_arm(self):
        """Test the ARM device."""
        self.fifo_push(((s.oSnEntry, ('A1429050001', )), ))
        sernum = m.ui_SnEntry.measure()[1][0]
        ser_cls = share.mock_serial.MockSerial if self._fifo else serial.Serial
        self._arm_ser = ser_cls(port=_ARM_PORT, baudrate=115200, timeout=0.1)
        self._trek2.set_port(self._arm_ser)
        # Reset micro.
        d.rla_reset.pulse(0.1)
        if self._fifo:
            self._arm_ser.putch('$DEADBEA7 UNLOCK', preflush=1, postflush=1)
            self._arm_ser.putch('1 0 " SET-HW-VER', preflush=1, postflush=1)
            self._arm_ser.putch(
                '"A1429050001 SET-SERIAL-ID', preflush=1, postflush=1)
            self._arm_ser.putch('$DEADBEA7 UNLOCK', preflush=1, postflush=1)
            self._arm_ser.putch('NV-DEFAULT', preflush=1, postflush=1)
            self._arm_ser.putch('NV-WRITE', preflush=1, postflush=1)
            self._arm_ser.putch('RESTART', preflush=1)
            self._arm_ser.puts('Banner1\r\nBanner2\r\n')
        self._trek2.defaults(_HW_VER, sernum)

    def _step_canbus(self):
        """Test the Can Bus."""
        if self._fifo:
            self._arm_ser.putch('"TQQ,16,0 CAN', preflush=1)
            self._arm_ser.put(b'RRQ,16,0,7,0,0,0,0,0,0,0\r\n')
        m.trek2_can_id.measure()
