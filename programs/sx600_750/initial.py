#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 - 2019 SETEC Pty Ltd
"""SX-600/750 Initial Test Program."""

import inspect
import os
import time

import serial
import tester

import share
from . import arduino, config, console


class Initial(share.TestSequence):

    """SX-600/750 Initial Test Program."""

    def open(self, uut):
        """Prepare for testing."""
        self.cfg = config.Config.get(self.parameter)
        Devices.sw_image = self.cfg.arm_bin
        Sensors.ratings = self.cfg.ratings
        self.limits = self.cfg.limits_initial()
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PartDetect', self._step_part_detect),
            tester.TestStep('Program', self._step_program_micros),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('5Vsb', self._step_reg_5v),
            tester.TestStep('12V', self._step_reg_12v),
            tester.TestStep('24V', self._step_reg_24v),
            tester.TestStep('PeakPower', self._step_peak_power),
            )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Check that Fixture Lock is closed."""
        mes['dmm_Lock'](timeout=2)
        if self.parameter == '750':
            self.measure(
                ('dmm_Part', 'dmm_R601', 'dmm_R602', 'dmm_R609', 'dmm_R608'),
                timeout=2)

    @share.teststep
    def _step_program_micros(self, dev, mes):
        """Program the ARM and PIC devices.

        5Vsb is injected to power the ARM and 5Vsb PIC. PriCtl is injected
        to power the PwrSw PIC and digital pots.
        The ARM is programmed.
        The PIC's are programmed.
        Digital pots are set for maximum OCP.
        Unit is left unpowered.

        """
        # Set BOOT active before power-on so the ARM boot-loader runs
        dev['rla_boot'].set_on()
        # Apply and check injected 5Vsb
        dev['dcs_5V'].output(self.cfg._5vsb_ext, True)
        self.measure(
            ('dmm_5Vext', 'dmm_5Vunsw', 'dmm_3V3', 'dmm_8V5Ard'),
            timeout=5)
        dev['programmer'].program()     # Program the ARM device
        dev['ard'].open()
        dev['rla_boot'].set_off(delay=2) # Wait for Arduino to start
        if self.parameter == '750':
            dev['rla_pic1'].set_on()
            dev['rla_pic1'].opc()
            mes['dmm_5Vunsw'](timeout=2)
            mes['pgm_5vsb']()           # Program the 5V Switch Board
            dev['rla_pic1'].set_off()
        # Switch off 5V rail and discharge the 5V to stop the ARM
        dev['dcs_5V'].output(0)
        self.dcload((('dcl_5V', 0.1), ), output=True, delay=0.5)
        # Apply and check injected 12V PriCtl
        dev['dcs_PriCtl'].output(self.cfg.prictl_ext, True)
        mes['dmm_PriCtl'](timeout=2)
        if self.parameter == '750':
            dev['rla_pic2'].set_on()
            dev['rla_pic2'].opc()
            mes['pgm_pwrsw']()      # Program the Power Switch Board
            dev['rla_pic2'].set_off()
        dev['rla_0Vp'].set_on()     # Disconnect 0Vp from PwrSw PIC relays
        dev['dcs_PriCtl'].output(0.0)
        # This will also enable all loads on an ATE3/4 tester.
        self.dcload(
            (('dcl_5V', 0.0), ('dcl_12V', 0.0), ('dcl_24V', 0.0), ),
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
        dev['dcs_5V'].output(self.cfg._5vsb_ext, True)
        self.measure(('dmm_5Vext', 'dmm_5Vunsw'), timeout=2)
        arm.initialise(self.cfg.fan_threshold)
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
        arm.action(expected=arm.banner_lines)
        self.measure(
            ('dmm_ACin', 'dmm_PriCtl', 'dmm_5Vnl', 'dmm_12Voff',
             'dmm_24Voff', 'dmm_ACFAIL', ), timeout=2)
        arm['UNLOCK'] = True
        if self.parameter == '600':     # Prevent shutdown due to no fan
            arm['FAN_CHECK_DISABLE'] = True
        # Switch all outputs ON
        dev['rla_pson'].set_on()
        self.measure(
            ('dmm_12V_set', 'dmm_24V_set', 'dmm_PGOOD'), timeout=2)
        # ARM data readings
        self.measure(
            ('arm_AcFreq', 'arm_AcVolt', 'arm_12V', 'arm_24V',
             'arm_SwVer', 'arm_SwBld', ))
        mes['ocp_max']()
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        pfc = mes['dmm_PFCpre'].stable(self.cfg.pfc_stable).reading1
        if self.parameter == '750':
            arm.calpfc(pfc)
            with mes['dmm_PFCpost'].position_fail_disabled():
                result = mes['dmm_PFCpost'].stable(self.cfg.pfc_stable).result
            if not result:
                self._logger.info('Retry PFC calibration')
                pfc = mes['dmm_PFCpre'].stable(self.cfg.pfc_stable).reading1
                arm.calpfc(pfc)
                mes['dmm_PFCpost'].stable(self.cfg.pfc_stable)
        else:   # SX-600
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
        if self.parameter == '750':
            self.ocp_set(
                target=self.cfg.ratings.v24.ocp,
                load=dev['dcl_24V'],
                dmm=mes['dmm_24V'],
                detect=mes['dmm_24V_inOCP'],
                enable=mes['ocp24_unlock'],
                olimit=self.limits['24V_ocp'])
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
            self.measurements['ocp_lock']()
            load.output(0.0)
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

    sw_image = None     # ARM software image filename

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
                ('dcs_DigPot', tester.DCSource, 'DCS5'),
                ('dcl_12V', tester.DCLoad, 'DCL1'),
                ('dcl_5V', tester.DCLoad, 'DCL2'),
                ('dcl_24V', tester.DCLoad, 'DCL3'),
                ('rla_pic1', tester.Relay, 'RLA1'),
                ('rla_pic2', tester.Relay, 'RLA2'),
                ('rla_pson', tester.Relay, 'RLA3'),
                ('rla_boot', tester.Relay, 'RLA4'),
                ('rla_0Vp', tester.Relay, 'RLA5'),
                ('rla_sw', tester.Relay, 'RLA6'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial port for the ARM. Used by programmer and ARM comms module.
        arm_port = share.config.Fixture.port('022837', 'ARM')
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, self.sw_image)
        self['programmer'] = share.programmer.ARM(
            arm_port, file, boot_relay=self['rla_boot'])
        # Console & Arduino class selection
        con_class, ard_class = {
            '600': (console.Console600, arduino.Arduino600),
            '750': (console.Console750, arduino.Arduino750),
            }[self.parameter]
        # Serial connection to the ARM console
        arm_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = arm_port
        self['arm'] = con_class(arm_ser)
        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port('022837', 'ARDUINO')
        self['ard'] = ard_class(ard_ser)
        # Switch on power to fixture circuits
        for dcs in ('dcs_Arduino', 'dcs_Vcom', 'dcs_DigPot'):
            self[dcs].output(12.0, output=True)
            self.add_closer(lambda: self[dcs].output(0.0, output=False))
        time.sleep(5)   # Allow OS to detect the new ports

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['ard'].close()
        self['acsource'].reset()
        self['dcl_5V'].output(1.0)
        self['dcl_12V'].output(5.0)
        self['dcl_24V'].output(5.0, delay=1)
        self['discharge'].pulse()
        for ld in ('dcl_5V', 'dcl_12V', 'dcl_24V'):
            self[ld].output(0.0)
        for dcs in ('dcs_PriCtl', 'dcs_5V'):
            self[dcs].output(0.0, False)
        for rla in ('rla_pic1', 'rla_pic2', 'rla_boot',
            'rla_pson', 'rla_0Vp', 'rla_sw'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    ratings = None          # Product specific output load ratings

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
        self['PFC'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
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
            start=self.ratings.v12.ocp * 0.9,
            stop=self.ratings.v12.ocp * 1.1,
            step=0.1, delay=0, reset=True, use_opc=True)
        self['OCP24V'] = sensor.Ramp(
            stimulus=self.devices['dcl_24V'],
            sensor=self['o24VinOCP'],
            detect_limit=(self.limits['24V_inOCP'], ),
            start=self.ratings.v24.ocp * 0.9,
            stop=self.ratings.v24.ocp * 1.1,
            step=0.1, delay=0, reset=True, use_opc=True)
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


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_5Voff', '5Voff', 'o5Vsb', ''),
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
            ('arm_SwVer', 'ARM-SwVer', 'ARM_SwVer', ''),
            ('arm_SwBld', 'ARM-SwBld', 'ARM_SwBld', ''),
            ))
        # Suppress signals on these measurements.
        for name in (
                'dmm_12V_inOCP', 'dmm_24V_inOCP',
                'ocp_max', 'ocp12_unlock', 'ocp24_unlock',
                'ocp_step_dn', 'ocp_lock',
                'pfcDnUnlock', 'pfcUpUnlock',
                'pfcStepDn', 'pfcStepUp',
                'pfcDnLock', 'pfcUpLock',
                ):
            self[name].send_signal = False
        # Suppress position failure on these measurements.
        for name in (
                'dmm_12V_inOCP', 'dmm_24V_inOCP',
                ):
            self[name].position_fail = False
