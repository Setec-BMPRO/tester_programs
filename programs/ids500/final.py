#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""IDS-500 Final Test Program."""

import time
import serial

import tester

import share
from . import console


class Final(share.TestSequence):

    """IDS-500 Final Test Programes."""

    # LDD limit values
    _ldd_6_error_limits = 0.07
    _ldd_50_error_limits = 0.7
    # Test limits
    limitdata = (
        tester.LimitLow('TecOff', 1.5),
        tester.LimitLow('TecVmonOff', 1.5),
        tester.LimitLow('LddOff', 1.5),
        tester.LimitLow('IsVmonOff', 0.5),
        tester.LimitLow('15VOff', 1.5),
        tester.LimitHigh('-15VOff', -1.5),
        tester.LimitLow('15VpOff', 1.5),
        tester.LimitLow('15VpSwOff', 1.5),
        tester.LimitLow('5VOff', 1.5),
        tester.LimitDelta('15V', 15.00, 0.75),
        tester.LimitDelta('-15V', -15.00, 0.75),
        tester.LimitDelta('15Vp', 15.00, 0.75),
        tester.LimitDelta('15VpSw', 15.00, 0.75),
        tester.LimitDelta('5V', 4.95, 0.15),
        tester.LimitDelta('Tec', 15.00, 0.30),
        tester.LimitDelta('TecPhase', -15.00, 0.30),
        tester.LimitBetween('TecVset', 4.95, 5.05),
        tester.LimitLow('TecVmon0V', 0.5),
        tester.LimitDelta('TecVmon', 5.00, 0.10),
        tester.LimitDelta('TecErr', 0.000, 0.275),
        tester.LimitDelta('TecVmonErr', 0.000, 0.030),
        tester.LimitBetween('Ldd', -0.4, 2.5),
        tester.LimitBetween('IsVmon', -0.4, 2.5),
        tester.LimitDelta('IsOut0V', 0.000, 0.001),
        tester.LimitDelta('IsOut06V', 0.006, 0.001),
        tester.LimitDelta('IsOut5V', 0.050, 0.002),
        tester.LimitDelta('IsIout0V', 0.00, 0.05),
        tester.LimitDelta('IsIout06V', 0.60, 0.02),
        tester.LimitDelta('IsIout5V', 5.00, 0.10),
        tester.LimitDelta('IsSet06V', 0.60, 0.05),
        tester.LimitDelta('IsSet5V', 5.00, 0.05),
        # these 3 are patched and then restored during the LDD accuracy test
        tester.LimitDelta('SetMonErr', 0, _ldd_6_error_limits),
        tester.LimitDelta('SetOutErr', 0, _ldd_6_error_limits),
        tester.LimitDelta('MonOutErr', 0, _ldd_6_error_limits),
        tester.LimitRegExp('HwRev', r'^[0-9]{2}[A-D]$'),
        )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwr_up),
            tester.TestStep('KeySw1', self._step_key_sw1),
            tester.TestStep('KeySw12', self._step_key_sw12),
            tester.TestStep('TEC', self._step_tec),
            tester.TestStep('LDD', self._step_ldd),
            tester.TestStep('Comms', self._step_comms),
            tester.TestStep('EmergStop', self._step_emg_stop),
            )

    @share.teststep
    def _step_pwr_up(self, dev, mes):
        """Power Up the unit. Outputs should be off."""
        self.dcload(
            (('dcl_tec', 0.0), ('dcl_15vp', 1.0), ('dcl_15vpsw', 0.0),
             ('dcl_5v', 5.0)),
             output=True)
        dev['acsource'].output(240.0, output=True, delay=2)
        self.measure(
            ('dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff', 'dmm_isvmonoff',
             'dmm_15voff', 'dmm__15voff', 'dmm_15vpoff', 'dmm_15vpswoff',
             'dmm_5voff', ),
            timeout=5)

    @share.teststep
    def _step_key_sw1(self, dev, mes):
        """KeySwitch 1. Outputs must switch on."""
        dev['rla_mainsenable'].set_on()
        self.measure(
            ('dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff', 'dmm_isvmonoff',
             'dmm_15v', 'dmm__15v', 'dmm_15vp', 'dmm_15vpswoff', 'dmm_5v', ),
            timeout=5)

    @share.teststep
    def _step_key_sw12(self, dev, mes):
        """KeySwitch 1 & 2. 15Vp must also switch on."""
        dev['rla_15vpenable'].set_on()
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
        dev['dcl_tec'].output(0.3)
        dev['dcs_tecvset'].output(5.0, delay=0.1)
        Vset, Vmon, Vtec = self.measure(
            ('dmm_tecvset', 'dmm_tecvmon', 'dmm_tec', ),
            timeout=5).readings
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        mes['tecerr'].sensor.store(Vtec - (Vset * 3))
        mes['tecerr']()
        mes['tecvmonerr'].sensor.store(Vmon - (Vtec / 3))
        mes['tecvmonerr']()
        self.measure(('ui_YesNoPsu', 'ui_YesNoTecGreen'))
        dev['rla_tecphase'].set_on()
        self.measure(('dmm_tecphase', 'ui_YesNoTecRed', ))
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
                ('dmm_isvmon', 'dmm_isout0v', 'dmm_isiout0v', ), timeout=5)
        with tester.PathName('6A'):
            dev['dcs_isset'].output(0.6, delay=1)
            mes['dmm_isvmon'](timeout=5)
            Iset, Iout, Imon = self.measure(
                ('dmm_isset06v', 'dmm_isout06v', 'dmm_isiout06v', ),
                timeout=5).readings
            self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
            self._ldd_err(mes, Iset, Iout, Imon)
            mes['ui_YesNoLddGreen']()
        with tester.PathName('50A'):
            dev['dcs_isset'].output(5.0, delay=1)
            mes['dmm_isvmon'](timeout=5)
            Iset, Iout, Imon = self.measure(
                ('dmm_isset5v', 'dmm_isout5v', 'dmm_isiout5v', ),
                timeout=5).readings
            self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
            try:
                # Set limits for 50A checks
                patch_limits = ('SetMonErr', 'SetOutErr', 'MonOutErr', )
                for name in patch_limits:
                    self.limits[name].adjust(0, self._ldd_50_error_limits)
                self._ldd_err(mes, Iset, Iout, Imon)
            finally:    # Restore the limits for 6A checks
                for name in patch_limits:
                    self.limits[name].adjust(0, self._ldd_6_error_limits)
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
    def _step_comms(self, dev, mes):
        """Write HW version and serial number. Read back values."""
        pic = dev['pic']
        pic.open()
        pic.clear_port()
        pic.sw_test_mode()
        hwrev = mes['ui_hwrev']().reading1
        pic.expected = 3
        pic['WriteHwRev'] = hwrev
        # Only the very 1st time a HwRev is written, the unit outputs 4 lines
        # Here we flush the 1 extra line...
        time.sleep(0.5)
        pic.port.flushInput()
        pic.expected = 1
        mes['pic_hwrev'].testlimit[0].adjust(
            r'^I,  2, {0},Hardware Revision$'.format(hwrev)
            )
        mes['pic_hwrev']()
        sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        pic.expected = 3
        pic['WriteSerNum'] = sernum
        pic.expected = 1
        mes['pic_sernum'].testlimit[0].adjust(
            r'^I,  3, {0},Serial Number$'.format(sernum)
            )
        mes['pic_sernum']()

    @share.teststep
    def _step_emg_stop(self, dev, mes):
        """Emergency stop. All outputs must switch off."""
        self.dcload(
            (('dcl_tec', 0.0), ('dcl_15vp', 1.0), ('dcl_15vpsw', 0.0),
             ('dcl_5v', 5.0), ))
        dev['rla_emergency'].set_on(delay=1)
        self.measure(
            ('dmm_tecoff', 'dmm_tecvmonoff', 'dmm_lddoff', 'dmm_isvmonoff',
             'dmm_15voff', 'dmm__15voff', 'dmm_15vpoff', 'dmm_15vpswoff',
             'dmm_5voff', ),
             timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_isset', tester.DCSource, 'DCS2'),
                ('dcs_5v', tester.DCSource, 'DCS3'),
                ('dcs_tecvset', tester.DCSource, 'DCS4'),
                ('dcl_tec', tester.DCLoad, 'DCL2'),
                ('dcl_15vp', tester.DCLoad, 'DCL3'),
                ('dcl_15vpsw', tester.DCLoad, 'DCL4'),
                ('dcl_5v', tester.DCLoad, 'DCL5'),
                ('rla_mainsenable', tester.Relay, 'RLA1'),
                ('rla_15vpenable', tester.Relay, 'RLA2'),
                ('rla_emergency', tester.Relay, 'RLA3'),
                ('rla_crowbar', tester.Relay, 'RLA4'),
                ('rla_enableis', tester.Relay, 'RLA5'),
                ('rla_interlock', tester.Relay, 'RLA6'),
                ('rla_enable', tester.Relay, 'RLA7'),
                ('rla_tecphase', tester.Relay, 'RLA8'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console to communicate with the PIC
        pic_ser = serial.Serial(baudrate=19200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = share.config.Fixture.port('017048', 'PIC')
        self['pic'] = console.Console(pic_ser)

    def reset(self):
        """Reset instruments."""
        self['pic'].close()
        self['acsource'].reset()
        for dev in (
                'dcs_tecvset', 'dcs_isset', 'dcs_5v',
                'dcl_tec', 'dcl_15vp', 'dcl_15vpsw', 'dcl_5v', ):
            self[dev].output(0.0, False)
        for rla in (
                'rla_mainsenable', 'rla_15vpenable', 'rla_emergency',
                'rla_crowbar', 'rla_enableis', 'rla_interlock',
                'rla_enable', 'rla_tecphase', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        pic = self.devices['pic']
        sensor = tester.sensor
        self['oMirTecErr'] = sensor.MirrorReading()
        self['oMirTecVmonErr'] = sensor.MirrorReading()
        self['oMirIsErr'] = sensor.MirrorReading()
        self['tec'] = sensor.Vdc(dmm, high=1, low=3, rng=100, res=0.001)
        self['tecvset'] = sensor.Vdc(dmm, high=3, low=6, rng=10, res=0.001)
        self['tecvmon'] = sensor.Vdc(dmm, high=4, low=6, rng=10, res=0.001)
        self['ldd'] = sensor.Vdc(dmm, high=2, low=4, rng=10, res=0.001)
        self['isset'] = sensor.Vdc(dmm, high=5, low=6, rng=10, res=0.0001)
        self['isout'] = sensor.Vdc(dmm, high=14, low=5, rng=10, res=0.00001)
        self['isiout'] = sensor.Vdc(dmm, high=6, low=6, rng=10, res=0.0001)
        self['isvmon'] = sensor.Vdc(dmm, high=7, low=6, rng=10, res=0.001)
        self['o15v'] = sensor.Vdc(dmm, high=8, low=1, rng=100, res=0.001)
        self['o_15v'] = sensor.Vdc(dmm, high=9, low=1, rng=100, res=0.001)
        self['o15vp'] = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self['o15vpsw'] = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self['o5v'] = sensor.Vdc(dmm, high=12, low=1, rng=10, res=0.001)
        self['pwrok'] = sensor.Vdc(dmm, high=13, low=2, rng=10, res=0.001)
        self['oYesNoPsu'] = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsPSULedGreen?'),
            caption=tester.translate('ids500_final', 'capPsuLed'))
        self['oYesNoTecGreen'] = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsTECLedGreen?'),
            caption=tester.translate('ids500_final', 'capTecGreenLed'))
        self['oYesNoTecRed'] = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsTECLedRed?'),
            caption=tester.translate('ids500_final', 'capTecRedLed'))
        self['oYesNoLddGreen'] = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsLDDLedGreen?'),
            caption=tester.translate('ids500_final', 'capLddGreenLed'))
        self['oYesNoLddRed'] = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsLDDLedRed?'),
            caption=tester.translate('ids500_final', 'capLddRedLed'))
        self['oSerNumEntry'] = sensor.DataEntry(
            message=tester.translate('ids500_final', 'msgSerEntry'),
            caption=tester.translate('ids500_final', 'capSerEntry'))
        self['oHwRevEntry'] = sensor.DataEntry(
            message=tester.translate('ids500_final', 'msgHwRev'),
            caption=tester.translate('ids500_final', 'capHwRev'))
        self['oHwRevEntry'].on_read = lambda value: value.upper().strip()
        self['hwrev'] = sensor.KeyedReadingString(pic, 'PIC-HwRev')
        self['sernum'] = sensor.KeyedReadingString(pic, 'PIC-SerNum')


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
            ('dmm_tecoff', 'TecOff', 'tec', ''),
            ('dmm_tec', 'Tec', 'tec', ''),
            ('dmm_tecphase', 'TecPhase', 'tec', ''),
            ('dmm_tecvset', 'TecVset', 'tecvset', ''),
            ('dmm_tecvmonoff', 'TecVmonOff', 'tecvmon', ''),
            ('dmm_tecvmon0v', 'TecVmon0V', 'tecvmon', ''),
            ('dmm_tecvmon', 'TecVmon', 'tecvmon', ''),
            ('dmm_lddoff', 'LddOff', 'ldd', ''),
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
            ('ui_YesNoPsu', 'Notify', 'oYesNoPsu', ''),
            ('ui_YesNoTecGreen', 'Notify', 'oYesNoTecGreen', ''),
            ('ui_YesNoTecRed', 'Notify', 'oYesNoTecRed', ''),
            ('ui_YesNoLddGreen', 'Notify', 'oYesNoLddGreen', ''),
            ('ui_YesNoLddRed', 'Notify', 'oYesNoLddRed', ''),
            ('ui_sernum', 'SerNum', 'oSerNumEntry', ''),
            ('ui_hwrev', 'HwRev', 'oHwRevEntry', ''),
            ))
        # Create limits locally for these dynamic measurements.
        self['pic_hwrev'] = tester.Measurement(
            tester.LimitRegExp('HwRev-PIC', ''), self.sensors['hwrev'])
        self['pic_sernum'] = tester.Measurement(
            tester.LimitRegExp('SerNum-PIC', ''), self.sensors['sernum'])
