#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 SynBuck Initial Test Program."""

import os
import inspect
import tester
from tester import TestStep, LimitLow, LimitBetween
import share


class InitialSyn(share.TestSequence):

    """IDS-500 Initial SynBuck Test Program."""

    # Firmware image
    pic_hex_syn = 'ids_picSyn_2.hex'
    # Test limits
    limitdata = (
        LimitBetween('20VT', 18.5, 22.0),
        LimitBetween('-20V', -22.0, -18.0),
        LimitBetween('9V', 8.0, 11.5),
        LimitBetween('TecOff', -0.5, 0.5),
        LimitBetween('Tec0V', -0.5, 1.0),
        LimitBetween('Tec2V5', 7.3, 7.8),
        LimitBetween('Tec5V', 14.75, 15.5),
        LimitBetween('Tec5V_Rev', -15.5, -14.5),
        LimitBetween('LddOff', -0.5, 0.5),
        LimitBetween('Ldd0V', -0.5, 0.5),
        LimitBetween('Ldd0V6', 0.6, 1.8),
        LimitBetween('Ldd5V', 1.0, 2.5),
        LimitBetween('LddVmonOff', -0.5, 0.5),
        LimitBetween('LddImonOff', -0.5, 0.5),
        LimitBetween('LddImon0V', -0.05, 0.05),
        LimitBetween('LddImon0V6', 0.55, 0.65),
        LimitBetween('LddImon5V', 4.9, 5.1),
        LimitBetween('ISIout0A', -1.0, 1.0),
        LimitBetween('ISIout6A', 5.0, 7.0),
        LimitBetween('ISIout50A', 49.0, 51.0),
        LimitBetween('ISIset5V', 4.95, 5.05),
        LimitBetween('AdjLimits', 49.9, 50.1),
        LimitBetween('TecVmonOff', -0.5, 0.5),
        LimitBetween('TecVmon0V', -0.5, 0.8),
        LimitBetween('TecVmon2V5', 2.4375, 2.5625),
        LimitBetween('TecVmon5V', 4.925, 5.075),
        LimitBetween('TecVsetOff', -0.5, 0.5),
        LimitLow('FixtureLock', 20),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Program', self._step_program),
            TestStep('PowerUp', self._step_pwrup),
            TestStep('TecEnable', self._step_tec_enable),
            TestStep('TecReverse', self._step_tec_rev),
            TestStep('LddEnable', self._step_ldd_enable),
            TestStep('ISSetAdj', self._step_ISset_adj),
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
        dev['dcs_lddiset'].output(5.0, True)
        setI = mes['dmm_ISIset5V'](timeout=5).reading1 * 10
        lo_lim = setI - (setI * 0.2/100)
        hi_lim = setI + (setI * 0.2/100)
        self.limits['AdjLimits'].limit = lo_lim, hi_lim
        mes['ui_AdjLdd'].sensor.low = lo_lim
        mes['ui_AdjLdd'].sensor.high = hi_lim
        self.measure(('ui_AdjLdd', 'dmm_ISIoutPost', ), timeout=2)


class Devices(share.Devices):

    """Devices."""

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
        self['program_picSyn'] = share.ProgramPIC(
            InitialSyn.pic_hex_syn, folder, '18F4321', self['rla_syn'])

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
        self['oLddVmon'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self['oLddImon'] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self['oLddShunt'] = sensor.Vdc(
            dmm, high=8, low=4, rng=0.1, res=0.0001, scale=1000, nplc=10)
        self['o20VT'] = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self['o9V'] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.001)
        self['o_20V'] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self['oLddIset'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
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
