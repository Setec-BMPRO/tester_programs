#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""IDS-500 Final Test Program."""

import os
from pydispatch import dispatcher
import tester
from tester.testlimit import lim_lo, lim_hilo, lim_string, lim_boolean
import share
from share import oldteststep
from . import console

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

LIMITS = tester.testlimit.limitset((
    lim_lo('TecOff', 1.5),
    lim_lo('TecVmonOff', 1.5),
    lim_lo('LddOff', 1.5),
    lim_lo('IsVmonOff', 1.5),
    lim_lo('15VOff', 1.5),
    lim_lo('-15VOff', 1.5),
    lim_lo('15VpOff', 1.5),
    lim_lo('15VpSwOff', 1.5),
    lim_lo('5VOff', 1.5),
    lim_hilo('15V', 14.25, 15.75),
    lim_hilo('-15V', -15.75, -14.25),
    lim_hilo('15Vp', 14.25, 15.75),
    lim_hilo('15VpSw', 14.25, 15.75),
    lim_hilo('5V', 4.85, 5.10),
    lim_hilo('Tec', 14.70, 15.30),
    lim_hilo('TecPhase', -15.30, -14.70),
    lim_hilo('TecVset', 4.95, 5.05),
    lim_lo('TecVmon0V', 0.5),
    lim_hilo('TecVmon', 4.90, 5.10),
    lim_hilo('TecErr', -0.275, 0.275),
    lim_hilo('TecVmonErr', -0.030, 0.030),
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
    lim_string('HwRev', r'^[0-9]{2}[AB]$'),
    lim_string('SerNum', r'^[AS][0-9]{4}[0-9,A-Z]{2}[0-9]{4}$'),
    lim_boolean('Notify', True),
    ))


