#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
from isplpc import Programmer, ProgrammingError
from share import SimSerial
from ..console import DirectConsole
from . import support
from . import limit


MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
_CAN_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]
# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM10'}[os.name]
# Software image filename
_ARM_BIN = 'Trek2_{}.bin'.format(limit.BIN_VERSION)
# CAN echo request messages
_CAN_ECHO = 'TQQ,16,0'

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Initial(tester.TestSequence):

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
        self._trek2_ser = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self._trek2_ser.port = _ARM_PORT
        # Trek2 Console driver
        self._trek2 = DirectConsole(self._trek2_ser)
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
                    string_data, preflush=0, postflush=0, priority=False,
                    addprompt=True):
        """Push string data into the buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
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
        self.fifo_push(
            ((s.oSnEntry, ('A1526040123', )), (s.oVin, 12.0), (s.o3V3, 3.3), ))

        self.sernum = m.ui_SnEntry.measure().reading1
        t.pwr_up.run()

    def _step_program(self):
        """Program the ARM device."""
        d.rla_boot.set_on()
        d.rla_reset.pulse(0.1)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        ser = SimSerial(port=_ARM_PORT, baudrate=115200)
        try:
            pgm = Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=False)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except ProgrammingError:
                s.oMirARM.store(1)
        finally:
            ser.close()
        m.pgmARM.measure()
        d.rla_boot.set_off()

    def _step_test_arm(self):
        """Test the ARM device."""
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) + ('success', ) * 2 + ('', ) * 2 +
                (limit.BIN_VERSION, )
                ):
            self._trek2_puts(str)

        self._trek2.open()
        d.rla_reset.pulse(0.1)
        self._trek2.action(None, delay=1.5, expected=2)  # Flush banner
        self._trek2['UNLOCK'] = '$DEADBEA7'
        self._trek2['HW_VER'] = limit.HW_VER
        self._trek2['SER_ID'] = self.sernum
        self._trek2['NVDEFAULT'] = True
        self._trek2['NVWRITE'] = True
        m.trek2_SwVer.measure()

    def _step_canbus(self):
        """Test the Can Bus."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            self._trek2_puts(str)
        self._trek2_puts('RRQ,16,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.trek2_can_bind.measure(timeout=10)
        self._trek2.can_testmode(True)
        time.sleep(2)   # Let other CAN messages come in...
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(_CAN_ECHO))
        self._trek2['CAN'] = _CAN_ECHO
        echo_reply = self._trek2_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.oMirCAN.store(echo_reply)
        m.rx_can.measure()
