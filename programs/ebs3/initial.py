#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EBS3 Initial Test Program."""

# Usage of the Digitize command and post-processing:
#
#    Configure acquisition
#        :ACQ:TYPE PEAK;COMP 100;:WAVEFORM:POIN 1000;
#
#    Digitise ch1 & ch2
#        :DIG CHAN1,CHAN2;
#
#    Read ch1 & ch2 waveforms
#        :WAV:SOUR CHAN1;FORM BYTE;PRE?;DATA?;
#        (Read 17000 bytes)
#        (Process data) => t(0), dt, [data0,data1,...]
#
#    4 point average
#
#    Waveform analysis
#        Voltage transitions => List of UP & DOWN level crosses
#        Current average => Vavg of specified time range
#        Peak average => Vavg of 5 sample at/after the Vpeak

import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitBetween
    )
import share


class Initial(share.TestSequence):

    """EBS3 Initial Test Program."""

    bin_version_1 = '2.0.16258.2002'
    bin_version_2 = '2.0.16258.2002'
    # Injected Vbatt
    vbatt = 12.0
    # Common limits
    _common = (
        LimitLow('FixtureLock', 200),
        LimitBetween('Vin', 23.5, 24.5),
        LimitBetween('Vcc1', 23.5, 24.5),
        LimitDelta('VTube', 1000.0, 5.0),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    limitdata = {
        '6-T2': {
            'BinVersion': bin_version_1,
            'Limits': _common + (
                LimitLow('5Vs', 99.0),
                ),
            },
        '6-T5': {
            'BinVersion': bin_version_2,
            'Limits': _common + (
                LimitDelta('5Vs', 4.95, 0.15),
                ),
            },
        }

    def open(self):
        """Create the test program as a linear sequence."""
        self.config = self.limitdata[self.parameter]
        super().open(
            self.config['Limits'], Devices, Sensors, Measurements)
        self.steps = (
            TestStep('CapCharge', self._step_cap_charge),
            TestStep('GetTube', self._step_get_tube),
            )

    @share.teststep
    def _step_cap_charge(self, dev, mes):
        """Initial charging of C15."""
        mes['dmm_lock'](timeout=5)
        self.relay(
            (('rla_d5', True), ('rla_24vbank1', True), ('rla_24vbank2', True),
             ('rla_24vbank3', True), ('rla_24vbank4', True), ))
        dev['acsource'].output(voltage=240.0, output=True, delay=45.0)
        dev['acsource'].output(voltage=0.0)
        dev['discharge'].pulse(duration=0.5)
        self.relay(
            (('rla_24vbank1', False), ('rla_24vbank2', False),
             ('rla_24vbank3', False), ('rla_24vbank4', False),
             ('rla_d5', False), ))

    @share.teststep
    def _step_get_tube(self, dev, mes):
        """Apply input voltage and measure waveform."""
        self.relay(
            (('rla_24vbank1', True), ('rla_dsobank1', True), ))
        dev['acsource'].output(voltage=240.0, output=True, delay=1.0)
        mes['dso_vtube'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dso', tester.DSO, 'DSO'),
                ('rla_dischge', tester.Relay, 'RLA1'),
                ('rla_24vbank1', tester.Relay, 'RLA4'),
                ('rla_24vbank2', tester.Relay, 'RLA5'),
                ('rla_24vbank3', tester.Relay, 'RLA6'),
                ('rla_24vbank4', tester.Relay, 'RLA7'),
                ('rla_d5', tester.Relay, 'RLA8'),
                ('rla_ebsgpwr', tester.Relay, 'RLA9'),
                ('rla_veoldble', tester.Relay, 'RLA10'),
                ('rla_load1', tester.Relay, 'RLA11'),
                ('rla_load2', tester.Relay, 'RLA13'),
                ('rla_load3', tester.Relay, 'RLA14'),
                ('rla_load4', tester.Relay, 'RLA15'),
                ('rla_load5', tester.Relay, 'RLA16'),
                ('rla_load6', tester.Relay, 'RLA17'),
                ('rla_load7', tester.Relay, 'RLA18'),
                ('rla_load8', tester.Relay, 'RLA12'),
                ('rla_dsobank4', tester.Relay, 'RLA19'),
                ('rla_dsobank3', tester.Relay, 'RLA20'),
                ('rla_dsobank2', tester.Relay, 'RLA21'),
                ('rla_dsobank1', tester.Relay, 'RLA22'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['discharge'].pulse()
        for rla in (
            'rla_dischge', 'rla_24vbank1', 'rla_24vbank2', 'rla_24vbank3',
            'rla_24vbank4', 'rla_d5', 'rla_ebsgpwr', 'rla_veoldble',
            'rla_load1', 'rla_load2', 'rla_load3', 'rla_load4', 'rla_load5',
            'rla_load6', 'rla_load7', 'rla_load8', 'rla_dsobank4',
            'rla_dsobank3', 'rla_dsobank2', 'rla_dsobank1'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        dso = self.devices['dso']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.01)
        self['veol1'] = sensor.Vdc(dmm, high=9, low=1, rng=10, res=0.001)
        self['veol2'] = sensor.Vdc(dmm, high=10, low=1, rng=10, res=0.001)
        self['veol3'] = sensor.Vdc(dmm, high=11, low=1, rng=10, res=0.001)
        self['veol4'] = sensor.Vdc(dmm, high=12, low=1, rng=10, res=0.001)
        self['veol5'] = sensor.Vdc(dmm, high=13, low=1, rng=10, res=0.001)
        self['veol6'] = sensor.Vdc(dmm, high=14, low=1, rng=10, res=0.001)
        self['veol7'] = sensor.Vdc(dmm, high=15, low=1, rng=10, res=0.001)
        self['veol8'] = sensor.Vdc(dmm, high=16, low=1, rng=10, res=0.001)
        self['vcc1'] = sensor.Vdc(dmm, high=17, low=1, rng=100, res=0.01)
        self['vcc2'] = sensor.Vdc(dmm, high=18, low=1, rng=100, res=0.01)
        self['vcc3'] = sensor.Vdc(dmm, high=19, low=1, rng=100, res=0.01)
        self['vcc4'] = sensor.Vdc(dmm, high=20, low=1, rng=100, res=0.01)
        self['vcc5'] = sensor.Vdc(dmm, high=21, low=1, rng=100, res=0.01)
        self['vcc6'] = sensor.Vdc(dmm, high=22, low=1, rng=100, res=0.01)
        self['vcc7'] = sensor.Vdc(dmm, high=23, low=1, rng=100, res=0.01)
        self['vcc8'] = sensor.Vdc(dmm, high=24, low=1, rng=100, res=0.01)
        self['tubei1'] = sensor.Vdc(dmm, high=1, low=2, rng=100, res=0.01)
        self['tubei2'] = sensor.Vdc(dmm, high=2, low=3, rng=100, res=0.01)
        self['dischge'] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.01)
        self['lock'] = sensor.Res(dmm, high=5, low=5, rng=10000, res=1)
        tbase = sensor.Timebase(
            range=8.0, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=1, level=9.0, normal_mode=True, pos_slope=True)
        rdgs = (sensor.Vmax(ch=1), sensor.Vmax(ch=2), )
        chans = (
            sensor.Channel(
                ch=1, mux=1, range=40.0, offset=-8.0,
                dc_coupling=True, att=100, bwlim=True),
            sensor.Channel(
                ch=2, mux=1, range=40.0, offset=8.0,
                dc_coupling=True, att=100, bwlim=True),
                )
        self['vtube'] = sensor.DSO(dso, chans, tbase, trg, rdgs, single=True)
        self['yesnogreen'] = sensor.YesNo(
            message=tester.translate('ebs3_initial', 'IsGreenLedOn?'),
            caption=tester.translate('ebs3_initial', 'capGreenLed'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_vcc1', 'Vcc1', 'vcc1', ''),
            ('dmm_lock', 'FixtureLock', 'lock', ''),
            ('ui_yesnogreen', 'Notify', 'yesnogreen', ''),
            ))
        lim = self.limits
        self['dso_vtube'] = tester.Measurement(
                ((lim['VTube'],) * 2), self.sensors['vtube'], '')
