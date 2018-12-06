#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN9-540 Initial Test Program."""

import os
import inspect
import time
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitHigh, LimitRegExp,
    LimitBetween, LimitDelta, LimitPercent
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """GEN9-540 Initial Test Program."""

    # Reading to reading difference for PFC voltage stability
    pfc_stable = 0.05
    # Reading to reading difference for 12V voltage stability
    v12_stable = 0.005
    # ARM software image file
    arm_file = 'gen8_{0}.bin'.format(config.SW_VERSION)

    limitdata = (
        LimitHigh('FanShort', 500),
        LimitLow('FixtureLock', 200),
        LimitPercent('3V3', 3.30, 10.0),
        LimitLow('5Voff', 0.5),
        LimitPercent('5Vset', 5.10, 1.0),
        LimitPercent('5V', 5.10, 2.0),
        LimitLow('12Voff', 0.5),
        LimitDelta('12Vpre', 12.1, 1.0),
        LimitDelta('12Vset', 12.18, 0.01),
        LimitPercent('12V', 12.18, 2.5),
        LimitLow('24Voff', 0.5),
        LimitDelta('24Vpre', 24.0, 2.0),
        LimitBetween('24V', 22.80, 25.68),
        LimitLow('PwrFail', 0.5),
        LimitDelta('ACin', 240, 10),
        LimitBetween('12Vpri', 11.4, 17.0),
        LimitDelta('PFCpre', 435, 15),
        LimitDelta('PFCpost1', 440.0, 0.8),
        LimitDelta('PFCpost2', 440.0, 0.8),
        LimitDelta('PFCpost3', 440.0, 0.8),
        LimitDelta('PFCpost4', 440.0, 0.8),
        LimitDelta('PFCpost', 440.0, 0.9),
        LimitDelta('ARM-AcFreq', 50, 10),
        LimitLow('ARM-AcVolt', 300),
        LimitDelta('ARM-5V', 5.0, 1.0),
        LimitDelta('ARM-12V', 12.0, 1.0),
        LimitDelta('ARM-24V', 24.0, 2.0),
        LimitRegExp('SwVer', '^{0}$'.format(
            config.SW_VERSION.replace('.', r'\.'))),
        LimitRegExp('SwBld', '^{0}$'.format(config.SW_VERSION[4:])),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PartDetect', self._step_part_detect),
            TestStep('Program', self._step_program),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('PowerUp', self._step_powerup),
            TestStep('5V', self._step_reg_5v),
            TestStep('12V', self._step_reg_12v),
            TestStep('24V', self._step_reg_24v),
            )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        5Vsb is injected to power up the ARM.

        """
        self.measure(('dmm_lock', 'dmm_fanshort'), timeout=2)
        dev['dcs_5v'].output(5.15, True)
        self.measure(('dmm_5v', 'dmm_3v3'), timeout=2)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected 5Vsb.
        Unit is left running the new code.

        """
        dev['program_arm'].program()
        # Reset micro, wait for ARM startup
        dev['rla_reset'].pulse(0.1, delay=1)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected 5Vsb.
        The ARM is initialised via the serial port.

        Unit is left unpowered.

        """
        arm = dev['arm']
        arm.open()
        arm['UNLOCK'] = True
        arm['NVWRITE'] = True
        dev['dcs_5v'].output(0.0, False)
        dev['dcl_5v'].output(0.1, True)
        time.sleep(0.5)
        dev['dcl_5v'].output(0.0, True)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        PFC voltage is calibrated.
        12V is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev['acsource'].output(voltage=240.0, output=True)
        self.measure(
            ('dmm_acin', 'dmm_5vset', 'dmm_12vpri', 'dmm_12voff',
             'dmm_24voff', 'dmm_pwrfail', ),
            timeout=5)
        # Switch all outputs ON
        dev['rla_pson'].set_on()
        self.measure(('dmm_5vset', 'dmm_24vpre', ), timeout=5)
        # Unlock ARM
        arm = dev['arm']
        arm['UNLOCK'] = True
        # A little load so PFC voltage falls faster
        self.dcload((('dcl_12v', 1.0), ('dcl_24v', 1.0)), output=True)
        # Calibrate the PFC set voltage
        pfc = mes['dmm_pfcpre'].stable(self.pfc_stable).reading1
        arm.calpfc(pfc)
        result, _, pfc = mes['dmm_pfcpost1'].stable(self.pfc_stable)
        if not result:      # 1st retry
            arm.calpfc(pfc)
            result, _, pfc = mes['dmm_pfcpost2'].stable(self.pfc_stable)
        if not result:      # 2nd retry
            arm.calpfc(pfc)
            result, _, pfc = mes['dmm_pfcpost3'].stable(self.pfc_stable)
        if not result:      # 3rd retry
            arm.calpfc(pfc)
            mes['dmm_pfcpost4'].stable(self.pfc_stable)
        # A final PFC setup check
        mes['dmm_pfcpost'].stable(self.pfc_stable)
        # no load for 12V calibration
        self.dcload((('dcl_12v', 0.0), ('dcl_24v', 0.0), ))
        # Calibrate the 12V set voltage
        v12 = mes['dmm_12vpre'].stable(self.v12_stable).reading1
        arm.cal12v(v12)
        # Prevent a fail from failing the unit
        mes['dmm_12vset'].position_fail = False
        result = mes['dmm_12vset'].stable(self.v12_stable).result
        # Allow a fail to fail the unit
        mes['dmm_12vset'].position_fail = True
        if not result:
            v12 = mes['dmm_12vpre'].stable(self.v12_stable).reading1
            arm.cal12v(v12)
            mes['dmm_12vset'].stable(self.v12_stable)
        self.measure(
            ('arm_acfreq', 'arm_acvolt', 'arm_5v', 'arm_12v', 'arm_24v',
             'arm_swver', 'arm_swbld'), )

    @share.teststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5V.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        self.dcload((('dcl_12v', 4.0), ('dcl_24v', 0.1), ))
        self.reg_check(
            dmm_out=mes['dmm_5v'], dcl_out=dev['dcl_5v'],
            max_load=2.0, peak_load=2.5)

    @share.teststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 4.0, Max = 24A, Peak = 28A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        dev['dcl_24v'].output(0.1)
        self.reg_check(
            dmm_out=mes['dmm_12v'], dcl_out=dev['dcl_12v'],
            max_load=24.0, peak_load=28.0)

    @share.teststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0.1, Max = 10A, Peak = 15A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        dev['dcl_12v'].output(4.0)
        self.reg_check(
            dmm_out=mes['dmm_24v'], dcl_out=dev['dcl_24v'],
            max_load=10.0, peak_load=15.0)

    def reg_check(self, dmm_out, dcl_out, max_load, peak_load):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        max_load: Maximum output load.
        peak_load: Peak output load.
        fet: Measurement instance to check 24V output FET

        Unit is left running at no load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName('NoLoad'):
            dcl_out.output(0.0)
            dcl_out.opc()
            dmm_out.measure()
        with tester.PathName('MaxLoad'):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()
        self.dcload((('dcl_5v', 0.0), ('dcl_12v', 0.0), ('dcl_24v', 0.0), ))


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_fixture', tester.DCSource, 'DCS1'),
                ('dcs_5v', tester.DCSource, 'DCS2'),
                ('dcl_24v', tester.DCLoad, 'DCL3'),
                ('dcl_12a', tester.DCLoad, 'DCL2'),
                ('dcl_12b', tester.DCLoad, 'DCL6'),
                ('dcl_5v', tester.DCLoad, 'DCL4'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_pson', tester.Relay, 'RLA3'),
                ('rla_sw', tester.Relay, 'RLA4'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcl_12v'] = tester.DCLoadParallel(
            ((self['dcl_12a'], 10), (self['dcl_12b'], 10)))
        # Serial port for the ARM. Used by programmer and ARM comms module.
        arm_port = share.fixture.port('025197', 'ARM')
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_arm'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, Initial.arm_file),
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the ARM console
        arm_ser = serial.Serial(baudrate=57600, timeout=2.0)
        # Set port separately - don't open until after programming
        arm_ser.port = arm_port
        self['arm'] = console.Console(arm_ser)
        # Switch on fixture power
        self['dcs_fixture'].output(10.0, output=True)
        self.add_closer(lambda: self['dcs_fixture'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        # Switch off AC Source and discharge the unit
        self['acsource'].reset()
        self['dcl_5v'].output(1.0)
        self['dcl_12v'].output(5.0)
        self['dcl_24v'].output(5.0)
        time.sleep(0.5)
        self['discharge'].pulse()
        for ld in ('dcl_5v', 'dcl_12v', 'dcl_24v'):
            self[ld].output(0.0, False)
        self['dcs_5v'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_pson', 'rla_sw'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['acin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['pfc'] = sensor.Vdc(dmm, high=3, low=3, rng=1000, res=0.001)
        self['o12vpri'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self['o15vccpri'] = sensor.Vdc(dmm, high=16, low=3, rng=100, res=0.01)
        self['o3v3'] = sensor.Vdc(dmm, high=5, low=4, rng=10, res=0.001)
        self['o5v'] = sensor.Vdc(dmm, high=6, low=4, rng=10, res=0.001)
        self['o12v'] = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self['o24v'] = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self['pwrfail'] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.01)
        self['fanshort'] = sensor.Res(dmm, high=10, low=5, rng=1000, res=0.1)
        self['lock'] = sensor.Res(dmm, high=11, low=6, rng=10000, res=1)
        arm = self.devices['arm']
        for name, cmdkey in (
                ('arm_acfreq', 'AcFreq'),
                ('arm_acvolt', 'AcVolt'),
                ('arm_5v', '5V'),
                ('arm_12v', '12V'),
                ('arm_24v', '24V'),
            ):
            self[name] = share.console.Sensor(arm, cmdkey)
        for name, cmdkey in (
                ('arm_swver', 'SwVer'),
                ('arm_swbld', 'SwBld'),
            ):
            self[name] = share.console.Sensor(
                arm, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'lock', ''),
            ('dmm_fanshort', 'FanShort', 'fanshort', ''),
            ('dmm_acin', 'ACin', 'acin', ''),
            ('dmm_12vpri', '12Vpri', 'o12vpri', ''),
            ('dmm_3v3', '3V3', 'o3v3', ''),
            ('dmm_5vset', '5Vset', 'o5v', ''),
            ('dmm_5v', '5V', 'o5v', ''),
            ('dmm_12voff', '12Voff', 'o12v', ''),
            ('dmm_12vpre', '12Vpre', 'o12v', ''),
            ('dmm_12vset', '12Vset', 'o12v', ''),
            ('dmm_12v', '12V', 'o12v', ''),
            ('dmm_24voff', '24Voff', 'o24v', ''),
            ('dmm_24vpre', '24Vpre', 'o24v', ''),
            ('dmm_24v', '24V', 'o24v', ''),
            ('dmm_pfcpre', 'PFCpre', 'pfc', ''),
            ('dmm_pfcpost1', 'PFCpost1', 'pfc', ''),
            ('dmm_pfcpost2', 'PFCpost2', 'pfc', ''),
            ('dmm_pfcpost3', 'PFCpost3', 'pfc', ''),
            ('dmm_pfcpost4', 'PFCpost4', 'pfc', ''),
            ('dmm_pfcpost', 'PFCpost', 'pfc', ''),
            ('dmm_pwrfail', 'PwrFail', 'pwrfail', ''),
            ('arm_acfreq', 'ARM-AcFreq', 'arm_acfreq', ''),
            ('arm_acvolt', 'ARM-AcVolt', 'arm_acvolt', ''),
            ('arm_5v', 'ARM-5V', 'arm_5v', ''),
            ('arm_12v', 'ARM-12V', 'arm_12v', ''),
            ('arm_24v', 'ARM-24V', 'arm_24v', ''),
            ('arm_swver', 'SwVer', 'arm_swver', ''),
            ('arm_swbld', 'SwBld', 'arm_swbld', ''),
            ))
        # Prevent test failures on these limits.
        for name in (
                'dmm_pfcpost1', 'dmm_pfcpost2', 'dmm_pfcpost3',
                'dmm_pfcpost4',
                ):
            self[name].position_fail = False