class Final(tester.TestSequence):

    """IDS-500 Final Test Programes."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.limits = LIMITS
        self.logdev = LogicalDevices(self.physical_devices, self.fifo)
        self.sensor = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensor, self.limits)
        self.subtest = SubTests(self.logdev, self.meas)
        self.steps = (
            tester.TestStep('PowerUp', self.subtest.pwr_up.run),
            tester.TestStep('KeySw1', self.subtest.key_sw1.run),
            tester.TestStep('KeySw12', self.subtest.key_sw12.run),
            tester.TestStep('TEC', self._step_tec),
            tester.TestStep('LDD', self._step_ldd),
            tester.TestStep('Comms', self._step_comms),
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
        dev.dcs_5v.output(5.0, True)
        dev.rla_enable.set_on()
        dev.dcs_tecvset.output(0.0, True)
        tester.MeasureGroup((mes.dmm_tecoff, mes.dmm_tecvmon0v), timeout=5)
        dev.dcl_tec.output(0.3)
        dev.dcs_tecvset.output(voltage=5.0, delay=0.1)
        Vset, Vmon, Vtec = tester.MeasureGroup(
            (mes.dmm_tecvset, mes.dmm_tecvmon, mes.dmm_tec), timeout=5).readings
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        self.sensor.oMirTecErr.store(Vtec - (Vset * 3))
        mes.tecerr.measure(timeout=5)
        self.sensor.oMirTecVmonErr.store(Vmon - (Vtec / 3))
        mes.tecvmonerr.measure(timeout=5)
        tester.MeasureGroup((mes.ui_YesNoPsu, mes.ui_YesNoTecGreen), timeout=5)
        dev.rla_tecphase.set_on()
        tester.MeasureGroup((mes.dmm_tecphase, mes.ui_YesNoTecRed), timeout=5)
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
            (mes.dmm_isvmon, mes.dmm_isout0v, mes.dmm_isiout0v), timeout=5)
        # Run LDD at 6A
        dev.dcs_isset.output(voltage=0.6, delay=1)
        mes.dmm_isvmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_isset06v, mes.dmm_isout06v, mes.dmm_isiout06v),
            timeout=5).readings
        self._ldd_err(Iset, Iout, Imon)
        # Run LDD at 50A
        mes.ui_YesNoLddGreen.measure(timeout=5)
        dev.dcs_isset.output(voltage=5.0, delay=1)
        mes.dmm_isvmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_isset5v, mes.dmm_isout5v, mes.dmm_isiout5v),
            timeout=5).readings
        for name in ('SetMonErr', 'SetOutErr', 'MonOutErr'):
            self.limits[name].limit = (-0.7, 0.7)
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
    def _step_comms(self, dev, mes):
        """Write HW version and serial number. Read back values."""
        dev.pic.open()
        dev.pic.clear_port()
        dev.pic.sw_test_mode()
        hwrev = mes.ui_hwrev.measure().reading1
        dev.pic.exp_cnt = 3
        dev.pic['WriteHwRev'] = hwrev
        dev.pic.exp_cnt = 1
        mes.pic_hwrev.testlimit[0].limit = hwrev
        mes.pic_hwrev.measure()
        sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        dev.pic.exp_cnt = 3
        dev.pic['WriteSerNum'] = sernum
        dev.pic.exp_cnt = 1
        mes.pic_sernum.testlimit[0].limit = sernum
        mes.pic_sernum.measure()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_tecvset = tester.DCSource(devices['DCS1'])
        self.dcs_isset = tester.DCSource(devices['DCS2'])
        self.dcs_5v = tester.DCSource(devices['DCS3'])
        self.dcl_tec = tester.DCLoad(devices['DCL2'])
        self.dcl_15vp = tester.DCLoad(devices['DCL3'])
        self.dcl_15vpsw = tester.DCLoad(devices['DCL4'])
        self.dcl_5v = tester.DCLoad(devices['DCL5'])
        self.rla_mainsenable = tester.Relay(devices['RLA1'])
        self.rla_15vpenable = tester.Relay(devices['RLA2'])
        self.rla_emergency = tester.Relay(devices['RLA3'])
        self.rla_crowbar = tester.Relay(devices['RLA4'])
        self.rla_enableis = tester.Relay(devices['RLA5'])
        self.rla_interlock = tester.Relay(devices['RLA6'])
        self.rla_enable = tester.Relay(devices['RLA7'])
        self.rla_tecphase = tester.Relay(devices['RLA8'])
        # Serial connection to the console to communicate with the PIC
        self.pic_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=19200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self.pic_ser.port = PIC_PORT
        self.pic = console.Console(self.pic_ser)

    def reset(self):
        """Reset instruments."""
        self.pic_ser.close()
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_tecvset, self.dcs_isset, self.dcs_5v):
            dcs.output(0.0, False)
        for ld in (self.dcl_tec, self.dcl_15vp, self.dcl_15vpsw, self.dcl_5v):
            ld.output(0.0, False)
        for rla in (
                self.rla_mainsenable, self.rla_15vpenable, self.rla_crowbar,
                self.rla_emergency, self.rla_enableis, self.rla_interlock,
                self.rla_enable, self.rla_tecphase):
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
        pic = logical_devices.pic
        sensor = tester.sensor
        self.oMirTecErr = sensor.Mirror()
        self.oMirTecVmonErr = sensor.Mirror()
        self.oMirIsErr = sensor.Mirror()
        self.tec = sensor.Vdc(dmm, high=1, low=3, rng=100, res=0.001)
        self.tecvset = sensor.Vdc(dmm, high=3, low=6, rng=10, res=0.001)
        self.tecvmon = sensor.Vdc(dmm, high=4, low=6, rng=10, res=0.001)
        self.ldd = sensor.Vdc(dmm, high=2, low=4, rng=10, res=0.001)
        self.isset = sensor.Vdc(dmm, high=5, low=6, rng=10, res=0.0001)
        self.isout = sensor.Vdc(dmm, high=14, low=5, rng=10, res=0.00001)
        self.isiout = sensor.Vdc(dmm, high=6, low=6, rng=10, res=0.0001)
        self.isvmon = sensor.Vdc(dmm, high=7, low=6, rng=10, res=0.001)
        self.o15v = sensor.Vdc(dmm, high=8, low=1, rng=100, res=0.001)
        self.o_15v = sensor.Vdc(dmm, high=9, low=1, rng=100, res=0.001)
        self.o15vp = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self.o15vpsw = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self.o5v = sensor.Vdc(dmm, high=12, low=1, rng=10, res=0.001)
        self.pwrok = sensor.Vdc(dmm, high=13, low=2, rng=10, res=0.001)
        self.oYesNoPsu = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsPSULedGreen?'),
            caption=tester.translate('ids500_final', 'capPsuLed'))
        self.oYesNoTecGreen = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsTECLedGreen?'),
            caption=tester.translate('ids500_final', 'capTecGreenLed'))
        self.oYesNoTecRed = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsTECLedRed?'),
            caption=tester.translate('ids500_final', 'capTecRedLed'))
        self.oYesNoLddGreen = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsLDDLedGreen?'),
            caption=tester.translate('ids500_final', 'capLddGreenLed'))
        self.oYesNoLddRed = sensor.YesNo(
            message=tester.translate('ids500_final', 'IsLDDLedRed?'),
            caption=tester.translate('ids500_final', 'capLddRedLed'))
        self.oSerNumEntry = sensor.DataEntry(
            message=tester.translate('ids500_final', 'msgSerEntry'),
            caption=tester.translate('ids500_final', 'capSerEntry'))
        self.oHwRevEntry = sensor.DataEntry(
            message=tester.translate('ids500_final', 'msgHwRev'),
            caption=tester.translate('ids500_final', 'capHwRev'))
        self.oHwRevEntry.callback = self.clean_hwrev
        self.hwrev = console.Sensor(
            pic, 'PIC-HwRev', rdgtype=sensor.ReadingString)
        self.sernum = console.Sensor(
            pic, 'PIC-SerNum', rdgtype=sensor.ReadingString)

    def clean_hwrev(self, value):
        """Callback for the HwRev user entry sensor.

        @param value Raw sensor reading string
        @return Uppercase, trimmed reading string

        """
        return value.upper().strip()

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
           @param limits Product test limits        self.dmm_tecphase = Measurement(limits['TecPhase'], sense.tec)


        """
        Measurement = tester.Measurement
        self.tecerr = Measurement(limits['TecErr'], sense.oMirTecErr)
        self.tecvmonerr = Measurement(
            limits['TecVmonErr'], sense.oMirTecVmonErr)
        self.setmonerr = Measurement(limits['SetMonErr'], sense.oMirIsErr)
        self.setouterr = Measurement(limits['SetOutErr'], sense.oMirIsErr)
        self.monouterr = Measurement(limits['MonOutErr'], sense.oMirIsErr)
        self.dmm_tecoff = Measurement(limits['TecOff'], sense.tec)
        self.dmm_tec = Measurement(limits['Tec'], sense.tec)
        self.dmm_tecphase = Measurement(limits['TecPhase'], sense.tec)
        self.dmm_tecvset = Measurement(limits['TecVset'], sense.tecvset)
        self.dmm_tecvmonoff = Measurement(limits['TecVmonOff'], sense.tecvmon)
        self.dmm_tecvmon0v = Measurement(limits['TecVmon0V'], sense.tecvmon)
        self.dmm_tecvmon = Measurement(limits['TecVmon'], sense.tecvmon)
        self.dmm_lddoff = Measurement(limits['LddOff'], sense.ldd)
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
        self.ui_YesNoPsu = Measurement(limits['Notify'], sense.oYesNoPsu)
        self.ui_YesNoTecGreen = Measurement(
            limits['Notify'], sense.oYesNoTecGreen)
        self.ui_YesNoTecRed = Measurement(
            limits['Notify'], sense.oYesNoTecRed)
        self.ui_YesNoLddGreen = Measurement(
            limits['Notify'], sense.oYesNoLddGreen)
        self.ui_YesNoLddRed = Measurement(
            limits['Notify'], sense.oYesNoLddRed)
        self.ui_sernum = Measurement(limits['SerNum'], sense.oSerNumEntry)
        self.ui_hwrev = Measurement(limits['HwRev'], sense.oHwRevEntry)
        # Create limits locally for these measurements.
        self.pic_hwrev = Measurement(
            tester.LimitString('HwRev-PIC', ''), sense.hwrev)
        self.pic_sernum = Measurement(
            tester.LimitString('SerNum-PIC', ''), sense.sernum)


