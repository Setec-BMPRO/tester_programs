#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""IDS-500 Initial Main Test Program."""

import time
from pydispatch import dispatcher
import tester
from tester.testlimit import lim_lo, lim_hilo, lim_hilo_delta, lim_boolean
from share import oldteststep

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('Vbus', 340.0, 10.0),
    lim_lo('TecOff', 1.5),
    lim_lo('TecVmonOff', 1.5),
    lim_lo('LddOff', 1.5),
    lim_lo('IsVmonOff', 0.5),
    lim_lo('15VOff', 1.5),
    lim_lo('-15VOff', 1.5),
    lim_lo('15VpOff', 1.5),
    lim_lo('15VpSwOff', 1.5),
    lim_lo('5VOff', 1.5),
    lim_hilo('15V', 14.25, 15.75),
    lim_hilo('-15V', -15.75, -14.25),
    lim_hilo('15Vp', 14.25, 15.75),
    lim_hilo('15VpSw', 14.25, 15.75),
    lim_hilo('5V', 4.80, 5.10),
    lim_hilo('Tec', 14.70, 15.30),
    lim_hilo('TecPhase', -15.30, 14.70),
    lim_hilo('TecVset', 4.95, 5.18),
    lim_lo('TecVmon0V', 0.5),
    lim_hilo('TecVmon', 4.90, 5.10),
    lim_hilo('TecErr', -0.275, 0.275),
    lim_hilo('TecVmonErr', -0.030, 0.030),
    lim_hilo('Ldd', -0.4, 2.5),
    lim_hilo('IsVmon', -0.4, 2.5),
    lim_hilo('IsOut0V', -0.001, 0.001),
    lim_hilo('IsOut06V', 0.005, 0.007),
    lim_hilo('IsOut5V', 0.048, 0.052),
    lim_hilo('IsIout0V', -0.05, 0.05),
    lim_hilo('IsIout06V', 0.58, 0.62),
    lim_hilo('IsIout5V', 4.90, 5.10),
    lim_hilo('IsSet06V', 0.55, 0.65),
    lim_hilo('IsSet5V', 4.95, 5.05),
    lim_hilo('SetMonErr', -0.07, 0.07),
    lim_hilo('SetOutErr', -0.07, 0.07),
    lim_hilo('MonOutErr', -0.07, 0.07),
    lim_hilo('OCP5V', 7.0, 10.0),
    lim_lo('inOCP5V', 4.0),
    lim_hilo('OCP15Vp', 7.0, 10.0),
    lim_lo('inOCP15Vp', 12.0),
    lim_hilo('OCPTec', 20.0, 23.0),
    lim_lo('inOCPTec', 12.0),
    lim_lo('FixtureLock', 20),
    lim_boolean('Notify', True),
    ))


