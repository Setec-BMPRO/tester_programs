#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import tester
from tester import TestStep, LimitLow, LimitHigh, LimitBetween, LimitDelta
import share


class Initial(share.TestSequence):

    """TRS1 Initial Test Program."""

    # Low battery condition voltage limits
    low_batt_l = 10.85
    low_batt_h = 11.55
    # Test limits
    limitdata = (
        LimitLow('VinOff', 0.5),
        LimitBetween('Vin', 11.0, 12.0),
        LimitLow('5VOff', 0.1),
        LimitDelta('5VOn', 5.0, 0.1),
        LimitLow('BrakeOff', 0.1),
        LimitDelta('BrakeOn', 12.0, 0.1),
        LimitLow('LightOff', 0.3),
        LimitDelta('LightOn', 12.0, 0.3),
        LimitLow('RemoteOff', 0.1),
        LimitDelta('RemoteOn', 12.0, 0.1),
        LimitHigh('RedLedOff', 9.0),
        LimitLow('RedLedOn', 0.1),
        LimitDelta('FreqTP3', 0.56, 0.2),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('BreakAway', self._step_breakaway),
            TestStep('BattLow', self._step_batt_low),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply 12Vdc input and measure voltages."""
        dev['rla_pin'].set_on()
        dev['dcs_Vin'].output(12.0, output=True, delay=0.8)
        self.measure(
            ('dmm_vinoff', 'dmm_5Voff', 'dmm_brakeoff', 'dmm_lightoff'),
            timeout=5)

    @share.teststep
    def _step_breakaway(self, dev, mes):
        """Measure voltages under 'breakaway' condition."""
        dev['rla_pin'].set_off()
        self.measure(
            ('dmm_vin', 'dmm_5Von', 'dmm_brakeon', 'dmm_lighton',
             'dmm_redoff', 'dso_tp3', 'ui_YesNoGreen'),
            timeout=5)

    @share.teststep
    def _step_batt_low(self, dev, mes):
        """Check operation of Red Led under low battery condition."""
        dev['dcs_Vin'].output(self.low_batt_l)
        mes['dmm_redon'](timeout=5)
        dev['dcs_Vin'].output(self.low_batt_h)
        mes['dmm_redoff'](timeout=5)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dso', tester.DSO, 'DSO'),
                ('dcs_Vin', tester.DCSource, 'DCS4'),
                ('rla_pin', tester.Relay, 'RLA5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['dcs_Vin'].output(0.0, False)
        self['rla_pin'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        dso = self.devices['dso']
        sensor = tester.sensor
        self['oVin'] = sensor.Vdc(dmm, high=10, low=4, rng=100, res=0.01)
        self['o5V'] = sensor.Vdc(dmm, high=11, low=4, rng=10, res=0.01)
        self['oBrake'] = sensor.Vdc(dmm, high=12, low=4, rng=100, res=0.01)
        self['oLight'] = sensor.Vdc(dmm, high=13, low=4, rng=100, res=0.01)
        self['oRemote'] = sensor.Vdc(dmm, high=14, low=4, rng=100, res=0.01)
        self['oRed'] = sensor.Vdc(dmm, high=15, low=4, rng=100, res=0.01)
        self['oYesNoGreen'] = sensor.YesNo(
            message=tester.translate('trs1_initial', 'IsGreenLedOn?'),
            caption=tester.translate('trs1_initial', 'capGreenLed'))
        tbase = sensor.Timebase(
            range=3.0, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=1, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = (sensor.Freq(ch=1), )
        chan1 = (
            sensor.Channel(
                ch=1, mux=1, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        self['tp3'] = sensor.DSO(dso, chan1, tbase, trg, rdgs)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vinoff', 'VinOff', 'oVin', ''),
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_5Voff', '5VOff', 'o5V', ''),
            ('dmm_5Von', '5VOn', 'o5V', ''),
            ('dmm_brakeoff', 'BrakeOff', 'oBrake', ''),
            ('dmm_brakeon', 'BrakeOn', 'oBrake', ''),
            ('dmm_lightoff', 'LightOff', 'oLight', ''),
            ('dmm_lighton', 'LightOn', 'oLight', ''),
            ('dmm_remoteoff', 'RemoteOff', 'oRemote', ''),
            ('dmm_remoteon', 'RemoteOn', 'oRemote', ''),
            ('dmm_redoff', 'RedLedOff', 'oRed', ''),
            ('dmm_redon', 'RedLedOn', 'oRed', ''),
            ('ui_YesNoGreen', 'Notify', 'oYesNoGreen', ''),
            ('dso_tp3', 'FreqTP3', 'tp3', ''),
            ))
