#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""

import sys
import os
import inspect
import subprocess
import time
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp, LimitBetween, LimitDelta, LimitBoolean, LimitInteger
    )
import share
from . import console


class Initial(share.TestSequence):

    """BatteryCheck Initial Test Program."""

    # Software binary version
    arm_version = '1.7.4080'
    avr_hex = 'BatteryCheckSupervisor-2.hex'
    avrdude = {
        'posix': 'avrdude',
        'nt': r'C:\Program Files\AVRdude\avrdude.exe',
        }[os.name]
    arm_bin = 'BatteryCheckControl_{}.bin'.format(arm_version)
    # Ishunt * this = DC Source voltage
    shunt_scale = 0.08
    limitdata = (
        LimitDelta('3V3', 3.3, 0.1),
        LimitDelta('5VReg', 5.0, 0.1),
        LimitDelta('12VReg', 12.0, 0.1),
        LimitBetween('shunt', -65.0, -60.0),
        LimitLow('Relay', 100),
        LimitInteger('PgmAVR', 0),
        LimitInteger('DetectBT', 0),
        LimitRegExp(
            'ARM_SwVer', '^{0}$'.format(arm_version.replace('.', r'\.'))),
        LimitDelta('ARM_Volt', 12.0, 0.5),
        LimitBetween('ARM_Curr', -65.0, -60.0),
        LimitDelta('Batt_Curr_Err', 0, 5.0),
        LimitBoolean('BTscan', True),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PreProgram', self._step_pre_program),
            TestStep('ProgramAVR', self._step_program_avr),
            TestStep('ProgramARM', self._step_program_arm),
            TestStep('InitialiseARM', self._step_initialise_arm),
            TestStep('ARM', self._step_test_arm),
            TestStep('BlueTooth', self._step_test_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_pre_program(self, dev, mes):
        """Prepare for Programming.

        Set the Input DC voltage to 15V.
        Vbatt (12V Reg) is generated to power the unit.
        5V Reg and 12V Reg are generated to program the ATtiny10.

        """
        # Hold the ARM device in reset before power-on
        dev['rla_reset'].set_on()
        # Apply and check supply rails
        dev['dcs_input'].output(15.0, output=True)
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_SnEntry')
        self.measure(('dmm_reg5V', 'dmm_reg12V', 'dmm_3V3'), timeout=2)

    @share.teststep
    def _step_program_avr(self, dev, mes):
        """Program the AVR ATtiny10 device."""
        dev['rla_avr'].set_on(delay=2)  # let programmer to 'see' the 5V power
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        avr_cmd = [
            self.avrdude,
            '-P', 'usb',
            '-p', 't10',
            '-c', 'avrisp2',
            '-U', 'flash:w:' + self.avr_hex,
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
        dev['rla_avr'].set_off()
        mes['pgmAVR'].sensor.store(result)
        mes['pgmAVR']()
        # Power cycle the unit to start the new code.
        dev['dcs_input'].output(output=False, delay=1)
        dev['dcs_input'].output(output=True)

    @share.teststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        The AVR will force the ARM into boot-loader mode 6.5sec
        after loss of the 5Hz heartbeat signal on BOOT.

        """
        dev['rla_boot'].set_on()
        dev['rla_reset'].set_off(delay=6.5) # Wait for AVR to bootload ARM...
        dev['rla_boot'].set_off()
        dev['rla_arm'].set_on()             # Connect ARM programming port
        dev['programmer'].program()
        dev['rla_arm'].set_off()

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device."""
        arm = dev['arm']
        arm.open()
        dev['rla_reset'].pulse_on(0.1)
        time.sleep(2)    # ARM startup delay
        arm['UNLOCK'] = True
        arm['NVWRITE'] = True
        time.sleep(1)    # NVWRITE delay
        arm['SER_ID'] = self.sernum
        arm['NVWRITE'] = True
        time.sleep(1)    # NVWRITE delay

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Get data from the ARM device.

        Simulate and read back battery current from the ARM.
        Test the alarm relay.

        """
        arm = dev['arm']
        dev['dcs_shunt'].output(62.5 * self.shunt_scale, True, delay=1.5)
        batt_curr, curr_ARM = self.measure(
            ('dmm_shunt', 'currARM'), timeout=5).readings
        # Compare simulated battery current against ARM reading, in %
        percent_error = ((batt_curr - curr_ARM) / batt_curr) * 100
        mes['currErr'].sensor.store(percent_error)
        # Disable alarm process so it won't switch the relay back
        arm['SYS_EN'] = 4
        arm['ALARM-RELAY'] = True
        self.measure(('dmm_relay', 'currErr', 'softARM', 'voltARM', ))
        arm['ALARM-RELAY'] = False
        dev['dcs_shunt'].output(0.0, False)

    @share.teststep
    def _step_test_bluetooth(self, dev, mes):
        """Test the Bluetooth transmitter function.

        Scan for BT device and match against serial number.

        """
        dev['rla_reset'].pulse_on(0.1)
        time.sleep(2)       # ARM startup delay
        blue = dev['bt']
        blue.open()
        mes['BTscan'].sensor.store(blue.scan(self.sernum))
        mes['BTscan']()
        blue.close()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_input', tester.DCSource, 'DCS1'),
                ('dcs_shunt', tester.DCSource, 'DCS2'), # Shunt signal
                ('rla_avr', tester.Relay, 'RLA1'),      # Connect AVR programmer
                ('rla_reset', tester.Relay, 'RLA2'),    # ARM/AVR RESET signal
                ('rla_boot', tester.Relay, 'RLA3'),     # ARM/AVR BOOT signal
                ('rla_arm', tester.Relay, 'RLA4'),      # ARM programming port
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            Initial.arm_bin)
        self['programmer'] = share.programmer.ARM(
            share.fixture.port('029083', 'ARM_PGM'), file,crpmode=False)
        # Serial connection to the console
        arm_ser = serial.Serial(baudrate=9600, timeout=2)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = share.fixture.port('029083', 'ARM_CON')
        self['arm'] = console.Console(arm_ser)
        # Serial connection to the Bluetooth device
        btport = serial.Serial(baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        btport.port = share.fixture.port('029083', 'BT')
        # BT Radio driver
        self['bt'] = share.bluetooth.BtRadio(btport)

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['bt'].close()
        for dcs in ('dcs_input', 'dcs_shunt'):
            self[dcs].output(0.0, output=False)
        for rla in ('rla_avr', 'rla_reset', 'rla_boot', 'rla_arm'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        arm = self.devices['arm']
        sensor = tester.sensor
        self['ARMvolt'] = share.console.Sensor(arm, 'VOLTAGE')
        self['ARMcurr'] = share.console.Sensor(arm, 'CURRENT')
        self['ARMsoft'] = share.console.Sensor(
            arm, 'SW_VER', rdgtype=sensor.ReadingString)
        self['oMirAVR'] = sensor.Mirror()
        self['oMirBT'] = sensor.Mirror()
        self['oMirCurrErr'] = sensor.Mirror()
        self['o3V3'] = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self['reg5V'] = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self['reg12V'] = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self['shunt'] = sensor.Vdc(
            dmm, high=3, low=1, rng=1, res=0.001, scale=-1250)
        self['relay'] = sensor.Res(dmm, high=2, low=2, rng=10000, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('batterycheck_initial', 'msgSnEntry'),
            caption=tester.translate('batterycheck_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('pgmAVR', 'PgmAVR', 'oMirAVR', ''),
            ('detectBT', 'DetectBT', 'oMirBT', ''),
            ('voltARM', 'ARM_Volt', 'ARMvolt', ''),
            ('currARM', 'ARM_Curr', 'ARMcurr', ''),
            ('softARM', 'ARM_SwVer', 'ARMsoft', ''),
            ('currErr', 'Batt_Curr_Err', 'oMirCurrErr', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_reg5V', '5VReg', 'reg5V', ''),
            ('dmm_reg12V', '12VReg', 'reg12V', ''),
            ('dmm_shunt', 'shunt', 'shunt', ''),
            ('dmm_relay', 'Relay', 'relay', ''),
            ('ui_SnEntry', 'SerNum', 'oSnEntry', ''),
            ('BTscan', 'BTscan', 'oMirBT', ''),
            ))
