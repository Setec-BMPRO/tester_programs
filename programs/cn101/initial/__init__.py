#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
from isplpc import Programmer, ProgrammingError
from ...share.sim_serial import SimSerial
from ...share.bluetooth.rn4020 import BleRadio
from ..console import Console
from . import support
from . import limit


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM15'}[os.name]
# ARM software image file
_ARM_BIN = 'cn101_{}.bin'.format(limit.BIN_VERSION)
# Serial port for the Bluetooth module.
_BLE_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM14'}[os.name]
# Serial port for the Trek2 as the CAN Bus interface.
#_CAN_PORT = {'posix': '/dev/ttyUSB2', 'nt': 'COM13'}[os.name]
# CAN echo request messages
_CAN_ECHO = 'TQQ,32,0'

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """CN101 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PartCheck', self._step_part_check, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, not fifo),
            ('TestArm', self._step_test_arm, None, True),
            ('Awning', self._step_awning, None, True),
            ('TankSense', self._step_tank_sense, None, True),
            ('Bluetooth', self._step_bluetooth, None, True),
            ('CanBus', self._step_canbus, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Serial connection to the CN101 console
        self._cn101_ser = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self._cn101_ser.setPort(_ARM_PORT)
        # CN101 Console driver
        self._cn101 = Console(self._cn101_ser)
        # Serial connection to the BLE module
        ble_ser = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.setPort(_BLE_PORT)
        self._ble = BleRadio(ble_ser)
        self._sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._cn101)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        d.dcs_vcom.output(12.0, output=True)
        time.sleep(5)   # Allow OS to detect the new ports

    def _cn101_puts(self,
                   string_data, preflush=0, postflush=0, priority=False,
                   addprompt=True):
        """Push string data into the BP35 buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self._cn101.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._cn101.close()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_part_check(self):
        """Measure Part detection microswitches."""
        self.fifo_push(((s.microsw, 10.0), (s.sw1, 10.0), (s.sw2, 10.0), ))
        MeasureGroup((m.dmm_microsw, m.dmm_sw1, m.dmm_sw2), 5)

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oSnEntry, ('A1526040123', )), (s.oVin, 8.0), (s.o3V3, 3.3), ))

        self._sernum = m.ui_serialnum.measure()[1][0]
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
        m.program.measure()
        d.rla_boot.set_off()

    def _step_test_arm(self):
        """Test the ARM device."""
        for str in (('Banner1\r\nBanner2', ) +
                    ('', ) * 5 ):
            self._cn101_puts(str)
        self._cn101_puts(limit.BIN_VERSION, postflush=0)

        self._cn101.open()
        d.rla_reset.pulse(0.1)
        self._cn101.action(None, delay=1.5, expected=2)   # Flush banner
        self._cn101['UNLOCK'] = '$DEADBEA7'
        self._cn101['HW_VER'] = limit.HW_VER
        self._cn101['SER_ID'] = self._sernum
        self._cn101['NVDEFAULT'] = True
        self._cn101['NVWRITE'] = True
        m.cn101_swver.measure()

    def _step_awning(self):
        """Test Awning relay operation."""
        self.fifo_push(
            ((s.oAwnA, (0.0, 11.0)), (s.oAwnB, (0.0, 11.0)), ))

        t.awning.run()

    def _step_tank_sense(self):
        """Activate tank sensors and read."""
        for str in (('', ) + ('5', ) * 4):
            self._cn101_puts(str)

        self._cn101['ADC_SCAN'] = 100
        t.tank.run()

    def _step_bluetooth(self):
        """Test the Bluetooth interface."""
        self._cn101_puts('001EC030BC15', )

        t.reset.run()
        _btmac = m.cn101_btmac.measure()[1][0]
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', _btmac)
        if self._fifo:
            reply = True
        else:
            self._ble.open()
            reply = self._ble.scan(_btmac)
            self._ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        s.oMirBT.store(reply)
        m.detectBT.measure()

    def _step_canbus(self):
        """Test the CAN interface."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            self._cn101_puts(str)
        self._cn101_puts('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.cn101_can_bind.measure(timeout=10)
        self._cn101.can_testmode(True)
        # From here on, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(_CAN_ECHO))
        self._cn101['CAN'] = _CAN_ECHO
        echo_reply = self._cn101_ser.readline().decode(errors='ignore')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.oMirCAN.store(echo_reply)
        m.cn101_rx_can.measure()
