#!/usr/bin/env python3
"""CN101 Initial Test Program."""

# FIXME: This program is not finished yet!

import os
import inspect
import logging
import time
import subprocess
import jsonrpclib

import tester
import share.isplpc
import share.cn101
from share.sim_serial import SimSerial
from . import support
from . import limit


MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt':    'COM2',
             }[os.name]
# Software image filename
_ARM_BIN = 'cn101_1.0.000.bin'
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
_HW_VER = (1, 0, '')

_PYTHON27 = r'C:\Python27\pythonw.exe'

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
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, not fifo),
            ('TestArm', self._step_test_arm, None, True),
            ('CanBus', self._step_canbus, None, True),
            ('BlueTooth', self._step_bluetooth, None, True),
            ('MotorControl', self._step_motor_control, None, True),
            ('TankSense', self._step_tank_sense, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._cn101 = share.cn101.Console(
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        self._cn101.setPort(_ARM_PORT)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._cn101)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        self._logger.debug('Starting bluetooth server')
        try:
            self._btserver = subprocess.Popen(
                [_PYTHON27, '../share/btserver.py'], cwd=self._folder)
            self.btserver = jsonrpclib.Server('http://localhost:8888/')
        except FileNotFoundError:
            pass
        self._logger.debug('Connected to bluetooth server')

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
        dummy_sn = 'A1526040123'
        self.fifo_push(((s.oSnEntry, (dummy_sn, )), ))
        sernum = m.ui_SnEntry.measure()[1][0]
        self._cn101.open()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        if self._fifo:
            self._cn101.puts('Banner1\r\nBanner2\r\n')
        self._cn101.action(None, delay=1, expected=2)   # Flush banner
        self._cn101.defaults(_HW_VER, sernum)
        if self._fifo:
            self._cn101.puts('1.0.10892.110\r\n')
        m.cn101_SwVer.measure()
        if self._fifo:
            self._cn101.puts('112233445566\r\n')
        self._btmac = m.cn101_BtMac.measure()[1][0]

    def _step_canbus(self):
        """Test the CAN Bus."""
        self.fifo_push(
            ((s.oCANBIND, 0x10000000), (s.oCANID, ('RRQ,16,0,7', )), ))
        m.cn101_can_bind.measure(timeout=5)
        time.sleep(1)   # Let junk CAN messages come in
        if self._fifo:
            self._cn101.puts('0x10000000\r\n', preflush=1)
        self._cn101.can_mode(True)
        m.cn101_can_id.measure()

    def _step_bluetooth(self):
        """Test the Bluetooth transmitter function."""
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', self._btmac)
        if self._fifo:
            reply = True
        else:
            reply = self.btserver.detect(self._btmac)
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        s.oMirBT.store(0 if reply else 1)
        m.detectBT.measure()

    def _step_motor_control(self):
        """Activate awnings, slideouts and measure."""
        self.fifo_push(
            ((s.oAwnA, (12.0, 0.0)), (s.oAwnB, (12.0, 0.0)),
             (s.oSldA, (12.0, 0.0)), (s.oSldB, (12.0, 0.0)), ))
        t.motctrl.run()

    def _step_tank_sense(self):
        """Activate tank sensors and read."""
