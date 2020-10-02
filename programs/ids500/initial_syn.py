#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""IDS-500 SynBuck Initial Test Program."""

import inspect
import os

import tester

import share


class InitialSyn(share.TestSequence):

    """IDS-500 Initial SynBuck Test Program."""

    # Firmware image
    pic_hex_syn = 'ids_picSyn_2.hex'
    # Test limits
    limitdata = (
        tester.LimitDelta('20VT', nominal=20.0, delta=(1.5, 2.0)),
        tester.LimitDelta('-20V', nominal=-20.0, delta=2.0),
        tester.LimitDelta('9V', nominal=9.0, delta=(1.0, 2.5)),
        tester.LimitDelta('TecOff', nominal=0, delta=0.5),
        tester.LimitLow('Tec0V', 1.0),
        tester.LimitDelta('Tec2V5', nominal=7.5, delta=0.3),
        tester.LimitDelta('Tec5V', nominal=15.0, delta=0.5),
        tester.LimitDelta('Tec5V_Rev', nominal=-15.0, delta=0.5),
        tester.LimitLow('TecVmonOff', 0.5),
        tester.LimitLow('TecVmon0V', 0.8),
        tester.LimitPercent('TecVmon2V5', nominal=2.5, percent=2.5),
        tester.LimitPercent('TecVmon5V', nominal=5.0, percent=1.5),
        tester.LimitLow('TecVsetOff', 0.5),
        tester.LimitLow('LddOff', 0.5),
        tester.LimitLow('Ldd0V', 0.5),
        tester.LimitBetween('Ldd0V6', 0.6, 1.8, doc='Vout @ 6A'),
        tester.LimitBetween('Ldd5V', 1.0, 2.5, doc='Vout @ 50A'),
        tester.LimitLow('LddVmonOff', 0.5),
        tester.LimitLow('LddImonOff', 0.5),
        tester.LimitLow('LddImon0V', 0.05),
        tester.LimitDelta('LddImon0V6', nominal=0.60, delta=0.05),
        tester.LimitDelta('LddImon5V', nominal=5.0, delta=0.1),
        tester.LimitLow('ISIout0A', 1.0),
        tester.LimitDelta('ISIout6A', nominal=6.0, delta=1.0),
        tester.LimitDelta('ISIout50A', nominal=50.0, delta=1.0),
        tester.LimitDelta('ISIset5V', nominal=5.0, delta=0.05),
        tester.LimitPercent('AdjLimits', nominal=50.0, percent=0.2),
        tester.LimitLow('FixtureLock', 20),
        )

    def open(self, uut):
        """Prepare for testing."""
        Devices.pic_hex_syn = self.pic_hex_syn
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Program', self._step_program),
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('TecEnable', self._step_tec_enable),
            tester.TestStep('TecReverse', self._step_tec_rev),
            tester.TestStep('LddEnable', self._step_ldd_enable),
            tester.TestStep('ISSetAdj', self._step_ISset_adj),
            )

    @share.teststep
    def _step_program(self, dev, mes):
        """Check Fixture Lock, apply Vcc and program the board."""
        mes['dmm_lock'](timeout=5)
        dev['dcs_vsec5Vlddtec'].output(5.0, True)
        dev['program_picSyn'].program()

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power up internal IDS-500 for 20VT,-20V, 9V rails and measure."""
        dev['dcs_fan'].output(12.0, output=True)
        dev['acsource'].output(voltage=240.0, output=True, delay=1.0)
        self.measure(
            ('dmm_20VT', 'dmm__20V', 'dmm_9V', 'dmm_tecOff', 'dmm_lddOff',
             'dmm_lddVmonOff', 'dmm_lddImonOff', 'dmm_tecVmonOff',
             'dmm_tecVsetOff'),
            timeout=2)

    @share.teststep
    def _step_tec_enable(self, dev, mes):
        """Enable TEC, set dc input and measure voltages."""
        dev['rla_tecphase'].set_on(delay=0.5)
        dev['rla_enable'].set_on(delay=0.5)
        dev['rla_enTec'].set_on(delay=0.5)
        dev['dcs_tecvset'].output(0.0, output=True)
        self.measure(('dmm_tecVmon0V', 'dmm_tec0V', ), timeout=2)
        dev['dcs_tecvset'].output(2.5)
        self.measure(('dmm_tecVmon2V5', 'dmm_tec2V5', ), timeout=2)
        dev['dcs_tecvset'].output(5.0)
        self.measure(('dmm_tecVmon5V', 'dmm_tec5V', ), timeout=2)

    @share.teststep
    def _step_tec_rev(self, dev, mes):
        """Reverse TEC and measure voltages."""
        dev['rla_tecphase'].set_off()
        self.measure(('dmm_tecVmon5V', 'dmm_tec5Vrev', ), timeout=2)
        dev['rla_tecphase'].set_on()
        self.measure(('dmm_tecVmon5V', 'dmm_tec5V', ), timeout=2)

    @share.teststep
    def _step_ldd_enable(self, dev, mes):
        """Enable LDD, set dc input and measure voltages."""
        self.relay(
            (('rla_interlock', True), ('rla_enIs', True),
             ('rla_lddcrowbar', True), ('rla_lddtest', True), ))
        dev['dcs_lddiset'].output(0.0, output=True)
        self.measure(
            ('dmm_ldd0V', 'dmm_ISIout0A', 'dmm_lddImon0V', ), timeout=2)
        dev['dcs_lddiset'].output(0.6)
        self.measure(
            ('dmm_ldd0V6', 'dmm_ISIout6A', 'dmm_lddImon0V6', ), timeout=2)
        dev['dcs_lddiset'].output(5.0)
        self.measure(
            ('dmm_ldd5V', 'dmm_ISIout50A', 'dmm_lddImon5V', ), timeout=2)
        dev['dcs_lddiset'].output(0.0)

    @share.teststep
    def _step_ISset_adj(self, dev, mes):
        """ISset adjustment.

         Set LDD current to 50A.
         Calculate adjustment limits from measured current setting.
         Adjust pot R489 for accuracy of LDD output current.
         Measure LDD output current with calculated limits.

         """
        dev['dcs_lddiset'].output(5.0, True, delay=0.5)
        setI = mes['dmm_ISIset5V'](timeout=5).reading1 * 10     # 5V == 50A
        self.limits['AdjLimits'].adjust(nominal=setI)
        lo_lim, hi_lim = self.limits['AdjLimits'].limit
        mes['ui_AdjLdd'].sensor.low = lo_lim
        mes['ui_AdjLdd'].sensor.high = hi_lim
        self.measure(('ui_AdjLdd', 'dmm_ISIoutPost', ), timeout=2)


class Devices(share.Devices):

    """Devices."""

    # Firmware image
    pic_hex_syn = None

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_vsec5Vlddtec', tester.DCSource, 'DCS1'),
                ('dcs_lddiset', tester.DCSource, 'DCS2'),
                ('dcs_tecvset', tester.DCSource, 'DCS3'),
                ('dcs_fan', tester.DCSource, 'DCS5'),
                ('rla_enTec', tester.Relay, 'RLA1'),
                ('rla_enIs', tester.Relay, 'RLA2'),
                ('rla_lddcrowbar', tester.Relay, 'RLA3'),
                ('rla_interlock', tester.Relay, 'RLA4'),
                ('rla_lddtest', tester.Relay, 'RLA5'),
                ('rla_tecphase', tester.Relay, 'RLA6'),
                ('rla_enable', tester.Relay, 'RLA12'),
                ('rla_syn', tester.Relay, 'RLA7'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_picSyn'] = share.programmer.PIC(
            self.pic_hex_syn, folder, '18F4321', self['rla_syn'])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset(delay=2)
        self['discharge'].pulse()
        for dcs in (
                'dcs_vsec5Vlddtec', 'dcs_lddiset', 'dcs_tecvset', 'dcs_fan', ):
            self[dcs].output(0.0, False)
        for rla in (
                'rla_enTec', 'rla_enIs', 'rla_lddcrowbar', 'rla_interlock',
                'rla_lddtest', 'rla_tecphase', 'rla_enable', 'rla_syn', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """ Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['olock'] = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self['oTec'] = sensor.Vdc(dmm, high=15, low=3, rng=100, res=0.001)
        self['oTecVmon'] = sensor.Vdc(dmm, high=24, low=1, rng=10, res=0.001)
        self['oTecVset'] = sensor.Vdc(dmm, high=14, low=1, rng=10, res=0.001)
        self['oLdd'] = sensor.Vdc(dmm, high=21, low=1, rng=10, res=0.001)
        self['oLddVmon'] = sensor.Vdc(dmm, high=5, low=6, rng=10, res=0.001)
        self['oLddImon'] = sensor.Vdc(dmm, high=6, low=6, rng=10, res=0.001)
        self['oLddShunt'] = sensor.Vdc(
            dmm, high=8, low=4, rng=0.1, res=0.0001, scale=1000, nplc=10)
        self['o20VT'] = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self['o9V'] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.001)
        self['o_20V'] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self['oLddIset'] = sensor.Vdc(dmm, high=7, low=6, rng=10, res=0.001)
        lo_lim, hi_lim = self.limits['AdjLimits'].limit
        self['oAdjLdd'] = sensor.AdjustAnalog(
            sensor=self['oLddShunt'],
            low=lo_lim, high=hi_lim,
            message=tester.translate('IDS500 Initial Syn', 'AdjR489'),
            caption=tester.translate('IDS500 Initial Syn', 'capAdjLdd'))


