#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""

import sys
import os
import inspect
import time
import subprocess
import logging
import jsonrpclib

import tester
from ...share.programmer import ProgramARM
from ...share.sim_serial import SimSerial
from . import support
from . import limit
from . import arm

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

_SHUNT_SCALE = 0.08     # Ishunt * this = DC Source voltage

# Serial port for the ARM programmer.
_ARM_PGM = {'posix': '/dev/ttyUSB1', 'nt': r'\\.\COM2'}[os.name]
# Serial port for the ARM console module.
_ARM_CON = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

_AVRDUDE = r'C:\Program Files\AVRdude\avrdude.exe'
_AVR_HEX = 'BatteryCheckSupervisor-2.hex'

_ARM_HEX = 'BatteryCheckControl_1.7.4080.hex'

_PYTHON27 = r'C:\Python27\pythonw.exe'

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


class Main(tester.TestSequence):

    """BatteryCheck Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PreProgram', self._step_pre_program, None, True),
            ('ProgramAVR', self._step_program_avr, None, not fifo),
            ('ProgramARM', self._step_program_arm, None, not fifo),
            ('InitialiseARM', self._step_initialise_arm, None, True),
            ('TestARM', self._step_test_arm, None, True),
            ('TestBlueTooth', self._step_test_bluetooth, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._sernum = None
        self._btmac = None
        # Serial connection to the console
        arm_ser = SimSerial(simulation=self._fifo, baudrate=9600)
        # Set port separately, as we don't want it opened yet
        arm_ser.setPort(_ARM_CON)
        self._armdev = arm.Console(arm_ser)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._armdev)
        m = support.Measurements(s, self._limits)
        self._logger.debug('Starting bluetooth server')
        try:
            self._btserver = subprocess.Popen(
                [_PYTHON27, '../share/bluetooth/jsonrpc_server.py'],
                cwd=self._folder)
            self.btserver = jsonrpclib.Server('http://localhost:8888/')
        except FileNotFoundError:
            pass
        self._logger.debug('Connected to bluetooth server')

    def _arm_puts(self,
                 string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the buffer only if FIFOs are enabled."""
        if self._fifo:
            self._armdev.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        if not self._fifo:
            self._logger.debug('Stopping bluetooth server')
            self.btserver.stop()
            self._btserver.wait()
            self._logger.debug('Bluetooth server stopped')
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._armdev.close()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _step_pre_program(self):
        """Prepare for Programming.

        Set the Input DC voltage to 15V.
        Vbatt (12V Reg) is generated to power the unit.
        5V Reg and 12V Reg are generated to program the ATtiny10.

        """
        # Hold the ARM device in reset before power-on
        d.rla_reset.set_on()
        # Apply and check supply rails
        d.dcs_input.output(15.0, output=True)
        self.fifo_push(
            ((s.oSnEntry, ('A1429050001', )), (s.reg5V, 5.10),
             (s.reg12V, 12.00), (s.o3V3, 3.30), ))
        result, sernum = m.ui_SnEntry.measure()
        self._sernum = sernum[0]
        tester.measure.group((m.dmm_reg5V, m.dmm_reg12V, m.dmm_3V3), 2)

    def _step_program_avr(self):
        """Program the AVR ATtiny10 device."""
        d.rla_avr.set_on()
        # Wait for the programmer to 'see' the 5V power
        time.sleep(2)
        avr_cmd = [
            _AVRDUDE,
            '-P', 'usb',
            '-p', 't10',
            '-c', 'avrisp2',
            '-U', 'flash:w:' + _AVR_HEX,
            '-U', 'fuse:w:0xfe:m',
            ]
        try:
            console = subprocess.check_output(avr_cmd, cwd=self._folder)
            result = 0
            self._logger.debug(console)
        except subprocess.CalledProcessError:
            err_msg = '{} {}'.format(sys.exc_info()[0], sys.exc_info()[1])
            result = 1
            self._logger.warning(err_msg)
        d.rla_avr.set_off()
        s.oMirAVR.store(result)
        m.pgmAVR.measure()
        # Power cycle the unit to start the new code.
        d.dcs_input.output(output=False)
        time.sleep(1)
        d.dcs_input.output(output=True)

    def _step_program_arm(self):
        """
        Program the ARM device.

        The AVR will force the ARM into boot-loader mode 6.5sec
        after loss of the 5Hz heartbeat signal on BOOT.

        """
        d.rla_boot.set_on()
        d.rla_reset.set_off()
        self._logger.debug('Wait for AVR to bootload ARM...')
        time.sleep(6.5)
        d.rla_boot.set_off()
        # Connect ARM programming port
# FIXME: Use the python ARM programmer.
        d.rla_arm.set_on()
        arm = ProgramARM(
            _ARM_HEX, self._folder, s.oMirARM, _ARM_PGM,
            wipe=True, fifo=self._fifo)
        arm.read()
        m.pgmARM.measure()
        d.rla_arm.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device."""
        self._armdev.open()
        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        if self._fifo:
            self._btmac = '11:22:33:44:55:66'
        else:
            self._armdev.defaults()
            self._armdev.set_serial(self._sernum)
            self._btmac = self._armdev.mac()

    def _step_test_arm(self):
        """
        Get data from the ARM device.

        Simulate and read back battery current from the ARM.
        Test the alarm relay.

        """
        d.dcs_shunt.output(62.5 * _SHUNT_SCALE, True)
        time.sleep(1.5)  # ARM rdgs settle
        self.fifo_push(((s.shunt, 62.5 / 1250), (s.ARMcurr, -62.0), ))
        batt_curr, curr_ARM = MeasureGroup(
            (m.dmm_shunt, m.currARM), timeout=5)[1]
        # Compare simulated battery current against ARM reading, in %
        percent_error = ((batt_curr - curr_ARM) / batt_curr) * 100
        s.oMirCurrErr.store(percent_error)
        if not self._fifo:
            self._armdev.alarm(True)
        self.fifo_push(
            ((s.relay, 5.0), (s.ARMsoft, ('1.7.4080', )),
             (s.ARMvolt, 12.12), ))
        MeasureGroup((m.dmm_relay, m.currErr, m.softARM, m.voltARM))
        if not self._fifo:
            self._armdev.alarm(False)
        d.dcs_shunt.output(0.0, False)

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function."""
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', self._btmac)
        reply = True if self._fifo else self.btserver.detect(self._btmac)
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        s.oMirBT.store(0 if reply else 1)
        m.detectBT.measure()
