#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 SETEC Pty Ltd
"""SX-600 Initial Test Program."""

import pathlib
import time

import serial
import tester

import share
from . import arduino, config, console


class Initial(share.TestSequence):

    """SX-600 Initial Test Program."""

    def open(self, uut):
        """Prepare for testing."""
        self.cfg = config.Config
        self.cfg.configure(uut)
        self.uut = uut
        Sensors.ratings = self.cfg.ratings
        Sensors.projectfile = self.cfg.projectfile
        Sensors.sw_image = self.cfg.sw_image
        Devices.uut = uut
        self.limits = self.cfg.limits_initial
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Lock', self._step_lock),
            tester.TestStep('Program', self._step_program),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('5Vsb', self._step_reg_5v),
            tester.TestStep('12V', self._step_reg_12v),
            tester.TestStep('24V', self._step_reg_24v),
            tester.TestStep('PeakPower', self._step_peak_power),
            )

    @share.teststep
    def _step_lock(self, dev, mes):
        """Check that Fixture Lock is closed."""
        mes['dmm_Lock'](timeout=2)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the micro."""
        dev['dcs_5V'].output(self.cfg._5vsb_ext, True)
        self.measure(
            ('dmm_5Vext', 'dmm_5Vunsw', 'dmm_3V3', 'dmm_8V5Ard'),
            timeout=5)
        mes['JLink']()      # Program the micro

# TODO: Do we need to switch it off then on again ?
        # Switch off 5V rail and discharge the 5V to stop the ARM
        dev['dcs_5V'].output(0)
        self.dcload((('dcl_5V', 0.1), ), output=True, delay=0.5)

        # This will also enable all loads on an ATE3/4 tester.
        self.dcload(
            (('dcl_5V', 0.0), ('dcl_12V', 0.0), ('dcl_24V', 0.0), ),
            output=True)

# TODO: Do we need to switch it off then on again ?
        dev['dcs_5V'].output(self.cfg._5vsb_ext, True)
        self.measure(('dmm_5Vext', 'dmm_5Vunsw'), timeout=2)

        arm = dev['arm']
        arm.initialise()
        # Switch everything off
        dev['dcs_5V'].output(0, False)
        dev['dcl_5V'].output(0.1, delay=0.5)
        dev['dcl_5V'].output(0)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        ARM data readings are logged.
        PFC voltage is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev['acsource'].output(voltage=240.0, output=True)
        # Switch 5V output ON (SX-600)
        dev['rla_sw'].set_on()
        # A little load so PFC voltage falls faster
        dev['dcl_12V'].output(1.0)
        dev['dcl_24V'].output(1.0)
        arm = dev['arm']
        if self.uut.lot.item.revision not in arm.renesas_revisions:
            # renesas was restarted during initialise() so we
            # don't need to get the banner here.
            arm.action(expected=arm.banner_lines)
        self.measure(
            ('dmm_ACin', 'dmm_PriCtl', 'dmm_5Vnl', 'dmm_12Voff',
             'dmm_24Voff', 'dmm_ACFAIL', ), timeout=2)
        arm['UNLOCK'] = True
        arm['FAN_CHECK_DISABLE'] = True
        dev['dcs_PriCtl'].output(self.cfg.fixture_fan, True)  # Turn fan on
        # Switch all outputs ON
        dev['rla_pson'].set_on()
        self.measure(
            ('dmm_12V_set', 'dmm_24V_set', 'dmm_PGOOD'), timeout=2)
        # ARM data readings
        self.measure(('arm_AcFreq', 'arm_AcVolt', 'arm_12V', 'arm_24V', ))
        mes['ocp_max']()
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        pfc = mes['dmm_PFCpre'].stable(self.cfg.pfc_stable).reading1
        steps = round(
            (self.cfg.pfc_target - pfc) / self.cfg.pfc_volt_per_step)
        if steps > 0:       # Too low
            self._logger.debug('Step UP %s steps', steps)
            mes['pfcUpUnlock']()
            for _ in range(steps):
                mes['pfcStepUp']()
            mes['pfcUpLock']()
        elif steps < 0:     # Too high
            self._logger.debug('Step DOWN %s steps', -steps)
            mes['pfcDnUnlock']()
            for _ in range(-steps):
                mes['pfcStepDn']()
            mes['pfcDnLock']()
        if steps:   # Post-adjustment check
            mes['dmm_PFCpost'].stable(self.cfg.pfc_stable)
        # Leave the loads at zero
        dev['dcl_12V'].output(0)
        dev['dcl_24V'].output(0)

    @share.teststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5Vsb.

        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes['dmm_5V'],
            dcl_out=dev['dcl_5V'],
            reg_limit=self.limits['Reg5V'],
            max_load=2.0,
            peak_load=2.5)
        dev['dcl_5V'].output(0)

    @share.teststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes['dmm_12V'],
            dcl_out=dev['dcl_12V'],
            reg_limit=self.limits['Reg12V'],
            max_load=self.cfg.ratings.v12.full,
            peak_load=self.cfg.ratings.v12.peak)
        self.ocp_set(
            target=self.cfg.ratings.v12.ocp,
            load=dev['dcl_12V'],
            dmm=mes['dmm_12V'],
            detect=mes['dmm_12V_inOCP'],
            enable=mes['ocp12_unlock'],
            olimit=self.limits['12V_ocp'])
        with tester.PathName('OCPcheck'):
            dev['dcl_12V'].binary(0.0, self.cfg.ratings.v12.ocp * 0.9, 2.0)
            mes['rampOcp12V']()
            dev['dcl_12V'].output(1.0)
            dev['dcl_12V'].output(0.0)

    @share.teststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes['dmm_24V'],
            dcl_out=dev['dcl_24V'],
            reg_limit=self.limits['Reg24V'],
            max_load=self.cfg.ratings.v24.full,
            peak_load=self.cfg.ratings.v24.peak)
        with tester.PathName('OCPcheck'):
            dev['dcl_24V'].binary(0.0, self.cfg.ratings.v24.ocp * 0.9, 2.0)
            mes['rampOcp24V']()
            dev['dcl_24V'].output(1.0)
            dev['dcl_24V'].output(0.0)

    @share.teststep
    def _step_peak_power(self, dev, mes):
        """Check operation at Peak load.

        Unit is left running at no load.

        """
        dev['dcl_5V'].binary(start=0.0, end=2.5, step=1.0)
        dev['dcl_12V'].binary(
            start=0.0, end=self.cfg.ratings.v12.peak, step=2.0)
        dev['dcl_24V'].binary(
            start=0.0, end=self.cfg.ratings.v24.peak, step=2.0)
        self.measure(
            ('dmm_5V', 'dmm_12V', 'dmm_24V', 'dmm_PGOOD', ), timeout=2)
        dev['dcl_24V'].output(0)
        dev['dcl_12V'].output(0)
        dev['dcl_5V'].output(0)

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
            load.output(0.0)
            self.measurements['ocp_lock']()
            olimit.check(setting)

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
            reg_limit.check(load_reg)
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()


class Devices(share.Devices):

    """Devices."""

    fixture = '033484'
    uut = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_PriCtl', tester.DCSource, 'DCS1'),
                ('dcs_5V', tester.DCSource, 'DCS2'),
                ('dcs_Arduino', tester.DCSource, 'DCS3'),
                ('dcs_Vcom', tester.DCSource, 'DCS4'),
                ('dcl_12V', tester.DCLoad, 'DCL1'),
                ('dcl_5V', tester.DCLoad, 'DCL2'),
                ('dcl_24V', tester.DCLoad, 'DCL3'),
                ('rla_pson', tester.Relay, 'RLA1'),
                ('rla_sw', tester.Relay, 'RLA2'),
                ('JLink', tester.JLink, 'JLINK'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Switch on power to fixture circuits
        for dcs in ('dcs_Arduino', 'dcs_Vcom'):
            self[dcs].output(12.0, output=True)
            self.add_closer(lambda: self[dcs].output(0.0, output=False))
        time.sleep(5)   # Allow OS to detect the new ports
        # Serial connection to the ARM console
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = share.config.Fixture.port(self.fixture, 'ARM')
        self['arm'] = console.Console(arm_ser)
        self['arm'].uut = self.uut
        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port(self.fixture, 'ARDUINO')
        self['ard'] = arduino.Arduino(ard_ser)
        # On xubuntu, a device detector opens the serial port for a while
        # after it is attached. Wait for the process to release the port.
        for _ in range(10):
            try:
                self['ard'].open()
                self.add_closer(self['ard'].close)
                break
            except Exception:
                time.sleep(1)
        self['arm'].open()
        self.add_closer(self['arm'].close)

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_5V'].output(1.0)
        self['dcl_12V'].output(5.0)
        self['dcl_24V'].output(5.0, delay=1)
        self['discharge'].pulse()
        for ld in ('dcl_5V', 'dcl_12V', 'dcl_24V'):
            self[ld].output(0.0)
        for dcs in ('dcs_PriCtl', 'dcs_5V'):
            self[dcs].output(0.0, False)
        for rla in ('rla_pson', 'rla_sw'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    ratings = None          # Output load ratings
    projectfile = None
    sw_image = None

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['ACin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['PFC'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
        self['o12V'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self['o24V'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o5Vsb'] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self['PGOOD'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.01)
        self['ACFAIL'] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self['PriCtl'] = sensor.Vdc(dmm, high=8, low=2, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self['o12VinOCP'] = sensor.Vdc(dmm, high=10, low=2, rng=100, res=0.1)
        self['o24VinOCP'] = sensor.Vdc(dmm, high=11, low=2, rng=100, res=0.1)
        self['Lock'] = sensor.Res(dmm, high=12, low=4, rng=1000, res=1)
        self['o5Vsbunsw'] = sensor.Vdc(dmm, high=13, low=3, rng=10, res=0.001)
        self['o8V5Ard'] = sensor.Vdc(dmm, high=14, low=8, rng=100, res=0.001)
        self['OCP12V'] = sensor.Ramp(
            stimulus=self.devices['dcl_12V'],
            sensor=self['o12VinOCP'],
            detect_limit=self.limits['12V_inOCP'],
            ramp_range=sensor.RampRange(
                start=self.ratings.v12.ocp * 0.9,
                stop=self.ratings.v12.ocp * 1.1,
                step=0.1),
            delay=0)
        self['OCP24V'] = sensor.Ramp(
            stimulus=self.devices['dcl_24V'],
            sensor=self['o24VinOCP'],
            detect_limit=self.limits['24V_inOCP'],
            ramp_range=sensor.RampRange(            # Spec: 12.1A to 16.2A
                start=self.ratings.v24.ocp - 0.5,   # 14.15-0.5 = 13.65
                stop=self.ratings.v24.ocp + 2.3,    # 14.15+2.3 = 16.45
                step=0.1),
            delay=0)
        # Arduino sensors
        ard = self.devices['ard']
        for name, cmdkey in (
                ('ocpMax', 'OCP_MAX'),
                ('ocp12Unlock', '12_OCP_UNLOCK'),
                ('ocpStepDn', 'OCP_STEP_DN'),
                ('ocpLock', 'OCP_LOCK'),
                ('pfcDnUnlock', 'PFC_DN_UNLOCK'),
                ('pfcUpUnlock', 'PFC_UP_UNLOCK'),
                ('pfcStepDn', 'PFC_STEP_DN'),
                ('pfcStepUp', 'PFC_STEP_UP'),
                ('pfcDnLock', 'PFC_DN_LOCK'),
                ('pfcUpLock', 'PFC_UP_LOCK'),
            ):
            self[name] = sensor.KeyedReadingString(ard, cmdkey)
        # ARM sensors
        arm = self.devices['arm']
        for name, cmdkey in (
                ('ARM_AcFreq', 'ARM-AcFreq'),
                ('ARM_AcVolt', 'ARM-AcVolt'),
                ('ARM_12V', 'ARM-12V'),
                ('ARM_24V', 'ARM-24V'),
            ):
            self[name] = sensor.KeyedReading(arm, cmdkey)
        for name, cmdkey in (
                ('ARM_SwVer', 'ARM_SwVer'),
                ('ARM_SwBld', 'ARM_SwBld'),
            ):
            self[name] = sensor.KeyedReadingString(arm, cmdkey)
        self['JLink'] = sensor.JLink(
            self.devices['JLink'],
            pathlib.Path(__file__).parent / self.projectfile,
            pathlib.Path(__file__).parent / self.sw_image)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_5Vext', '5Vext', 'o5Vsb', ''),
            ('dmm_5Vunsw', '5Vunsw', 'o5Vsbunsw', ''),
            ('dmm_5Vnl', '5Vnl', 'o5Vsb', ''),
            ('dmm_5V', '5Vfl', 'o5Vsb', ''),
            ('dmm_12V_set', '12Vnl', 'o12V', ''),
            ('dmm_12V', '12Vfl', 'o12V', ''),
            ('dmm_12Voff', '12Voff', 'o12V', ''),
            ('dmm_12V_inOCP', '12V_inOCP', 'o12VinOCP', ''),
            ('dmm_24V', '24Vfl', 'o24V', ''),
            ('dmm_24V_set', '24Vnl', 'o24V', ''),
            ('dmm_24Voff', '24Voff', 'o24V', ''),
            ('dmm_PriCtl', 'PriCtl', 'PriCtl', ''),
            ('dmm_PFCpre', 'PFCpre', 'PFC', ''),
            ('dmm_PFCpost', 'PFCpost', 'PFC', ''),
            ('dmm_ACin', 'ACin', 'ACin', ''),
            ('dmm_PGOOD', 'PGOOD', 'PGOOD', ''),
            ('dmm_ACFAIL', 'ACFAIL', 'ACFAIL', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_Lock', 'FixtureLock', 'Lock', ''),
            ('rampOcp12V', '12V_OCPchk', 'OCP12V', ''),
            ('rampOcp24V', '24V_OCPchk', 'OCP24V', ''),
            ('dmm_8V5Ard', '8.5V Arduino', 'o8V5Ard', ''),
            ('ocp_max', 'Reply', 'ocpMax', ''),
            ('ocp12_unlock', 'Reply', 'ocp12Unlock', ''),
            ('ocp_step_dn', 'Reply', 'ocpStepDn', ''),
            ('ocp_lock', 'Reply', 'ocpLock', ''),
            ('pfcDnUnlock', 'Reply', 'pfcDnUnlock', ''),
            ('pfcUpUnlock', 'Reply', 'pfcUpUnlock', ''),
            ('pfcStepDn', 'Reply', 'pfcStepDn', ''),
            ('pfcStepUp', 'Reply', 'pfcStepUp', ''),
            ('pfcDnLock', 'Reply', 'pfcDnLock', ''),
            ('pfcUpLock', 'Reply', 'pfcUpLock', ''),
            ('arm_AcFreq', 'ARM-AcFreq', 'ARM_AcFreq', ''),
            ('arm_AcVolt', 'ARM-AcVolt', 'ARM_AcVolt', ''),
            ('arm_12V', 'ARM-12V', 'ARM_12V', ''),
            ('arm_24V', 'ARM-24V', 'ARM_24V', ''),
            ('JLink', 'ProgramOk', 'JLink', 'Programmed'),
            ))
        # Suppress signals on these measurements.
        for name in (
                'dmm_12V_inOCP',
                'ocp_max', 'ocp12_unlock',
                'ocp_step_dn', 'ocp_lock',
                'pfcDnUnlock', 'pfcUpUnlock',
                'pfcStepDn', 'pfcStepUp',
                'pfcDnLock', 'pfcUpLock',
                ):
            self[name].send_signal = False
        # Suppress position failure on these measurements.
        for name in (
                'dmm_12V_inOCP',
                ):
            self[name].position_fail = False
            self[name].autoconfig = False