class InitialMain(tester.testsequence.TestSequence):

    """IDS-500 Initial Main Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.limits = LIMITS
        self.logdev = LogicalDevices(self.physical_devices)
        self.sensor = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensor, self.limits)
        self.subtest = SubTests(self.logdev, self.meas)
        self.steps = (
            tester.TestStep('PowerUp', self.subtest.pwr_up.run),
            tester.TestStep('KeySw1', self.subtest.key_sw1.run),
            tester.TestStep('KeySw12', self.subtest.key_sw12.run),
            tester.TestStep('TEC', self._step_tec),
            tester.TestStep('LDD', self._step_ldd),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('EmergStop', self.subtest.emg_stop.run),
            )

    def close(self):
        """Finished testing."""
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_tec(self, dev, mes):
        """Check the TEC circuit.

           Enable, measure voltages.
           Error calculations.
           Check LED status.

         """
        sen = self.sensor
        dev.dcs_5v.output(5.0, True)
        dev.rla_enable.set_on()
        dev.dcs_tecvset.output(0.0, True)
        tester.MeasureGroup((mes.dmm_tecoff, mes.dmm_tecvmon0v), timeout=5)
        dev.dcs_tecvset.output(voltage=5.0, delay=0.1)
        Vset, Vmon, Vtec = tester.MeasureGroup(
            (mes.dmm_tecvset, mes.dmm_tecvmon, mes.dmm_tec),
            timeout=5).readings
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        sen.oMirTecErr.store(Vtec - (Vset * 3))
        mes.tecerr.measure(timeout=5)
        sen.oMirTecVmonErr.store(Vmon - (Vtec / 3))
        mes.tecvmonerr.measure(timeout=5)
        tester.MeasureGroup((mes.ui_YesNoPsu, mes.ui_YesNoTecRed), timeout=5)
        dev.rla_tecphase.set_on()
        tester.MeasureGroup(
            (mes.dmm_tecphase, mes.ui_YesNoTecGreen), timeout=5)
        dev.rla_tecphase.set_off()

    @oldteststep
    def _step_ldd(self, dev, mes):
        """Check the Laser diode circuit.

           Enable, measure voltages.
           Error calculations at 0A, 6A & 50A loading.
           Check LED status.

        """
        # Run LDD at 0A
        dev.dcs_isset.output(0.0, True)
        dev.rla_crowbar.set_on()
        dev.rla_interlock.set_on()
        dev.rla_enableis.set_on()
        tester.MeasureGroup(
            (mes.dmm_isvmon, mes.dmm_isout0v, mes.dmm_isiout0v,
            mes.dmm_isldd), timeout=5)
        # Run LDD at 6A
        dev.dcs_isset.output(voltage=0.6, delay=1)
        mes.dmm_isvmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_isset06v, mes.dmm_isout06v, mes.dmm_isiout06v),
            timeout=5).readings
        mes.dmm_isldd.measure(timeout=5)
        with tester.PathName('6A'):
            self._ldd_err(Iset, Iout, Imon)
        # Run LDD at 50A
        mes.ui_YesNoLddGreen.measure(timeout=5)
        dev.dcs_isset.output(voltage=5.0, delay=1)
        mes.dmm_isvmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_isset5v, mes.dmm_isout5v, mes.dmm_isiout5v),
            timeout=5).readings
        mes.dmm_isldd.measure(timeout=5)
        for name in ('SetMonErr', 'SetOutErr', 'MonOutErr'):
            self.limits[name].limit = (-0.7, 0.7)
        with tester.PathName('50A'):
            self._ldd_err(Iset, Iout, Imon)
        # LDD off
        mes.ui_YesNoLddRed.measure(timeout=5)
        dev.dcs_isset.output(0.0, False)
        dev.rla_crowbar.set_off()
        dev.rla_interlock.set_off()
        dev.rla_enableis.set_off()

    def _ldd_err(self, Iset, Iout, Imon):
        """Check the accuracy between set and measured values for LD."""
        mes, sen = self.meas, self.sensor
        self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
        # Compare Set value to Mon
        sen.oMirIsErr.store((Iset * 10) - (Imon * 10))
        mes.setmonerr.measure()
        # Compare Set value to Out
        sen.oMirIsErr.store((Iset * 10) - (Iout * 1000))
        mes.setouterr.measure()
        # Compare Mon to Out
        sen.oMirIsErr.store((Imon * 10) - (Iout * 1000))
        mes.monouterr.measure()

    @oldteststep
    def _step_ocp(self, dev, mes):
        """OCP."""
        tst = self.subtest
        dev.dcl_tec.output(0.1)
        dev.dcl_15vp.output(1.0)
        dev.dcl_15vpsw.output(0.0)
        dev.dcl_5v.output(5.0)
        tester.MeasureGroup((mes.dmm_5v, mes.ramp_ocp5v), timeout=5)
        tst.reset.run()
        tester.MeasureGroup((mes.dmm_15vp, mes.ramp_ocp15vp), timeout=5)
        tst.reset.run()
        dev.dcs_tecvset.output(5.0, True, 1.0)
        dev.dcl_tec.output(current=0.5, delay=1.0)
        tester.MeasureGroup((mes.dmm_tec, mes.ramp_ocptec), timeout=5)
        tst.reset.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_tecvset = tester.DCSource(devices['DCS1'])
        self.dcs_isset = tester.DCSource(devices['DCS2'])
        self.dcs_5v = tester.DCSource(devices['DCS3'])
        self.dcl_tec = tester.DCLoad(devices['DCL1'])
        self.dcl_15vp = tester.DCLoad(devices['DCL2'])
        self.dcl_15vpsw = tester.DCLoad(devices['DCL5'])
        self.dcl_5v = tester.DCLoad(devices['DCL6'])
        self.rla_keysw1 = tester.Relay(devices['RLA1'])
        self.rla_keysw2 = tester.Relay(devices['RLA2'])
        self.rla_emergency = tester.Relay(devices['RLA3'])
        self.rla_crowbar = tester.Relay(devices['RLA4'])
        self.rla_enableis = tester.Relay(devices['RLA5'])
        self.rla_interlock = tester.Relay(devices['RLA6'])
        self.rla_enable = tester.Relay(devices['RLA7'])
        self.rla_tecphase = tester.Relay(devices['RLA8'])
        self.rla_ledsel0 = tester.Relay(devices['RLA9'])
        self.rla_ledsel1 = tester.Relay(devices['RLA10'])
        self.rla_ledsel2 = tester.Relay(devices['RLA11'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_tec.output(0.1)
        self.dcl_15vp.output(2.0)
        self.dcl_15vpsw.output(0.0)
        self.dcl_5v.output(5.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_tecvset, self.dcs_isset, self.dcs_5v):
            dcs.output(0.0, False)
        for ld in (self.dcl_tec, self.dcl_15vp, self.dcl_15vpsw, self.dcl_5v):
            ld.output(0.0, False)
        for rla in (
                self.rla_keysw1, self.rla_keysw2, self.rla_emergency,
                self.rla_crowbar, self.rla_enableis, self.rla_interlock,
                self.rla_enable, self.rla_tecphase, self.rla_ledsel0,
                self.rla_ledsel1, self.rla_ledsel2):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(
            self._reset, sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oMirTecErr = sensor.Mirror()
        self.oMirTecVmonErr = sensor.Mirror()
        self.oMirIsErr = sensor.Mirror()
        self.lock = sensor.Res(dmm, high=18, low=3, rng=10000, res=1)
        self.tec = sensor.Vdc(dmm, high=1, low=4, rng=100, res=0.001, scale=-1)
        self.ldd = sensor.Vdc(dmm, high=2, low=5, rng=100, res=0.001)
        self.tecvset = sensor.Vdc(dmm, high=3, low=7, rng=10, res=0.001)
        self.tecvmon = sensor.Vdc(dmm, high=4, low=7, rng=10, res=0.001)
        self.isset = sensor.Vdc(dmm, high=5, low=7, rng=10, res=0.0001)
        self.isout = sensor.Vdc(dmm, high=14, low=6, rng=10, res=0.00001)
        self.isiout = sensor.Vdc(dmm, high=6, low=7, rng=10, res=0.0001)
        self.isvmon = sensor.Vdc(dmm, high=7, low=7, rng=10, res=0.001)
        self.o15v = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.o_15v = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.001)
        self.o15vp = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.001)
        self.o15vpsw = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.001)
        self.o5v = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001)
        self.pwrok = sensor.Vdc(dmm, high=13, low=8, rng=100, res=0.01)
        self.active = sensor.Vac(dmm, high=20, low=1, rng=1000, res=0.1)
        self.vbus = sensor.Vdc(dmm, high=15, low=2, rng=1000, res=0.1)
        self.red = sensor.Vdc(dmm, high=16, low=7, rng=10, res=0.01)
        self.green = sensor.Vdc(dmm, high=17, low=7, rng=10, res=0.01)
        self.fan1 = sensor.Vdc(dmm, high=18, low=7, rng=100, res=0.01)
        self.fan2 = sensor.Vdc(dmm, high=19, low=7, rng=100, res=0.01)
        self.vsec13v = sensor.Vdc(dmm, high=21, low=7, rng=100, res=0.001)
        self.o5vlddtec = sensor.Vdc(dmm, high=22, low=7, rng=10, res=0.001)
        self.o5vupaux = sensor.Vdc(dmm, high=23, low=7, rng=10, res=0.001)
        self.o5vup = sensor.Vdc(dmm, high=24, low=7, rng=10, res=0.001)
        low, high = limits['OCP5V'].limit
        self.ocp5v = sensor.Ramp(
            stimulus=logical_devices.dcl_5v, sensor=self.o5v,
            detect_limit=(limits['inOCP5V'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.2)
        low, high = limits['OCP15Vp'].limit
        self.ocp15vp = sensor.Ramp(
            stimulus=logical_devices.dcl_15vp, sensor=self.o15vp,
            detect_limit=(limits['inOCP15Vp'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.2)
        low, high = limits['OCPTec'].limit
        self.ocptec = sensor.Ramp(
            stimulus=logical_devices.dcl_tec, sensor=self.tec,
            detect_limit=(limits['inOCPTec'], ),
            start=low - 1, stop=high + 1, step=0.1, delay=0.2)
        self.oYesNoPsu = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsPSULedGreen?'),
            caption=tester.translate('ids500_ini_main', 'capPsuLed'))
        self.oYesNoTecGreen = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsTECLedGreen?'),
            caption=tester.translate('ids500_ini_main', 'capTecGreenLed'))
        self.oYesNoTecRed = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsTECLedRed?'),
            caption=tester.translate('ids500_ini_main', 'capTecRedLed'))
        self.oYesNoLddGreen = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsLDDLedGreen?'),
            caption=tester.translate('ids500_ini_main', 'capLddGreenLed'))
        self.oYesNoLddRed = sensor.YesNo(
            message=tester.translate('ids500_ini_main', 'IsLDDLedRed?'),
            caption=tester.translate('ids500_ini_main', 'capLddRedLed'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirTecErr.flush()
        self.oMirTecVmonErr.flush()
        self.oMirIsErr.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.tecerr = Measurement(limits['TecErr'], sense.oMirTecErr)
        self.tecvmonerr = Measurement(
            limits['TecVmonErr'], sense.oMirTecVmonErr)
        self.setmonerr = Measurement(limits['SetMonErr'], sense.oMirIsErr)
        self.setouterr = Measurement(limits['SetOutErr'], sense.oMirIsErr)
        self.monouterr = Measurement(limits['MonOutErr'], sense.oMirIsErr)
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.lock)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.vbus)
        self.dmm_tecoff = Measurement(limits['TecOff'], sense.tec)
        self.dmm_tec = Measurement(limits['Tec'], sense.tec)
        self.dmm_tecphase = Measurement(limits['TecPhase'], sense.tec)
        self.dmm_tecvset = Measurement(limits['TecVset'], sense.tecvset)
        self.dmm_tecvmonoff = Measurement(limits['TecVmonOff'], sense.tecvmon)
        self.dmm_tecvmon0v = Measurement(limits['TecVmon0V'], sense.tecvmon)
        self.dmm_tecvmon = Measurement(limits['TecVmon'], sense.tecvmon)
        self.dmm_lddoff = Measurement(limits['LddOff'], sense.ldd)
        self.dmm_isldd = Measurement(limits['Ldd'], sense.ldd)
        self.dmm_isvmonoff = Measurement(limits['IsVmonOff'], sense.isvmon)
        self.dmm_isvmon = Measurement(limits['IsVmon'], sense.isvmon)
        self.dmm_isout0v = Measurement(limits['IsOut0V'], sense.isout)
        self.dmm_isout06v = Measurement(limits['IsOut06V'], sense.isout)
        self.dmm_isout5v = Measurement(limits['IsOut5V'], sense.isout)
        self.dmm_isiout0v = Measurement(limits['IsIout0V'], sense.isiout)
        self.dmm_isiout06v = Measurement(limits['IsIout06V'], sense.isiout)
        self.dmm_isiout5v = Measurement(limits['IsIout5V'], sense.isiout)
        self.dmm_isset06v = Measurement(limits['IsSet06V'], sense.isset)
        self.dmm_isset5v = Measurement(limits['IsSet5V'], sense.isset)
        self.dmm_15voff = Measurement(limits['15VOff'], sense.o15v)
        self.dmm_15v = Measurement(limits['15V'], sense.o15v)
        self.dmm__15voff = Measurement(limits['-15VOff'], sense.o_15v)
        self.dmm__15v = Measurement(limits['-15V'], sense.o_15v)
        self.dmm_15vpoff = Measurement(limits['15VpOff'], sense.o15vp)
        self.dmm_15vp = Measurement(limits['15Vp'], sense.o15vp)
        self.dmm_15vpswoff = Measurement(limits['15VpSwOff'], sense.o15vpsw)
        self.dmm_15vpsw = Measurement(limits['15VpSw'], sense.o15vpsw)
        self.dmm_5voff = Measurement(limits['5VOff'], sense.o5v)
        self.dmm_5v = Measurement(limits['5V'], sense.o5v)
        self.ramp_ocp5v = Measurement(limits['OCP5V'], sense.ocp5v)
        self.ramp_ocp15vp = Measurement(limits['OCP15Vp'], sense.ocp15vp)
        self.ramp_ocptec = Measurement(limits['OCPTec'], sense.ocptec)
        self.ui_YesNoPsu = Measurement(limits['Notify'], sense.oYesNoPsu)
        self.ui_YesNoTecGreen = Measurement(
            limits['Notify'], sense.oYesNoTecGreen)
        self.ui_YesNoTecRed = Measurement(
            limits['Notify'], sense.oYesNoTecRed)
        self.ui_YesNoLddGreen = Measurement(
            limits['Notify'], sense.oYesNoLddGreen)
        self.ui_YesNoLddRed = Measurement(
            limits['Notify'], sense.oYesNoLddRed)


class SubTests():

    """SubTest Steps."""

    def __init__(self, dev, mes):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        # PowerUp: Fixture lock, Min load, input AC, measure.
        self.pwr_up = tester.SubStep((
            tester.MeasureSubStep((mes.dmm_lock, ), timeout=5),
            tester.LoadSubStep(
                ((dev.dcl_tec, 0.1), (dev.dcl_15vp, 1.0),
                (dev.dcl_15vpsw, 0.0), (dev.dcl_5v, 5.0)), output=True),
            tester.AcSubStep(
                acs=dev.acsource, voltage=240.0, output=True, delay=1.0),
            tester.MeasureSubStep(
                (mes.dmm_vbus, mes.dmm_tecoff, mes.dmm_tecvmonoff,
                mes.dmm_lddoff, mes.dmm_isvmonoff, mes.dmm_15voff,
                mes.dmm__15voff, mes.dmm_15vpoff, mes.dmm_15vpswoff,
                mes.dmm_5voff), timeout=5),
            ))

        # KeySw1: KeySwitch 1, measure.
        self.key_sw1 = tester.SubStep((
            tester.RelaySubStep(((dev.rla_keysw1, True), )),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                mes.dmm_isvmonoff, mes.dmm_15v, mes.dmm__15v,
                mes.dmm_15vp, mes.dmm_15vpswoff, mes.dmm_5v), timeout=5),
            ))

        # KeySw12: KeySwitch 1 & 2, measure.
        self.key_sw12 = tester.SubStep((
            tester.RelaySubStep(((dev.rla_keysw2, True), )),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                mes.dmm_isvmonoff, mes.dmm_15v, mes.dmm__15v,
                mes.dmm_15vp, mes.dmm_15vpsw, mes.dmm_5v), timeout=5),
            ))

        # Reset: Power off and on.
        self.reset = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_tec, 0.1), (dev.dcl_15vp, 1.0),
                 (dev.dcl_15vpsw, 0.0), (dev.dcl_5v, 5.0), )),
            tester.DcSubStep(setting=((dev.dcs_5v, 0.0), )),
            tester.AcSubStep(acs=dev.acsource, voltage=0.0, delay=4.5),
            tester.AcSubStep(acs=dev.acsource, voltage=240.0, delay=0.5),
            tester.DcSubStep(setting=((dev.dcs_5v, 5.0), )),
            tester.MeasureSubStep((mes.dmm_15vp, ), timeout=10),
            ))

        # EmergStop: Emergency stop, measure.
        self.emg_stop = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_tec, 0.1), (dev.dcl_15vp, 1.0),
                 (dev.dcl_15vpsw, 0.0), (dev.dcl_5v, 5.0), )),
            tester.RelaySubStep(((dev.rla_emergency, True), ), delay=1),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                 mes.dmm_isvmonoff, mes.dmm_15voff, mes.dmm__15voff,
                 mes.dmm_15vpoff, mes.dmm_15vpswoff, mes.dmm_5voff),
                 timeout=5)
            ))
