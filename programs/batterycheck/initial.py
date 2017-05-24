#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""
# FIXME: Upgrade this program to 3rd Generation standards with unittest.

import sys
import os
import inspect
import time
import subprocess
import tester
import share
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_int, lim_lo, lim_string,
    lim_boolean)
from . import console

ARM_VERSION = '1.7.4080'        # Software binary version
AVR_HEX = 'BatteryCheckSupervisor-2.hex'

# Serial port for the ARM console module.
ARM_CON = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Serial port for the ARM programmer.
ARM_PGM = {'posix': '/dev/ttyUSB1', 'nt': r'\\.\COM2'}[os.name]
# Serial port for the Bluetooth device
BT_PORT = {'posix': '/dev/ttyUSB2', 'nt': 'COM4'}[os.name]

AVRDUDE = {
    'posix': 'avrdude',
    'nt': r'C:\Program Files\AVRdude\avrdude.exe',
    }[os.name]

ARM_BIN = 'BatteryCheckControl_{}.bin'.format(ARM_VERSION)

SHUNT_SCALE = 0.08     # Ishunt * this = DC Source voltage

LIMITS = tester.testlimit.limitset((
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_hilo_delta('3V3', 3.3, 0.1),
    lim_hilo_delta('5VReg', 5.0, 0.1),
    lim_hilo_delta('12VReg', 12.0, 0.1),
    lim_hilo('shunt', -65.0, -60.0),
    lim_lo('Relay', 100),
    lim_hilo_int('PgmAVR', 0),
    lim_hilo_int('DetectBT', 0),
    lim_string('ARM_SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_hilo_delta('ARM_Volt', 12.0, 0.5),
    lim_hilo('ARM_Curr', -65.0, -60.0),
    lim_hilo_delta('Batt_Curr_Err', 0, 5.0),
    lim_boolean('BTscan', True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """BatteryCheck Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PreProgram', self._step_pre_program),
            tester.TestStep(
            'ProgramAVR', self._step_program_avr, not self.fifo),
            tester.TestStep(
            'ProgramARM', self._step_program_arm, not self.fifo),
            tester.TestStep('InitialiseARM', self._step_initialise_arm),
            tester.TestStep('TestARM', self._step_test_arm),
            tester.TestStep('TestBlueTooth', self._step_test_bluetooth),
            )
        global d, s, m
        self._limits = LIMITS
        self._sernum = None
        d = LogicalDevices(self.physical_devices, self.fifo)
        s = Sensors(d)
        m = Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

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
        self._sernum = share.get_sernum(
            self.uuts, self._limits['SerNum'], m.ui_SnEntry)
        tester.MeasureGroup((m.dmm_reg5V, m.dmm_reg12V, m.dmm_3V3), 2)

    def _step_program_avr(self):
        """Program the AVR ATtiny10 device."""
        d.rla_avr.set_on()
        time.sleep(2)   # Wait for the programmer to 'see' the 5V power
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        avr_cmd = [
            AVRDUDE,
            '-P', 'usb',
            '-p', 't10',
            '-c', 'avrisp2',
            '-U', 'flash:w:' + AVR_HEX,
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
        d.programmer.program()
        d.rla_arm.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device."""
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) * 3
                ):
            d.arm.puts(str)

        d.arm.open()
        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        d.arm['UNLOCK'] = True
        d.arm['NVWRITE'] = True
        time.sleep(1.0)  # NVWRITE delay
        d.arm['SER_ID'] = self._sernum
        d.arm['NVWRITE'] = True
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
                    (ARM_VERSION, ) +
                    ('12120', ) +
                    ('', )
                    ):
            d.arm.puts(str)

        d.dcs_shunt.output(62.5 * SHUNT_SCALE, True)
        time.sleep(1.5)  # ARM rdgs settle
        batt_curr, curr_ARM = tester.MeasureGroup(
            (m.dmm_shunt, m.currARM), timeout=5).readings
        # Compare simulated battery current against ARM reading, in %
        percent_error = ((batt_curr - curr_ARM) / batt_curr) * 100
        s.oMirCurrErr.store(percent_error)
        # Disable alarm process so it won't switch the relay back
        d.arm['SYS_EN'] = 4
        d.arm['ALARM-RELAY'] = True
        tester.MeasureGroup((m.dmm_relay, m.currErr, m.softARM, m.voltARM))
        d.arm['ALARM-RELAY'] = False
        d.dcs_shunt.output(0.0, False)

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function.

        Scan for BT device and match against serial number.

        """
        d.bt.puts('OK', preflush=2)
        d.bt.puts('OK', preflush=1)
        d.bt.puts('OK', preflush=1)
        d.bt.puts('+RDDSRES=112233445566,BCheck A1509020010,2,3')
        d.bt.puts('+RDDSCNF=0')

        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        self._logger.debug('Scan for Serial Number: "%s"', self._sernum)
        d.bt.open()
        reply = d.bt.scan(self._sernum)
        s.oMirBT.store(reply)
        m.BTscan.measure()
        d.bt.close()


class LogicalDevices():

    """BatteryCheck Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_input = tester.DCSource(devices['DCS1'])  # Fixture power
        self.dcs_shunt = tester.DCSource(devices['DCS2'])  # Shunt signal
        self.rla_avr = tester.Relay(devices['RLA1'])   # Connect AVR programmer
        self.rla_reset = tester.Relay(devices['RLA2'])   # ARM/AVR RESET signal
        self.rla_boot = tester.Relay(devices['RLA3'])    # ARM/AVR BOOT signal
        self.rla_arm = tester.Relay(devices['RLA4'])     # ARM programming port
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            ARM_BIN)
        self.programmer = share.ProgramARM(ARM_PGM, file, crpmode=False)
        # Serial connection to the console
        arm_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=9600, timeout=2)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = ARM_CON
        self.arm = console.Console(arm_ser)
        # Serial connection to the BT device
        self.btport = tester.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        self.btport.port = BT_PORT
        # BT Radio driver
        self.bt = share.BtRadio(self.btport)

    def reset(self):
        """Reset instruments."""
        self.arm.close()
        self.bt.close()
        for dcs in (self.dcs_input, self.dcs_shunt):
            dcs.output(0.0, output=False)
        for rla in (self.rla_avr, self.rla_reset,
                    self.rla_boot, self.rla_arm):
            rla.set_off()


