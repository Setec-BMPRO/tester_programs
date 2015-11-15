#!/usr/bin/env python3
"""Trek2 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
import share.isplpc
from share.sim_serial import SimSerial
from ..console import Console
from . import support
from . import limit


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
_CAN_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM10'}[os.name]
# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]
# Software image filename
_ARM_BIN = 'Trek2_1.0.11535.127.bin'
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
_HW_VER = (1, 0, 'A')

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
            ('Program', self._step_program, None, not fifo),
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
        # Serial connection to the Trek2 console
        trek2_ser = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        trek2_ser.setPort(_ARM_PORT)
        # Trek2 Console driver
        self._trek2 = Console(trek2_ser)
        self.sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._trek2)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        d.dcs_Vcom.output(12.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def _trek2_puts(self,
                    string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the Trek2 buffer only if FIFOs are enabled."""
        if self._fifo:
            self._trek2.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._trek2.close()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        dummy_sn = 'A1526040123'
        self.fifo_push(
            ((s.oSnEntry, (dummy_sn, )), (s.oVin, 12.0), (s.o3V3, 3.3), ))
        self.sernum = m.ui_SnEntry.measure()[1][0]
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
            ser = SimSerial(port=_ARM_PORT, baudrate=115200)
            # Program the device (LPC1549 has internal CRC for verification)
            pgm = share.isplpc.Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=False)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except share.isplpc.ProgrammingError:
                s.oMirARM.store(1)
        finally:
            try:
                ser.close()
            except:
                pass
        m.pgmARM.measure()
        # Reset BOOT to ARM
        d.rla_boot.set_off()

    def _step_test_arm(self):
        """Test the ARM device."""
        self._trek2.open()
        d.rla_reset.pulse(0.1)          # Reset micro.
        self._trek2_puts('Banner1\r\nBanner2\r\n')
        self._trek2.action(None, delay=1, expected=2)   # Flush banner
        self._trek2.defaults(_HW_VER, self.sernum)
        self._trek2_puts('1.0.11535.127\r\n')
        m.trek2_SwVer.measure()

    def _step_canbus(self):
        """Test the CAN Bus."""
        self.fifo_push(
            ((s.oCANBIND, 0x10000000), (s.oCANID, ('RRQ,16,0,7', )), ))
        m.trek2_can_bind.measure(timeout=5)
        time.sleep(1)   # Let junk CAN messages come in
        self._trek2_puts('0x10000000\r\n', preflush=1)
        self._trek2.can_mode(True)
        m.trek2_can_id.measure()
