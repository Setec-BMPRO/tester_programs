#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""SX-750 Initial Test Program."""

import os
import inspect
import time
import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitBetween, LimitDelta, LimitPercent,
    LimitInteger, LimitRegExp
    )
import share
from . import arduino
from . import console

BIN_VERSION = '3.1.2118'        # Software versions
PIC_HEX1 = 'sx750_pic5Vsb_1.hex'
PIC_HEX2 = 'sx750_picPwrSw_2.hex'

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM7'}[os.name]
# Serial port for the Arduino.
ARDUINO_PORT = {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name]
# Software image filenames
ARM_BIN = 'sx750_arm_{}.bin'.format(BIN_VERSION)

# Reading to reading difference for PFC voltage stability
PFC_STABLE = 0.05

# Fan ON threshold temperature (C)
FAN_THRESHOLD = 65.0

_5VSB_EXT = 6.3

LIMITS = (
    LimitDelta('8.5V Arduino', 8.5, 0.4),
    LimitLow('5Voff', 0.5),
    LimitDelta('5Vext', _5VSB_EXT - 0.8, 1.0),
    LimitDelta('5Vunsw', _5VSB_EXT - 0.8 - 0.7, 1.0),
    LimitPercent('5Vsb_set', 5.10, 1.5),
    LimitPercent('5Vsb', 5.10, 5.5),
    LimitLow('5Vsb_reg', 3.0),        # Load Reg < 3.0%
    LimitLow('12Voff', 0.5),
    LimitPercent('12V_set', 12.25, 2.0),
    LimitPercent('12V', 12.25, 8.0),
    LimitLow('12V_reg', 3.0),         # Load Reg < 3.0%
    LimitBetween('12V_ocp', 4, 63),     # Digital Pot setting - counts up from MIN
    LimitHigh('12V_inOCP', 4.0),       # Detect OCP when TP405 > 4V
    LimitBetween('12V_OCPchk', 36.2, 37.0),
    LimitLow('24Voff', 0.5),
    LimitPercent('24V_set', 24.13, 2.0),
    LimitPercent('24V', 24.13, 10.5),
    LimitLow('24V_reg', 7.5),         # Load Reg < 7.5%
    LimitBetween('24V_ocp', 4, 63),     # Digital Pot setting - counts up from MIN
    LimitHigh('24V_inOCP', 4.0),       # Detect OCP when TP404 > 4V
    LimitBetween('24V_OCPchk', 18.1, 18.5),
    LimitBetween('PriCtl', 11.40, 17.0),
    LimitLow('PGOOD', 0.5),
    LimitDelta('ACFAIL', 5.0, 0.5),
    LimitLow('ACOK', 0.5),
    LimitDelta('3V3', 3.3, 0.1),
    LimitDelta('ACin', 240, 10),
    LimitDelta('PFCpre', 420, 20),
    LimitDelta('PFCpost', 435, 1.0),
    LimitDelta('OCP12pre', 36, 2),
    LimitBetween('OCP12post', 35.7, 36.5),
    LimitLow('OCP12step', 0.116),
    LimitDelta('OCP24pre', 18, 1),
    LimitDelta('OCP24post', 18.2, 0.1),
    LimitLow('OCP24step', 0.058),
    # Data reported by the ARM
    LimitLow('ARM-AcFreq', 999),
    LimitLow('ARM-AcVolt', 999),
    LimitLow('ARM-12V', 999),
    LimitLow('ARM-24V', 999),
    LimitRegExp(
        'ARM-SwVer', '^{}$'.format(BIN_VERSION[:3].replace('.', r'\.'))),
    LimitRegExp('ARM-SwBld', '^{}$'.format(BIN_VERSION[4:])),
    LimitLow('FixtureLock', 200),
    LimitLow('PartCheck', 1.0),           # Photo sensor on D404
    LimitBetween('Snubber', 1000, 3000),    # Snubbing resistors
    LimitRegExp('Reply', '^OK$'),
    LimitInteger('Program', 0)
    )