class SubTests():

    """SubTest Steps."""

    def __init__(self, dev, mes):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        # PowerUp: Min loads, input AC, measure.
        self.pwr_up = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_tec, 0.0), (dev.dcl_15vp, 1.0),
                 (dev.dcl_15vpsw, 0.0), (dev.dcl_5v, 5.0), ), output=True),
            tester.AcSubStep(acs=dev.acsource, voltage=240.0, output=True,
                                delay=2.0),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                 mes.dmm_isvmonoff, mes.dmm_15voff, mes.dmm__15voff,
                 mes.dmm_15vpoff, mes.dmm_15vpswoff, mes.dmm_5voff),
                 timeout=5),
            ))

        # KeySw1: KeySwitch 1, measure.
        self.key_sw1 = tester.SubStep((
            tester.RelaySubStep(((dev.rla_mainsenable, True), )),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                 mes.dmm_isvmonoff, mes.dmm_15v, mes.dmm__15v, mes.dmm_15vp,
                 mes.dmm_15vpswoff, mes.dmm_5v),
                 timeout=5),
            ))

        # KeySw12: KeySwitch 1 & 2, measure.
        self.key_sw12 = tester.SubStep((
            tester.RelaySubStep(((dev.rla_15vpenable, True), )),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                 mes.dmm_isvmonoff, mes.dmm_15v, mes.dmm__15v, mes.dmm_15vp,
                 mes.dmm_15vpsw, mes.dmm_5v),
                 timeout=5),
            ))

        # EmergStop: Emergency stop, measure.
        self.emg_stop = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_tec, 0.0), (dev.dcl_15vp, 1.0),
                 (dev.dcl_15vpsw, 0.0), (dev.dcl_5v, 5.0))),
            tester.RelaySubStep(((dev.rla_emergency, True), ), delay=1),
            tester.MeasureSubStep(
                (mes.dmm_tecoff, mes.dmm_tecvmonoff, mes.dmm_lddoff,
                 mes.dmm_isvmonoff, mes.dmm_15voff, mes.dmm__15voff,
                 mes.dmm_15vpoff, mes.dmm_15vpswoff, mes.dmm_5voff),
                 timeout=5)
            ))
