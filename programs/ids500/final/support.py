#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Final Test Program."""

from pydispatch import dispatcher
import tester
from . import limit
from .. import console


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
        self.pic_ser.port = limit.PIC_PORT
        self.pic = console.Console(self.pic_ser)
        # Auto add prompt to puts strings
        self.pic.puts_prompt = '\r\n'

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
        self.hwrev = console.Sensor(
            pic, 'PIC-HwRev', rdgtype=sensor.ReadingString)
        self.sernum = console.Sensor(
            pic, 'PIC-SerNum', rdgtype=sensor.ReadingString)

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
