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
        self.dcs_TecVset = tester.DCSource(devices['DCS1'])
        self.dcs_IsSet = tester.DCSource(devices['DCS2'])
        self.dcs_5V = tester.DCSource(devices['DCS3'])
        self.dcl_Tec = tester.DCLoad(devices['DCL2'])
        self.dcl_15Vp = tester.DCLoad(devices['DCL3'])
        self.dcl_15VpSw = tester.DCLoad(devices['DCL4'])
        self.dcl_5V = tester.DCLoad(devices['DCL5'])
        self.rla_MainsEnable = tester.Relay(devices['RLA1'])
        self.rla_15VpEnable = tester.Relay(devices['RLA2'])
        self.rla_Emergency = tester.Relay(devices['RLA3'])
        self.rla_Crowbar = tester.Relay(devices['RLA4'])
        self.rla_EnableIs = tester.Relay(devices['RLA5'])
        self.rla_Interlock = tester.Relay(devices['RLA6'])
        self.rla_Enable = tester.Relay(devices['RLA7'])
        self.rla_TecPhase = tester.Relay(devices['RLA8'])
        # Serial connection to the console to communicate with the PIC
        self.pic_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=19200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self.pic_ser.port = limit.PIC_PORT
        self.pic = console.Console(self.pic_ser, verbose=True)

    def ids_puts(self, string_data, preflush=0, postflush=0, priority=False,
                 addprompt=False):
        """Push string data into the IDS buffer if FIFOs are enabled."""
        if self.fifo:
            if addprompt:
                string_data = string_data + '\r\n>'
            self.pic.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.pic_ser.close()
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_TecVset, self.dcs_IsSet, self.dcs_5V):
            dcs.output(0.0, False)
        for ld in (self.dcl_Tec, self.dcl_15Vp, self.dcl_15VpSw, self.dcl_5V):
            ld.output(0.0, False)
        for rla in (
                self.rla_MainsEnable, self.rla_15VpEnable, self.rla_Crowbar,
                self.rla_Emergency, self.rla_EnableIs, self.rla_Interlock,
                self.rla_Enable, self.rla_TecPhase):
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
        self.Tec = sensor.Vdc(dmm, high=1, low=3, rng=100, res=0.001)
        self.TecVset = sensor.Vdc(dmm, high=3, low=6, rng=10, res=0.001)
        self.TecVmon = sensor.Vdc(dmm, high=4, low=6, rng=10, res=0.001)
        self.Ldd = sensor.Vdc(dmm, high=2, low=4, rng=10, res=0.001)
        self.IsSet = sensor.Vdc(dmm, high=5, low=6, rng=10, res=0.0001)
        self.IsOut = sensor.Vdc(dmm, high=14, low=5, rng=10, res=0.00001)
        self.IsIout = sensor.Vdc(dmm, high=6, low=6, rng=10, res=0.0001)
        self.IsVmon = sensor.Vdc(dmm, high=7, low=6, rng=10, res=0.001)
        self.o15V = sensor.Vdc(dmm, high=8, low=1, rng=100, res=0.001)
        self.o_15V = sensor.Vdc(dmm, high=9, low=1, rng=100, res=0.001)
        self.o15Vp = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self.o15VpSw = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=12, low=1, rng=10, res=0.001)
        self.PwrOk = sensor.Vdc(dmm, high=13, low=2, rng=10, res=0.001)
        self.oHwRev = console.Sensor(
            pic, 'PIC-HwRev', rdgtype=sensor.ReadingString)
        self.oSerChk = console.Sensor(
            pic, 'PIC-SerChk', rdgtype=sensor.ReadingString)
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
        self.oSerEntry = sensor.DataEntry(
            message=tester.translate('ids500_final', 'msgSerEntry'),
            caption=tester.translate('ids500_final', 'capSerEntry'))

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
        self.TecErr = Measurement(limits['TecErr'], sense.oMirTecErr)
        self.TecVmonErr = Measurement(
            limits['TecVmonErr'], sense.oMirTecVmonErr)
        self.SetMonErr = Measurement(limits['SetMonErr'], sense.oMirIsErr)
        self.SetOutErr = Measurement(limits['SetOutErr'], sense.oMirIsErr)
        self.MonOutErr = Measurement(limits['MonOutErr'], sense.oMirIsErr)
        self.dmm_TecOff = Measurement(limits['TecOff'], sense.Tec)
        self.dmm_Tec = Measurement(limits['Tec'], sense.Tec)
        self.dmm_TecPhase = Measurement(limits['TecPhase'], sense.Tec)
        self.dmm_TecVset = Measurement(limits['TecVset'], sense.TecVset)
        self.dmm_TecVmonOff = Measurement(limits['TecVmonOff'], sense.TecVmon)
        self.dmm_TecVmon0V = Measurement(limits['TecVmon0V'], sense.TecVmon)
        self.dmm_TecVmon = Measurement(limits['TecVmon'], sense.TecVmon)
        self.dmm_LddOff = Measurement(limits['LddOff'], sense.Ldd)
        self.dmm_IsVmonOff = Measurement(limits['IsVmonOff'], sense.IsVmon)
        self.dmm_IsVmon = Measurement(limits['IsVmon'], sense.IsVmon)
        self.dmm_IsOut0V = Measurement(limits['IsOut0V'], sense.IsOut)
        self.dmm_IsOut06V = Measurement(limits['IsOut06V'], sense.IsOut)
        self.dmm_IsOut5V = Measurement(limits['IsOut5V'], sense.IsOut)
        self.dmm_IsIout0V = Measurement(limits['IsIout0V'], sense.IsIout)
        self.dmm_IsIout06V = Measurement(limits['IsIout06V'], sense.IsIout)
        self.dmm_IsIout5V = Measurement(limits['IsIout5V'], sense.IsIout)
        self.dmm_IsSet06V = Measurement(limits['IsSet06V'], sense.IsSet)
        self.dmm_IsSet5V = Measurement(limits['IsSet5V'], sense.IsSet)
        self.dmm_15VOff = Measurement(limits['15VOff'], sense.o15V)
        self.dmm_15V = Measurement(limits['15V'], sense.o15V)
        self.dmm__15VOff = Measurement(limits['-15VOff'], sense.o_15V)
        self.dmm__15V = Measurement(limits['-15V'], sense.o_15V)
        self.dmm_15VpOff = Measurement(limits['15VpOff'], sense.o15Vp)
        self.dmm_15Vp = Measurement(limits['15Vp'], sense.o15Vp)
        self.dmm_15VpSwOff = Measurement(limits['15VpSwOff'], sense.o15VpSw)
        self.dmm_15VpSw = Measurement(limits['15VpSw'], sense.o15VpSw)
        self.dmm_5VOff = Measurement(limits['5VOff'], sense.o5V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.pic_hwrev = Measurement(
            limits['HwRev'], sense.oHwRev)
        self.pic_serchk = Measurement(limits['SerChk'], sense.oSerChk)
        self.ui_YesNoPsu = Measurement(limits['Notify'], sense.oYesNoPsu)
        self.ui_YesNoTecGreen = Measurement(
            limits['Notify'], sense.oYesNoTecGreen)
        self.ui_YesNoTecRed = Measurement(limits['Notify'], sense.oYesNoTecRed)
        self.ui_YesNoLddGreen = Measurement(
            limits['Notify'], sense.oYesNoLddGreen)
        self.ui_YesNoLddRed = Measurement(limits['Notify'], sense.oYesNoLddRed)
        self.ui_SerEntry = Measurement(limits['SerEntry'], sense.oSerEntry)


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
                ((dev.dcl_Tec, 0.4), (dev.dcl_15Vp, 0.4),
                 (dev.dcl_15VpSw, 0.4), (dev.dcl_5V, 0.4), ), output=True),
            tester.AcSubStep(acs=dev.acsource, voltage=240.0, output=True,
                                delay=2.0),
            tester.MeasureSubStep(
                (mes.dmm_TecOff, mes.dmm_TecVmonOff, mes.dmm_LddOff,
                 mes.dmm_IsVmonOff, mes.dmm_15VOff, mes.dmm__15VOff,
                 mes.dmm_15VpOff, mes.dmm_15VpSwOff, mes.dmm_5VOff),
                 timeout=5),
            ))

        # KeySw1: KeySwitch 1, measure.
        self.key_sw1 = tester.SubStep((
            tester.RelaySubStep(((dev.rla_MainsEnable, True), )),
            tester.MeasureSubStep(
                (mes.dmm_TecOff, mes.dmm_TecVmonOff, mes.dmm_LddOff,
                 mes.dmm_IsVmonOff, mes.dmm_15V, mes.dmm__15V, mes.dmm_15Vp,
                 mes.dmm_15VpSwOff, mes.dmm_5V),
                 timeout=5),
            ))

        # KeySw12: KeySwitch 1 & 2, measure.
        self.key_sw12 = tester.SubStep((
            tester.RelaySubStep(((dev.rla_15VpEnable, True), )),
            tester.MeasureSubStep(
                (mes.dmm_TecOff, mes.dmm_TecVmonOff, mes.dmm_LddOff,
                 mes.dmm_IsVmonOff, mes.dmm_15V, mes.dmm__15V, mes.dmm_15Vp,
                 mes.dmm_15VpSw, mes.dmm_5V),
                 timeout=5),
            ))

        # EmergStop: Emergency stop, measure.
        self.emg_stop = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_Tec, 0.0), (dev.dcl_15Vp, 1.0),
                 (dev.dcl_15VpSw, 0.0), (dev.dcl_5V, 5.0))),
            tester.RelaySubStep(((dev.rla_Emergency, True), ), delay=1),
            tester.MeasureSubStep(
                (mes.dmm_TecOff, mes.dmm_TecVmonOff, mes.dmm_LddOff,
                 mes.dmm_IsVmonOff, mes.dmm_15VOff, mes.dmm__15VOff,
                 mes.dmm_15VpOff, mes.dmm_15VpSwOff, mes.dmm_5VOff),
                 timeout=5)
            ))
