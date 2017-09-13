#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""IDS-500 Initial Main Test Program."""

import tester
from tester import TestStep, LimitLow, LimitHigh, LimitBetween, LimitDelta
import share


class InitialMain(share.TestSequence):

    """IDS-500 Initial Main Test Program."""

    # LDD limit values
    _ldd_6_error_limits = 0.07
    _ldd_50_error_limits = 0.7
    # Test limits
    limitdata = (
        LimitDelta('PfcOff', 340.0, 10.0),
        LimitBetween('PfcOn', 395.0, 410.0),
        LimitLow('TecOff', 1.5),
        LimitLow('TecVmonOff', 1.5),
        LimitLow('LddOff', 1.5),
        LimitLow('IsVmonOff', 0.5),
        LimitLow('15VOff', 1.5),
        LimitHigh('-15VOff', -1.5),
        LimitLow('15VpOff', 1.5),
        LimitLow('15VpSwOff', 1.5),
        LimitLow('5VOff', 1.5),
        LimitDelta('15V', 15.00, 0.75),
        LimitDelta('-15V', -15.00, 0.75),
        LimitDelta('15Vp', 15.00, 0.75),
        LimitDelta('15VpSw', 15.00, 0.75),
        LimitDelta('5V', 4.95, 0.15),
        LimitDelta('Tec', 15.00, 0.30),
        LimitDelta('TecPhase', -15.00, 0.30),
        LimitBetween('TecVset', 4.95, 5.18),
        LimitLow('TecVmon0V', 0.5),
        LimitDelta('TecVmon', 5.00, 0.10),
        LimitDelta('TecErr', 0.000, 0.275),
        LimitDelta('TecVmonErr', 0.000, 0.030),
        LimitBetween('Ldd', -0.4, 2.5),
        LimitBetween('IsVmon', -0.4, 2.5),
        LimitDelta('IsOut0V', 0.000, 0.001),
        LimitDelta('IsOut06V', 0.006, 0.001),
        LimitDelta('IsOut5V', 0.050, 0.002),
        LimitDelta('IsIout0V', 0.00, 0.05),
        LimitDelta('IsIout06V', 0.60, 0.02),
        LimitDelta('IsIout5V', 5.00, 0.10),
        LimitDelta('IsSet06V', 0.60, 0.05),
        LimitDelta('IsSet5V', 5.00, 0.05),
        # these 3 are patched and then restored during the LDD accuracy test
        LimitDelta('SetMonErr', 0, _ldd_6_error_limits),
        LimitDelta('SetOutErr', 0, _ldd_6_error_limits),
        LimitDelta('MonOutErr', 0, _ldd_6_error_limits),
        LimitBetween('OCP5V', 7.0, 10.0),
        LimitLow('inOCP5V', 4.0),
        LimitBetween('OCP15Vp', 7.0, 10.0),
        LimitLow('inOCP15Vp', 12.0),
        LimitBetween('OCPTec', 20.0, 23.0),
        LimitLow('inOCPTec', 12.0),
        LimitLow('FixtureLock', 20),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_pwr_up),
            TestStep('KeySw1', self._step_key_sw1),
            TestStep('KeySw12', self._step_key_sw12),
            TestStep('TEC', self._step_tec),
            TestStep('LDD', self._step_ldd),
            TestStep('OCP', self._step_ocp),
            TestStep('EmergStop', self._step_emg_stop),
            )

    @share.teststep
    def _step_pwr_up(self, dev, mes):
        """Power Up the unit. Outputs should be off."""
        mes['dmm_lock'](timeout=5)
        self.dcload(
            (('dcl_tec', 0.1), ('dcl_15vp', 1.0), ('dcl_15vpsw', 0.0),
             ('dcl_5v', 5.0)),
             output=True)
        dev['acsource'].output(240.0, output=True, delay=1)
        self.measure(
            ('dmm_PFC_off', 'dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff',
             'dmm_isvmonoff', 'dmm_15voff', 'dmm__15voff', 'dmm_15vpoff',
             'dmm_15vpswoff', 'dmm_5voff', ),
            timeout=5)

    @share.teststep
    def _step_key_sw1(self, dev, mes):
        """KeySwitch 1. Outputs must switch on."""
        dev['rla_keysw1'].set_on()
        self.measure(
            ('dmm_PFC_on', 'dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff',
             'dmm_isvmonoff', 'dmm_15v', 'dmm__15v', 'dmm_15vp',
             'dmm_15vpswoff', 'dmm_5v', ),
            timeout=5)

    @share.teststep
    def _step_key_sw12(self, dev, mes):
        """KeySwitch 1 & 2. 15Vp must also switch on."""
        dev['rla_keysw2'].set_on()
        self.measure(
            ('dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff', 'dmm_isvmonoff',
             'dmm_15v', 'dmm__15v', 'dmm_15vp', 'dmm_15vpsw', 'dmm_5v', ),
            timeout=5)

    @share.teststep
    def _step_tec(self, dev, mes):
        """TEC output accuracy and polarity tests.

           Enable, measure voltages.
           Error calculations of actual & monitor vs set point.
           Check LED status as TEC polarity reverses.

         """
        dev['dcs_5v'].output(5.0, True)
        dev['rla_enable'].set_on()
        dev['dcs_tecvset'].output(0.0, True)
        self.measure(('dmm_tecoff', 'dmm_tecvmon0v'), timeout=5)
        dev['dcs_tecvset'].output(5.0, delay=0.1)
        Vset, Vmon, Vtec = self.measure(
            ('dmm_tecvset', 'dmm_tecvmon', 'dmm_tec', ),
            timeout=5).readings
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        mes['tecerr'].sensor.store(Vtec - (Vset * 3))
        mes['tecerr']()
        mes['tecvmonerr'].sensor.store(Vmon - (Vtec / 3))
        mes['tecvmonerr']()
        self.measure(('ui_YesNoPsu', 'ui_YesNoTecRed'))
        dev['rla_tecphase'].set_on()
        self.measure(('dmm_tecphase', 'ui_YesNoTecGreen', ))
        dev['rla_tecphase'].set_off()

    @share.teststep
    def _step_ldd(self, dev, mes):
        """Laser diode output setting and accuracy tests.

           Enable, measure set vs actual and monitor.
           Error calculations at 0A, 6A & 50A loading.
           Check LED status at 6A (green) and 50A (red).

        """
        dev['dcs_isset'].output(0.0, True)
        for rla in ('rla_crowbar', 'rla_interlock', 'rla_enableis'):
            dev[rla].set_on()
        with tester.PathName('0A'):
            self.measure(
                ('dmm_isvmon', 'dmm_isout0v', 'dmm_isiout0v', 'dmm_isldd', ),
                timeout=5)
        with tester.PathName('6A'):
            dev['dcs_isset'].output(0.6, delay=1)
            mes['dmm_isvmon'](timeout=5)
            Iset, Iout, Imon = self.measure(
                ('dmm_isset06v', 'dmm_isout06v', 'dmm_isiout06v', ),
                timeout=5).readings
            mes['dmm_isldd'](timeout=5)
            self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
            self._ldd_err(mes, Iset, Iout, Imon)
            mes['ui_YesNoLddGreen']()
        with tester.PathName('50A'):
            dev['dcs_isset'].output(5.0, delay=1)
            mes['dmm_isvmon'](timeout=5)
            Iset, Iout, Imon = self.measure(
                ('dmm_isset5v', 'dmm_isout5v', 'dmm_isiout5v', ),
                timeout=5).readings
            mes['dmm_isldd'](timeout=5)
            self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
            try:
                # Patch limits for 50A checks
                patch_limits = ('SetMonErr', 'SetOutErr', 'MonOutErr', )
                for name in patch_limits:
                    self.limits[name].limit = (
                    -self._ldd_50_error_limits, self._ldd_50_error_limits)
                self._ldd_err(mes, Iset, Iout, Imon)
            finally:    # Restore the limits for 6A checks
                for name in patch_limits:
                    self.limits[name].limit = (
                    -self._ldd_6_error_limits, self._ldd_6_error_limits)
            mes['ui_YesNoLddRed']()
        # LDD off
        dev['dcs_isset'].output(0.0, False)
        for rla in ('rla_crowbar', 'rla_interlock', 'rla_enableis'):
            dev[rla].set_off()

    @staticmethod
    def _ldd_err(mes, Iset, Iout, Imon):
        """Accuracy check between set and measured values for LDD.

        @param mes Measurements instance
        @param Iset LDD Set value of control voltage
        @param Iout LDD Output current
        @param Imon LDD Monitor output voltage

        """
        # Compare Set value to Mon
        mes['setmonerr'].sensor.store((Iset * 10) - (Imon * 10))
        mes['setmonerr']()
        # Compare Set value to Out
        mes['setouterr'].sensor.store((Iset * 10) - (Iout * 1000))
        mes['setouterr']()
        # Compare Mon to Out
        mes['monouterr'].sensor.store((Imon * 10) - (Iout * 1000))
        mes['monouterr']()

    @share.teststep
    def _step_ocp(self, dev, mes):
        """OCP of the 5V, 15Vp and TEC outputs."""
        dev['dcl_tec'].output(0.1)
        dev['dcl_15vp'].output(1.0)
        dev['dcl_15vpsw'].output(0.0)
        dev['dcl_5v'].output(5.0)
        self.measure(('dmm_5v', 'ramp_ocp5v', ), timeout=5)
        self._restart()
        self.measure(('dmm_15vp', 'ramp_ocp15vp', ), timeout=5)
        self._restart()
        dev['dcs_tecvset'].output(5.0, output=True, delay=1)
        dev['dcl_tec'].output(0.5, delay=1.0)
        self.measure(('dmm_tec', 'ramp_ocptec', ), timeout=5)
        self._restart()

    @share.teststep
    def _step_emg_stop(self, dev, mes):
        """Emergency stop. All outputs must switch off."""
        self.dcload(
            (('dcl_tec', 0.1), ('dcl_15vp', 1.0), ('dcl_15vpsw', 0.0),
             ('dcl_5v', 5.0), ))
        dev['rla_emergency'].set_on(delay=1)
        self.measure(
            ('dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff', 'dmm_isvmonoff',
             'dmm_15voff', 'dmm__15voff', 'dmm_15vpoff', 'dmm_15vpswoff',
             'dmm_5voff', ),
             timeout=5)

    @share.teststep     # Not a real teststep - used to get dev and mes
    def _restart(self, dev, mes):
        """Restart: By cycling AC off and on."""
        self.dcload(
            (('dcl_tec', 0.1), ('dcl_15vp', 1.0), ('dcl_15vpsw', 0.0),
             ('dcl_5v', 5.0), ))
        dev['dcs_5v'].output(0.0)
        dev['acsource'].output(0.0, delay=4.5)
        dev['acsource'].output(240.0, delay=0.5)
        dev['dcs_5v'].output(5.0)
        mes['dmm_15vp'](timeout=10)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_tecvset', tester.DCSource, 'DCS1'),
                ('dcs_isset', tester.DCSource, 'DCS2'),
                ('dcs_5v', tester.DCSource, 'DCS3'),
                ('dcl_tec', tester.DCLoad, 'DCL1'),
                ('dcl_15vp', tester.DCLoad, 'DCL2'),
                ('dcl_15vpsw', tester.DCLoad, 'DCL5'),
                ('dcl_5v', tester.DCLoad, 'DCL6'),
                ('rla_keysw1', tester.Relay, 'RLA1'),
                ('rla_keysw2', tester.Relay, 'RLA2'),
                ('rla_emergency', tester.Relay, 'RLA3'),
                ('rla_crowbar', tester.Relay, 'RLA4'),
                ('rla_enableis', tester.Relay, 'RLA5'),
                ('rla_interlock', tester.Relay, 'RLA6'),
                ('rla_enable', tester.Relay, 'RLA7'),
                ('rla_tecphase', tester.Relay, 'RLA8'),
                ('rla_ledsel0', tester.Relay, 'RLA9'),
                ('rla_ledsel1', tester.Relay, 'RLA10'),
                ('rla_ledsel2', tester.Relay, 'RLA11'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        self['acsource'].reset()
        self['dcl_tec'].output(0.1)
        self['dcl_15vp'].output(2.0)
        self['dcl_15vpsw'].output(0.0)
        self['dcl_5v'].output(5.0, delay=1)
        self['discharge'].pulse()
        for dev in (
                'dcs_tecvset', 'dcs_isset', 'dcs_5v',
                'dcl_tec', 'dcl_15vp', 'dcl_15vpsw', 'dcl_5v', ):
            self[dev].output(0.0, False)
        for rla in (
                'rla_keysw1', 'rla_keysw2', 'rla_emergency',
                'rla_crowbar', 'rla_enableis', 'rla_interlock',
                'rla_enable', 'rla_tecphase', 'rla_ledsel0',
                'rla_ledsel1', 'rla_ledsel2', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oMirTecErr'] = sensor.Mirror()
        self['oMirTecVmonErr'] = sensor.Mirror()
        self['oMirIsErr'] = sensor.Mirror()
        self['lock'] = sensor.Res(dmm, high=18, low=3, rng=10000, res=1)
        self['tec'] = sensor.Vdc(
            dmm, high=1, low=4, rng=100, res=0.001, scale=-1.0)
        self['ldd'] = sensor.Vdc(dmm, high=2, low=5, rng=100, res=0.001)
        self['tecvset'] = sensor.Vdc(dmm, high=3, low=7, rng=10, res=0.001)
        self['tecvmon'] = sensor.Vdc(dmm, high=4, low=7, rng=10, res=0.001)
        self['isset'] = sensor.Vdc(dmm, high=5, low=7, rng=10, res=0.0001)
        self['isout'] = sensor.Vdc(dmm, high=14, low=6, rng=10, res=0.00001)
        self['isiout'] = sensor.Vdc(dmm, high=6, low=7, rng=10, res=0.0001)
        self['isvmon'] = sensor.Vdc(dmm, high=7, low=7, rng=10, res=0.001)
        self['o15v'] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self['o_15v'] = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.001)
        self['o15vp'] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.001)
        self['o15vpsw'] = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.001)
        self['o5v'] = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001)
        self['pwrok'] = sensor.Vdc(dmm, high=13, low=8, rng=100, res=0.01)
        self['active'] = sensor.Vac(dmm, high=20, low=1, rng=1000, res=0.1)
        self['vbus'] = sensor.Vdc(dmm, high=15, low=2, rng=1000, res=0.1)
        self['red'] = sensor.Vdc(dmm, high=16, low=7, rng=10, res=0.01)
        self['green'] = sensor.Vdc(dmm, high=17, low=7, rng=10, res=0.01)
        self['fan1'] = sensor.Vdc(dmm, high=18, low=7, rng=100, res=0.01)
        self['fan2'] = sensor.Vdc(dmm, high=19, low=7, rng=100, res=0.01)
        self['vsec13v'] = sensor.Vdc(dmm, high=21, low=7, rng=100, res=0.001)
        self['o5vlddtec'] = sensor.Vdc(dmm, high=22, low=7, rng=10, res=0.001)
        self['o5vupaux'] = sensor.Vdc(dmm, high=23, low=7, rng=10, res=0.001)
        self['o5vup'] = sensor.Vdc(dmm, high=24, low=7, rng=10, res=0.001)
        low, high = self.limits['OCP5V'].limit
        self['ocp5v'] = sensor.Ramp(
            stimulus=self.devices['dcl_5v'],
            sensor=self['o5v'],
            detect_limit=(self.limits['inOCP5V'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.2)
        low, high = self.limits['OCP15Vp'].limit
        self['ocp15vp'] = sensor.Ramp(
            stimulus=self.devices['dcl_15vp'],
            sensor=self['o15vp'],
            detect_limit=(self.limits['inOCP15Vp'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.2)
        low, high = self.limits['OCPTec'].limit
        self['ocptec'] = sensor.Ramp(
            stimulus=self.devices['dcl_tec'],
            sensor=self['tec'],
            detect_limit=(self.limits['inOCPTec'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.2)
        self['oYesNoPsu'] = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsPSULedGreen?'),
            caption=tester.translate('ids500_ini_main', 'capPsuLed'))
        self['oYesNoTecGreen'] = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsTECLedGreen?'),
            caption=tester.translate('ids500_ini_main', 'capTecGreenLed'))
        self['oYesNoTecRed'] = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsTECLedRed?'),
            caption=tester.translate('ids500_ini_main', 'capTecRedLed'))
        self['oYesNoLddGreen'] = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsLDDLedGreen?'),
            caption=tester.translate('ids500_ini_main', 'capLddGreenLed'))
        self['oYesNoLddRed'] = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsLDDLedRed?'),
            caption=tester.translate('ids500_ini_main', 'capLddRedLed'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('tecerr', 'TecErr', 'oMirTecErr', ''),
            ('tecvmonerr', 'TecVmonErr', 'oMirTecVmonErr', ''),
            ('setmonerr', 'SetMonErr', 'oMirIsErr', ''),
            ('setouterr', 'SetOutErr', 'oMirIsErr', ''),
            ('monouterr', 'MonOutErr', 'oMirIsErr', ''),
            ('dmm_lock', 'FixtureLock', 'lock', ''),
            ('dmm_PFC_off', 'PfcOff', 'vbus', ''),
            ('dmm_PFC_on', 'PfcOn', 'vbus', ''),
            ('dmm_tecoff', 'TecOff', 'tec', ''),
            ('dmm_tec', 'Tec', 'tec', ''),
            ('dmm_tecphase', 'TecPhase', 'tec', ''),
            ('dmm_tecvset', 'TecVset', 'tecvset', ''),
            ('dmm_tecvmonoff', 'TecVmonOff', 'tecvmon', ''),
            ('dmm_tecvmon0v', 'TecVmon0V', 'tecvmon', ''),
            ('dmm_tecvmon', 'TecVmon', 'tecvmon', ''),
            ('dmm_lddoff', 'LddOff', 'ldd', ''),
            ('dmm_isldd', 'Ldd', 'ldd', ''),
            ('dmm_isvmonoff', 'IsVmonOff', 'isvmon', ''),
            ('dmm_isvmon', 'IsVmon', 'isvmon', ''),
            ('dmm_isout0v', 'IsOut0V', 'isout', ''),
            ('dmm_isout06v', 'IsOut06V', 'isout', ''),
            ('dmm_isout5v', 'IsOut5V', 'isout', ''),
            ('dmm_isiout0v', 'IsIout0V', 'isiout', ''),
            ('dmm_isiout06v', 'IsIout06V', 'isiout', ''),
            ('dmm_isiout5v', 'IsIout5V', 'isiout', ''),
            ('dmm_isset06v', 'IsSet06V', 'isset', ''),
            ('dmm_isset5v', 'IsSet5V', 'isset', ''),
            ('dmm_15voff', '15VOff', 'o15v', ''),
            ('dmm_15v', '15V', 'o15v', ''),
            ('dmm__15voff', '-15VOff', 'o_15v', ''),
            ('dmm__15v', '-15V', 'o_15v', ''),
            ('dmm_15vpoff', '15VpOff', 'o15vp', ''),
            ('dmm_15vp', '15Vp', 'o15vp', ''),
            ('dmm_15vpswoff', '15VpSwOff', 'o15vpsw', ''),
            ('dmm_15vpsw', '15VpSw', 'o15vpsw', ''),
            ('dmm_5voff', '5VOff', 'o5v', ''),
            ('dmm_5v', '5V', 'o5v', ''),
            ('ramp_ocp5v', 'OCP5V', 'ocp5v', ''),
            ('ramp_ocp15vp', 'OCP15Vp', 'ocp15vp', ''),
            ('ramp_ocptec', 'OCPTec', 'ocptec', ''),
            ('ui_YesNoPsu', 'Notify', 'oYesNoPsu', ''),
            ('ui_YesNoTecGreen', 'Notify', 'oYesNoTecGreen', ''),
            ('ui_YesNoTecRed', 'Notify', 'oYesNoTecRed', ''),
            ('ui_YesNoLddGreen', 'Notify', 'oYesNoLddGreen', ''),
            ('ui_YesNoLddRed', 'Notify', 'oYesNoLddRed', ''),
            ))
