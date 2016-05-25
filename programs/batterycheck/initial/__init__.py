#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""

import sys
import os
import inspect
import time
import subprocess
import logging
import tester
from isplpc import Programmer, ProgrammingError
from share import SimSerial, BtRadio
from ..console import Console
from . import support
from . import limit

MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA

# Serial port for the ARM programmer.
_ARM_PGM = {'posix': '/dev/ttyUSB1', 'nt': r'\\.\COM2'}[os.name]
# Serial port for the ARM console module.
_ARM_CON = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

_AVRDUDE = {
    'posix': 'avrdude',
    'nt': r'C:\Program Files\AVRdude\avrdude.exe',
    }[os.name]

_ARM_BIN = 'BatteryCheckControl_{}.bin'.format(limit.ARM_VERSION)

_BT_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM4'}[os.name]

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


class Initial(tester.TestSequence):

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
        # Serial connection to the console
        self._arm_ser = SimSerial(
            simulation=self._fifo, baudrate=9600, timeout=2)
        # Set port separately, as we don't want it opened yet
        self._arm_ser.port = _ARM_CON
        self._armdev = Console(self._arm_ser)
        # Serial connection to the BT device
        self._btport = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        self._btport.port = _BT_PORT
        # BT Radio driver
        self._bt = BtRadio(self._btport)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._armdev)
        m = support.Measurements(s, self._limits)

    def _arm_puts(self,
                   string_data, preflush=0, postflush=0, priority=False,
                   addprompt=True):
        """Push string data into the buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self._armdev.puts(string_data, preflush, postflush, priority)

    def _bt_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                   addcrlf=True):
        """Push string data into the buffer only if FIFOs are enabled."""
        if self._fifo:
            if addcrlf:
                string_data = string_data + '\r\n'
            self._btport.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
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
        self.fifo_push(
            ((s.oSnEntry, ('A1509020010', )), (s.reg5V, 5.10),
             (s.reg12V, 12.00), (s.o3V3, 3.30), ))

        # Hold the ARM device in reset before power-on
        d.rla_reset.set_on()
        # Apply and check supply rails
        d.dcs_input.output(15.0, output=True)
        self._sernum = m.ui_SnEntry.measure().reading1
        MeasureGroup((m.dmm_reg5V, m.dmm_reg12V, m.dmm_3V3), 2)

    def _step_program_avr(self):
        """Program the AVR ATtiny10 device."""
        d.rla_avr.set_on()
        # Wait for the programmer to 'see' the 5V power
        time.sleep(2)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        avr_cmd = [
            _AVRDUDE,
            '-P', 'usb',
            '-p', 't10',
            '-c', 'avrisp2',
            '-U', 'flash:w:' + limit.AVR_HEX,
            '-U', 'fuse:w:0xfe:m',
            ]
        try:
            console = subprocess.check_output(avr_cmd, cwd=folder)
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
        """Program the ARM device.

        The AVR will force the ARM into boot-loader mode 6.5sec
        after loss of the 5Hz heartbeat signal on BOOT.

        """
        d.rla_boot.set_on()
        d.rla_reset.set_off()
        self._logger.debug('Wait for AVR to bootload ARM...')
        time.sleep(6.5)
        d.rla_boot.set_off()
        d.rla_arm.set_on()      # Connect ARM programming port
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        ser = SimSerial(port=_ARM_PGM, baudrate=115200)
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
        d.rla_arm.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device."""
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) * 3
                ):
            self._arm_puts(str)

        self._armdev.open()
        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        self._armdev['UNLOCK'] = '$DEADBEA7'
        self._armdev['NVWRITE'] = True
        time.sleep(1.0)  # NVWRITE delay
        self._armdev['SER_ID'] = self._sernum
        self._armdev['NVWRITE'] = True
        time.sleep(1.0)  # NVWRITE delay

    def _step_test_arm(self):
        """Get data from the ARM device.

        Simulate and read back battery current from the ARM.
        Test the alarm relay.

        """
        self.fifo_push(
            ((s.relay, 5.0), (s.shunt, 62.5 / 1250), ))
        for str in (('-62000mA', ) +
                    ('', ) * 2 +
                    (limit.ARM_VERSION, ) +
                    ('12120', ) +
                    ('', )
                    ):
            self._arm_puts(str)

        d.dcs_shunt.output(62.5 * limit.SHUNT_SCALE, True)
        time.sleep(1.5)  # ARM rdgs settle
        batt_curr, curr_ARM = MeasureGroup(
            (m.dmm_shunt, m.currARM), timeout=5).readings
        # Compare simulated battery current against ARM reading, in %
        percent_error = ((batt_curr - curr_ARM) / batt_curr) * 100
        s.oMirCurrErr.store(percent_error)
        # Disable alarm process so it won't switch the relay back
        self._armdev['SYS_EN'] = 4
        self._armdev['ALARM-RELAY'] = True
        MeasureGroup((m.dmm_relay, m.currErr, m.softARM, m.voltARM))
        self._armdev['ALARM-RELAY'] = False
        d.dcs_shunt.output(0.0, False)

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function.

        Scan for BT device and match against serial number.

        """
        self._bt_puts('OK', preflush=2)
        self._bt_puts('OK', preflush=1)
        self._bt_puts('OK', preflush=1)
        self._bt_puts('+RDDSRES=112233445566,BCheck A1509020010,2,3')
        self._bt_puts('+RDDSCNF=0')

        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        self._logger.debug('Scan for Serial Number: "%s"', self._sernum)
        self._bt.open()
        reply = self._bt.scan(self._sernum)
        s.oMirBT.store(reply)
        m.BTscan.measure()
        self._bt.close()