class Sensors():

    """BatteryCheck Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        arm = logical_devices.arm
        sensor = tester.sensor
        self.ARMvolt = console.Sensor(arm, 'VOLTAGE')
        self.ARMcurr = console.Sensor(arm, 'CURRENT')
        self.ARMsoft = console.Sensor(
            arm, 'SW_VER', rdgtype=sensor.ReadingString)
        self.oMirAVR = sensor.Mirror()
        self.oMirBT = sensor.Mirror()
        self.oMirCurrErr = sensor.Mirror()
        self.o3V3 = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.reg5V = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.reg12V = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self.shunt = sensor.Vdc(
            dmm, high=3, low=1, rng=1, res=0.001, scale=-1250)
        self.relay = sensor.Res(dmm, high=2, low=2, rng=10000, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('batterycheck_initial', 'msgSnEntry'),
            caption=tester.translate('batterycheck_initial', 'capSnEntry'))


class Measurements():

    """BatteryCheck Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.pgmAVR = Measurement(limits['PgmAVR'], sense.oMirAVR)
        self.detectBT = Measurement(limits['DetectBT'], sense.oMirBT)
        self.voltARM = Measurement(limits['ARM_Volt'], sense.ARMvolt)
        self.currARM = Measurement(limits['ARM_Curr'], sense.ARMcurr)
        self.softARM = Measurement(limits['ARM_SwVer'], sense.ARMsoft)
        self.currErr = Measurement(limits['Batt_Curr_Err'], sense.oMirCurrErr)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_reg5V = Measurement(limits['5VReg'], sense.reg5V)
        self.dmm_reg12V = Measurement(limits['12VReg'], sense.reg12V)
        self.dmm_shunt = Measurement(limits['shunt'], sense.shunt)
        self.dmm_relay = Measurement(limits['Relay'], sense.relay)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.BTscan = Measurement(limits['BTscan'], sense.oMirBT)