class Measurements(share.Measurements):

    """SynBuck Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'olock', ''),
            ('dmm_20VT', '20VT', 'o20VT', ''),
            ('dmm__20V', '-20V', 'o_20V', ''),
            ('dmm_9V', '9V', 'o9V', ''),
            ('dmm_tecOff', 'TecOff', 'oTec', ''),
            ('dmm_tec0V', 'Tec0V', 'oTec', ''),
            ('dmm_tec2V5', 'Tec2V5', 'oTec', ''),
            ('dmm_tec5V', 'Tec5V', 'oTec', ''),
            ('dmm_tec5Vrev', 'Tec5V_Rev', 'oTec', ''),
            ('dmm_tecVmonOff', 'TecVmonOff', 'oTecVmon', ''),
            ('dmm_tecVmon0V', 'TecVmon0V', 'oTecVmon', ''),
            ('dmm_tecVmon2V5', 'TecVmon2V5', 'oTecVmon', ''),
            ('dmm_tecVmon5V', 'TecVmon5V', 'oTecVmon', ''),
            ('dmm_tecVsetOff', 'TecVsetOff', 'oTecVset', ''),
            ('dmm_lddOff', 'LddOff', 'oLdd', ''),
            ('dmm_ldd0V', 'Ldd0V', 'oLdd', ''),
            ('dmm_ldd0V6', 'Ldd0V6', 'oLdd', ''),
            ('dmm_ldd5V', 'Ldd5V', 'oLdd', ''),
            ('dmm_lddVmonOff', 'LddVmonOff', 'oLddVmon', ''),
            ('dmm_lddImonOff', 'LddImonOff', 'oLddImon', ''),
            ('dmm_lddImon0V', 'LddImon0V', 'oLddImon', ''),
            ('dmm_lddImon0V6', 'LddImon0V6', 'oLddImon', ''),
            ('dmm_lddImon5V', 'LddImon5V', 'oLddImon', ''),
            ('dmm_ISIout0A', 'ISIout0A', 'oLddShunt', ''),
            ('dmm_ISIout6A', 'ISIout6A', 'oLddShunt', ''),
            ('dmm_ISIout50A', 'ISIout50A', 'oLddShunt', ''),
            ('dmm_ISIset5V', 'ISIset5V', 'oLddIset', ''),
            ('ui_AdjLdd', 'Notify', 'oAdjLdd', ''),
            ('dmm_ISIoutPost', 'AdjLimits', 'oLddShunt', ''),
            ))