class Initial(share.TestSequence):

    """SX-750 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PartDetect', self._step_part_detect),
            TestStep('Program', self._step_program_micros),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('PowerUp', self._step_powerup),
            TestStep('5Vsb', self._step_reg_5v),
            TestStep('12V', self._step_reg_12v),
            TestStep('24V', self._step_reg_24v),
            TestStep('PeakPower', self._step_peak_power),
            )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Check that Fixture Lock is closed."""
        self.measure(
            ('dmm_Lock', 'dmm_Part', 'dmm_R601', 'dmm_R602',
             'dmm_R609', 'dmm_R608'),
            timeout=2)

    @share.teststep
    def _step_program_micros(self, dev, mes):
        """Program the ARM and PIC devices.

        5Vsb is injected to power the ARM and 5Vsb PIC. PriCtl is injected
        to power the PwrSw PIC and digital pots.
        The ARM is programmed.
        The PIC's are programmed and the digital pots are set for maximum OCP.
        Unit is left unpowered.

        """
        # Set BOOT active before power-on so the ARM boot-loader runs
        dev['rla_boot'].set_on()
        # Apply and check injected rails
        self.dcsource(
            (('dcs_5Vsb', _5VSB_EXT), ('dcs_PriCtl', 12.0), ),
            output=True)
        self.measure(
            ('dmm_5Vext', 'dmm_5Vunsw', 'dmm_3V3', 'dmm_PriCtl',
             'dmm_8V5Ard',),
            timeout=5)
        if self.fifo:
            self._logger.info(
                '**** Programming skipped due to active FIFOs ****')
        else:
            dev['programmer'].program()  # Program the ARM device
        dev['ard'].open()
        time.sleep(2)        # Wait for Arduino to start
        dev['rla_pic1'].set_on()
        dev['rla_pic1'].opc()
        mes['dmm_5Vunsw'](timeout=2)
        mes['pgm_5vsb']()
        dev['rla_pic1'].set_off()
        dev['rla_pic2'].set_on()
        dev['rla_pic2'].opc()
        mes['pgm_pwrsw']()
        dev['rla_pic2'].set_off()
        mes['ocp_max']()
        # Switch off rails and discharge the 5Vsb to stop the ARM
        self.dcsource(
            (('dcs_5Vsb', 0.0), ('dcs_PriCtl', 0.0), ),
            output=False)
        self.dcload(
            (('dcl_5Vsb', 0.1), ), output=True, delay=0.5)
        # This will also enable all loads on an ATE3/4 tester.
        self.dcload(
            (('dcl_5Vsb', 0.0), ('dcl_12V', 0.0), ('dcl_24V', 0.0), ),
            output=True)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        5Vsb is injected to power the ARM.
        The ARM is initialised via the serial port.
        Unit is left unpowered.

        """
        arm = dev['arm']
        arm.open()
        dev['dcs_5Vsb'].output(_5VSB_EXT, True)
        self.measure(('dmm_5Vext', 'dmm_5Vunsw'), timeout=2)
        time.sleep(2)           # ARM startup delay
        arm['UNLOCK'] = True
        arm['FAN_SET'] = FAN_THRESHOLD
        arm['NVWRITE'] = True
        time.sleep(1.0)
        # Switch everything off
        dev['dcs_5Vsb'].output(0, False)
        dev['dcl_5Vsb'].output(0.1)
        time.sleep(0.5)
        dev['dcl_5Vsb'].output(0)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        ARM data readings are logged.
        PFC voltage is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev['acsource'].output(voltage=240.0, output=True)
        # A little load so PFC voltage falls faster
        dev['dcl_12V'].output(1.0)
        dev['dcl_24V'].output(1.0)
        self.measure(
            ('dmm_ACin', 'dmm_PriCtl', 'dmm_5Vsb_set', 'dmm_12Voff',
             'dmm_24Voff', 'dmm_ACFAIL'), timeout=2)
        # Switch all outputs ON
        dev['rla_pson'].set_on()
        self.measure(
            ('dmm_12V_set', 'dmm_24V_set', 'dmm_PGOOD'), timeout=2)
        # ARM data readings
        arm = dev['arm']
        arm['UNLOCK'] = True
        self.measure(
            ('arm_AcFreq', 'arm_AcVolt', 'arm_12V', 'arm_24V',
             'arm_SwVer', 'arm_SwBld'), )
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        pfc = mes['dmm_PFCpre'].stable(PFC_STABLE).reading1
        arm.calpfc(pfc)
        # Prevent a fail from failing the unit
        mes['dmm_PFCpost'].position_fail = False
        result = mes['dmm_PFCpost'].stable(PFC_STABLE).result
        # Allow a fail to fail the unit
        mes['dmm_PFCpost'].position_fail = True
        if not result:
            self._logger.info('Retry PFC calibration')
            pfc = mes['dmm_PFCpre'].stable(PFC_STABLE).reading1
            arm.calpfc(pfc)
            mes['dmm_PFCpost'].stable(PFC_STABLE)
        # Leave the loads at zero
        dev['dcl_12V'].output(0)
        dev['dcl_24V'].output(0)

    @share.teststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5Vsb.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes['dmm_5Vsb'], dcl_out=dev['dcl_5Vsb'],
            reg_limit=self.limits['5Vsb_reg'], max_load=2.0, peak_load=2.5)
        dev['dcl_5Vsb'].output(0)

    @share.teststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 0, Max = 32A, Peak = 36A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    34.0 - 38.0A
        Post adjustment range   36.2 - 36.6A
        Adjustment resolution   116mA/step
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes['dmm_12V'], dcl_out=dev['dcl_12V'],
            reg_limit=self.limits['12V_reg'], max_load=32.0, peak_load=36.0)
        self.ocp_set(
            target=36.6, load=dev['dcl_12V'],
            dmm=mes['dmm_12V'], detect=mes['dmm_12V_inOCP'],
            enable=mes['ocp12_unlock'], olimit=self.limits['12V_ocp'])
        with tester.PathName('OCPcheck'):
            dev['dcl_12V'].binary(0.0, 36.6 * 0.9, 2.0)
            mes['rampOcp12V']()
            dev['dcl_12V'].output(1.0)
            dev['dcl_12V'].output(0.0)

    @share.teststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0, Max = 15A, Peak = 18A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    17.0 - 19.0A
        Post adjustment range   18.1 - 18.3A
        Adjustment resolution   58mA/step
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes['dmm_24V'], dcl_out=dev['dcl_24V'],
            reg_limit=self.limits['24V_reg'], max_load=15.0, peak_load=18.0)
        self.ocp_set(
            target=18.3, load=dev['dcl_24V'],
            dmm=mes['dmm_24V'], detect=mes['dmm_24V_inOCP'],
            enable=mes['ocp24_unlock'], olimit=self.limits['24V_ocp'])
        with tester.PathName('OCPcheck'):
            dev['dcl_24V'].binary(0.0, 18.3 * 0.9, 2.0)
            mes['rampOcp24V']()
            dev['dcl_24V'].output(1.0)
            dev['dcl_24V'].output(0.0)

    @share.teststep
    def _step_peak_power(self, dev, mes):
        """Check operation at Peak load.

        5Vsb @ 2.5A, 12V @ 36.0A, 24V @ 18.0A
        Unit is left running at no load.

        """
        dev['dcl_5Vsb'].binary(start=0.0, end=2.5, step=1.0)
        dev['dcl_12V'].binary(start=0.0, end=36.0, step=2.0)
        dev['dcl_24V'].binary(start=0.0, end=18.0, step=2.0)
        self.measure(
            ('dmm_5Vsb', 'dmm_12V', 'dmm_24V', 'dmm_PGOOD'), timeout=2)
        dev['dcl_24V'].output(0)
        dev['dcl_12V'].output(0)
        dev['dcl_5Vsb'].output(0)

    def ocp_set(self, target, load, dmm, detect, enable, olimit):
        """Set OCP of an output.

        target: Target setpoint in Amp.
        load: Load instrument.
        dmm: Measurement of output voltage.
        detect: Measurement of 'In OCP'.
        enable: Measurement to call to enable digital pot.
        olimit: Limit to check OCP pot setting.

        OCP has been set to maximum in the programming step.
        Apply the desired load current, then lower the OCP setting until
        OCP triggers. The unit is left running at no load.

        """
        with tester.PathName('OCPset'):
            load.output(target)
            dmm.measure()
            detect.configure()
            detect.opc()
            enable.measure()
            setting = 0
            for setting in range(63, 0, -1):
                self.measurements['ocp_step_dn']()
                if detect.measure().result:
                    break
            self.measurements['ocp_lock']()
            load.output(0.0)
            olimit.check(setting, 1)

    @staticmethod
    def reg_check(dmm_out, dcl_out, reg_limit, max_load, peak_load):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        reg_limit: TestLimit for Load Regulation.
        max_load: Maximum output load.
        peak_load: Peak output load.
        Unit is left running at peak load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName('NoLoad'):
            dcl_out.output(0.0)
            dcl_out.opc()
            volt00 = dmm_out.measure().reading1
        with tester.PathName('MaxLoad'):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
        with tester.PathName('LoadReg'):
            dcl_out.output(peak_load * 0.95)
            dcl_out.opc()
            volt = dmm_out.measure().reading1
            load_reg = 100.0 * (volt00 - volt) / volt00
            reg_limit.check(load_reg, 1)
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()


class LogicalDevices(share.LogicalDevices):

    """SX-750 Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_PriCtl', tester.DCSource, 'DCS1'),
                ('dcs_Arduino', tester.DCSource, 'DCS2'),
                ('dcs_5Vsb', tester.DCSource, 'DCS3'),
                ('dcs_Vcom', tester.DCSource, 'DCS4'),
                ('dcl_12V', tester.DCLoad, 'DCL1'),
                ('dcl_5Vsb', tester.DCLoad, 'DCL2'),
                ('dcl_24V', tester.DCLoad, 'DCL3'),
                ('rla_pic1', tester.Relay, 'RLA1'),
                ('rla_pic2', tester.Relay, 'RLA2'),
                ('rla_pson', tester.Relay, 'RLA3'),
                ('rla_boot', tester.Relay, 'RLA4'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, ARM_BIN)
        self['programmer'] = share.ProgramARM(
            ARM_PORT, file, boot_relay=self['rla_boot'])
        # Serial connection to the ARM console
        arm_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=57600, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = ARM_PORT
        self['arm'] = console.Console(arm_ser, verbose=False)
        # Serial connection to the Arduino console
        ard_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = ARDUINO_PORT
        self['ard'] = arduino.Arduino(ard_ser, verbose=False)
        # Switch on power to fixture
        self['dcs_Arduino'].output(12.0, output=True)
        self['dcs_Vcom'].output(9.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['ard'].close()
        self['acsource'].reset()
        self['dcl_5Vsb'].output(1.0)
        self['dcl_12V'].output(5.0)
        self['dcl_24V'].output(5.0)
        time.sleep(1)
        self['discharge'].pulse()
        for ld in ('dcl_5Vsb', 'dcl_12V', 'dcl_24V'):
            self[ld].output(0.0)
        for dcs in ('dcs_PriCtl', 'dcs_5Vsb'):
            self[dcs].output(0.0, False)
        for rla in ('rla_pic1', 'rla_pic2', 'rla_boot', 'rla_pson'):
            self[rla].set_off()

    def close(self):
        """Finished testing."""
        self['dcs_Arduino'].output(0.0, output=False)
        self['dcs_Vcom'].output(0.0, output=False)
        super().close()


class Sensors(share.Sensors):

    """SX-750 Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['o5Vsb'] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self['o5Vsbunsw'] = sensor.Vdc(dmm, high=18, low=3, rng=10, res=0.001)
        self['o8V5Ard'] = sensor.Vdc(dmm, high=19, low=8, rng=100, res=0.001)
        self['o12V'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['o12VinOCP'] = sensor.Vdc(dmm, high=10, low=2, rng=100, res=0.01)
        self['o24V'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o24VinOCP'] = sensor.Vdc(dmm, high=11, low=2, rng=100, res=0.01)
        self['PriCtl'] = sensor.Vdc(dmm, high=8, low=2, rng=100, res=0.01)
        self['PFC'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self['PGOOD'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.01)
        self['ACFAIL'] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self['ACin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['Lock'] = sensor.Res(dmm, high=12, low=4, rng=1000, res=1)
        self['Part'] = sensor.Vdc(dmm, high=13, low=7, rng=100, res=0.01)
        self['R601'] = sensor.Res(dmm, high=14, low=5, rng=10000, res=1)
        self['R602'] = sensor.Res(dmm, high=15, low=5, rng=10000, res=1)
        self['R609'] = sensor.Res(dmm, high=16, low=6, rng=10000, res=1)
        self['R608'] = sensor.Res(dmm, high=17, low=6, rng=10000, res=1)
        self['OCP12V'] = sensor.Ramp(
            stimulus=self.devices['dcl_12V'],
            sensor=self['o12VinOCP'],
            detect_limit=(self.limits['12V_inOCP'], ),
            start=36.6 * 0.9, stop=36.6 * 1.1, step=0.1, delay=0,
            reset=True, use_opc=True)
        self['OCP24V'] = sensor.Ramp(
            stimulus=self.devices['dcl_24V'],
            sensor=self['o24VinOCP'],
            detect_limit=(self.limits['24V_inOCP'], ),
            start=18.3 * 0.9, stop=18.3 * 1.1, step=0.1, delay=0,
            reset=True, use_opc=True)
        # Arduino sensors
        ard = self.devices['ard']
        for name, cmdkey in (
                ('pgm5Vsb', 'PGM_5VSB'),
                ('pgmPwrSw', 'PGM_PWRSW'),
                ('ocpMax', 'OCP_MAX'),
                ('ocp12Unlock', '12_OCP_UNLOCK'),
                ('ocp24Unlock', '24_OCP_UNLOCK'),
                ('ocpStepDn', 'OCP_STEP_DN'),
                ('ocpLock', 'OCP_LOCK'),
            ):
            self[name] = console.Sensor(
                ard, cmdkey, rdgtype=sensor.ReadingString)
        # ARM sensors
        arm = self.devices['arm']
        for name, cmdkey in (
                ('ARM_AcFreq', 'ARM-AcFreq'),
                ('ARM_AcVolt', 'ARM-AcVolt'),
                ('ARM_12V', 'ARM-12V'),
                ('ARM_24V', 'ARM-24V'),
            ):
            self[name] = console.Sensor(arm, cmdkey)
        for name, cmdkey in (
                ('ARM_SwVer', 'ARM_SwVer'),
                ('ARM_SwBld', 'ARM_SwBld'),
            ):
            self[name] = console.Sensor(
                arm, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """SX-750 Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_5Voff', '5Voff', 'o5Vsb', ''),
            ('dmm_5Vext', '5Vext', 'o5Vsb', ''),
            ('dmm_5Vunsw', '5Vunsw', 'o5Vsbunsw', ''),
            ('dmm_5Vsb_set', '5Vsb_set', 'o5Vsb', ''),
            ('dmm_5Vsb', '5Vsb', 'o5Vsb', ''),
            ('dmm_12V_set', '12V_set', 'o12V', ''),
            ('dmm_12V', '12V', 'o12V', ''),
            ('dmm_12Voff', '12Voff', 'o12V', ''),
            ('dmm_12V_inOCP', '12V_inOCP', 'o12VinOCP', ''),
            ('dmm_24V', '24V', 'o24V', ''),
            ('dmm_24V_set', '24V_set', 'o24V', ''),
            ('dmm_24Voff', '24Voff', 'o24V', ''),
            ('dmm_24V_inOCP', '24V_inOCP', 'o24VinOCP', ''),
            ('dmm_PriCtl', 'PriCtl', 'PriCtl', ''),
            ('dmm_PFCpre', 'PFCpre', 'PFC', ''),
            ('dmm_PFCpost', 'PFCpost', 'PFC', ''),
            ('dmm_ACin', 'ACin', 'ACin', ''),
            ('dmm_PGOOD', 'PGOOD', 'PGOOD', ''),
            ('dmm_ACFAIL', 'ACFAIL', 'ACFAIL', ''),
            ('dmm_ACOK', 'ACOK', 'ACFAIL', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_Lock', 'FixtureLock', 'Lock', ''),
            ('dmm_Part', 'PartCheck', 'Part', ''),
            ('dmm_R601', 'Snubber', 'R601', ''),
            ('dmm_R602', 'Snubber', 'R602', ''),
            ('dmm_R609', 'Snubber', 'R609', ''),
            ('dmm_R608', 'Snubber', 'R608', ''),
            ('rampOcp12V', '12V_OCPchk', 'OCP12V', ''),
            ('rampOcp24V', '24V_OCPchk', 'OCP24V', ''),
            ('dmm_8V5Ard', '8.5V Arduino', 'o8V5Ard', ''),
            ('pgm_5vsb', 'Reply', 'pgm5Vsb', ''),
            ('pgm_pwrsw', 'Reply', 'pgmPwrSw', ''),
            ('ocp_max', 'Reply', 'ocpMax', ''),
            ('ocp12_unlock', 'Reply', 'ocp12Unlock', ''),
            ('ocp24_unlock', 'Reply', 'ocp24Unlock', ''),
            ('ocp_step_dn', 'Reply', 'ocpStepDn', ''),
            ('ocp_lock', 'Reply', 'ocpLock', ''),
            ('arm_AcFreq', 'ARM-AcFreq', 'ARM_AcFreq', ''),
            ('arm_AcVolt', 'ARM-AcVolt', 'ARM_AcVolt', ''),
            ('arm_12V', 'ARM-12V', 'ARM_12V', ''),
            ('arm_24V', 'ARM-24V', 'ARM_24V', ''),
            ('arm_SwVer', 'ARM-SwVer', 'ARM_SwVer', ''),
            ('arm_SwBld', 'ARM-SwBld', 'ARM_SwBld', ''),
            ))
        # Suppress signals on these measurements.
        for name in (
                'dmm_12V_inOCP', 'dmm_24V_inOCP',
                'pgm_5vsb', 'pgm_pwrsw',
                'ocp_max', 'ocp12_unlock', 'ocp24_unlock',
                'ocp_step_dn', 'ocp_lock',
                ):
            self[name].send_signal = False
