#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Final Test Program."""

from pydispatch import dispatcher

import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from .. import console

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcs_TecVset = dcsource.DCSource(devices['DCS1'])
        self.dcs_IsSet = dcsource.DCSource(devices['DCS2'])
        self.dcs_5V = dcsource.DCSource(devices['DCS3'])
        self.dcl_Tec = dcload.DCLoad(devices['DCL2'])
        self.dcl_15Vp = dcload.DCLoad(devices['DCL3'])
        self.dcl_15VpSw = dcload.DCLoad(devices['DCL4'])
        self.dcl_5V = dcload.DCLoad(devices['DCL5'])
        self.rla_MainsEnable = relay.Relay(devices['RLA1'])
        self.rla_15VpEnable = relay.Relay(devices['RLA2'])
        self.rla_Emergency = relay.Relay(devices['RLA3'])
        self.rla_Crowbar = relay.Relay(devices['RLA4'])
        self.rla_EnableIs = relay.Relay(devices['RLA5'])
        self.rla_Interlock = relay.Relay(devices['RLA6'])
        self.rla_Enable = relay.Relay(devices['RLA7'])
        self.rla_TecPhase = relay.Relay(devices['RLA8'])

    def reset(self):
        """Reset instruments."""
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

    def __init__(self, logical_devices, limits, picdev):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirTecErr = sensor.Mirror()
        self.oMirTecVmonErr = sensor.Mirror()
        self.oMirIsErr = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
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
        self.oPic_SwTstMode = console.Sensor(
            picdev, 'PIC-SwTstMode', rdgtype=sensor.ReadingString)
        self.oPic_HwVerChk = console.Sensor(
            picdev, 'PIC-HwVerCheck', rdgtype=sensor.ReadingString)
        self.oPic_SerChk = console.Sensor(
            picdev, 'PIC-SerCheck', rdgtype=sensor.ReadingString)
        self.oYesNoPsu = sensor.YesNo(
            message=translate('ids500_final', 'IsPSULedGreen?'),
            caption=translate('ids500_final', 'capPsuLed'))
        self.oYesNoTecGreen = sensor.YesNo(
            message=translate('ids500_final', 'IsTECLedGreen?'),
            caption=translate('ids500_final', 'capTecGreenLed'))
        self.oYesNoTecRed = sensor.YesNo(
            message=translate('ids500_final', 'IsTECLedRed?'),
            caption=translate('ids500_final', 'capTecRedLed'))
        self.oYesNoLddGreen = sensor.YesNo(
            message=translate('ids500_final', 'IsLDDLedGreen?'),
            caption=translate('ids500_final', 'capLddGreenLed'))
        self.oYesNoLddRed = sensor.YesNo(
            message=translate('ids500_final', 'IsLDDLedRed?'),
            caption=translate('ids500_final', 'capLddRedLed'))
        self.oSerEntry = sensor.DataEntry(
            message=translate('ids500_final', 'msgSerEntry'),
            caption=translate('ids500_final', 'capSerEntry'))
        self.oOCP5V = sensor.Ramp(
            stimulus=logical_devices.dcl_5V, sensor=self.o5V,
            detect_limit=(limits['inOCP5V'], ),
            start=5.0, stop=12.0, step=0.1, delay=0.2)
        self.oOCP15Vp = sensor.Ramp(
            stimulus=logical_devices.dcl_15Vp, sensor=self.o15Vp,
            detect_limit=(limits['inOCP15Vp'], ),
            start=5.0, stop=12.0, step=0.1, delay=0.2)
        self.oOCP15VpSw = sensor.Ramp(
            stimulus=logical_devices.dcl_15VpSw, sensor=self.o15VpSw,
            detect_limit=(limits['inOCP15VpSw'], ),
            start=4.0, stop=11.0, step=0.1, delay=0.2)
        self.oOCPTec = sensor.Ramp(
            stimulus=logical_devices.dcl_Tec, sensor=self.Tec,
            detect_limit=(limits['inOCPTec'], ),
            start=20.0, stop=23.0, step=0.1, delay=0.2)

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
        self.dmm_15VpSw = Measurement(limits['15Vp'], sense.o15VpSw)
        self.dmm_5VOff = Measurement(limits['5VOff'], sense.o5V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.pic_SwTstMode = Measurement(
            limits['SwTstMode'], sense.oPic_SwTstMode)
        self.pic_HwVerChk = Measurement(
            limits['HwVerCheck'], sense.oPic_HwVerChk)
        self.pic_SerChk = Measurement(limits['SerCheck'], sense.oPic_SerChk)
        self.ui_YesNoPsu = Measurement(limits['Notify'], sense.oYesNoPsu)
        self.ui_YesNoTecGreen = Measurement(
            limits['Notify'], sense.oYesNoTecGreen)
        self.ui_YesNoTecRed = Measurement(limits['Notify'], sense.oYesNoTecRed)
        self.ui_YesNoLddGreen = Measurement(
            limits['Notify'], sense.oYesNoLddGreen)
        self.ui_YesNoLddRed = Measurement(limits['Notify'], sense.oYesNoLddRed)
        self.ui_SerEntry = Measurement(limits['SerEntry'], sense.oSerEntry)
        self.ramp_OCP5V = Measurement(limits['OCP5V'], sense.oOCP5V)
        self.ramp_OCP15Vp = Measurement(limits['OCP15Vp'], sense.oOCP15Vp)
        self.ramp_OCP15VpSw = Measurement(
            limits['OCP15VpSw'], sense.oOCP15VpSw)
        self.ramp_OCPTec = Measurement(limits['OCPTec'], sense.oOCPTec)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp: Set min loads, Input AC, measure.
        ld1 = LoadSubStep(
            ((d.dcl_Tec, 0.0), (d.dcl_15Vp, 1.0), (d.dcl_15VpSw, 0.0),
             (d.dcl_5V, 5.0)), output=True)
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=2.0)
        msr1 = MeasureSubStep(
            (m.dmm_TecOff, m.dmm_TecVmonOff, m.dmm_LddOff, m.dmm_IsVmonOff,
             m.dmm_15VOff, m.dmm__15VOff, m.dmm_15VpOff, m.dmm_15VpSwOff,
             m.dmm_5VOff, ),
             timeout=5)
        self.pwr_up = Step((ld1, acs1, msr1))
        # KeySw: Turn on KeySwitches, measure.
        rly1 = RelaySubStep(((d.rla_MainsEnable, True), ))
        msr1 = MeasureSubStep(
            (m.dmm_TecOff, m.dmm_TecVmonOff, m.dmm_LddOff, m.dmm_IsVmonOff,
             m.dmm_15V, m.dmm__15V, m.dmm_15Vp, m.dmm_15VpSwOff, m.dmm_5V, ),
             timeout=5)
        rly2 = RelaySubStep(((d.rla_15VpEnable, True), ))
        msr2 = MeasureSubStep(
            (m.dmm_TecOff, m.dmm_TecVmonOff, m.dmm_LddOff, m.dmm_IsVmonOff,
             m.dmm_15V, m.dmm__15V, m.dmm_15Vp, m.dmm_15VpSw, m.dmm_5V, ),
             timeout=5)
        self.key_sw1 = Step((rly1, msr1, ))
        self.key_sw12 = Step((rly2, msr2, ))
        # TEC:  Enable, measure.
        dcs1 = DcSubStep(setting=((d.dcs_5V, 5.0), ), output=True)
        rly1 = RelaySubStep(((d.rla_Enable, True), ))
        dcs2 = DcSubStep(setting=((d.dcs_TecVset, 0.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_TecOff, m.dmm_TecVmon0V, ), timeout=5)
        ld1 = LoadSubStep(((d.dcl_Tec, 0.3), ))
        dcs3 = DcSubStep(setting=((d.dcs_TecVset, 5.0), ), delay=0.1)
        msr2 = MeasureSubStep(
            (m.ui_YesNoPsu, m.ui_YesNoTecGreen, ), timeout=5)
        rly2 = RelaySubStep(((d.rla_TecPhase, True), ))
        msr3 = MeasureSubStep(
            (m.dmm_TecPhase, m.ui_YesNoTecRed, ), timeout=5)
        rly3 = RelaySubStep(((d.rla_TecPhase, False), ))
        self.tec_pre = Step((dcs1, rly1, dcs2, msr1, ld1, dcs3))
        self.tec_post = Step((msr2, rly2, msr3, rly3))
        # LDD:  Enable, measure.
        dcs1 = DcSubStep(setting=((d.dcs_IsSet, 0.0), ), output=True)
        rly1 = RelaySubStep(
            ((d.rla_Crowbar, True), (d.rla_Interlock, True),
             (d.rla_EnableIs, True), ))
        msr1 = MeasureSubStep(
            (m.dmm_IsVmon, m.dmm_IsOut0V, m.dmm_IsIout0V, ), timeout=5)
        dcs2 = DcSubStep(setting=((d.dcs_IsSet, 0.6), ), delay=1)
        msr2 = MeasureSubStep((m.dmm_IsVmon, ), timeout=5)
        msr3 = MeasureSubStep((m.ui_YesNoLddGreen, ), timeout=5)
        dcs3 = DcSubStep(setting=((d.dcs_IsSet, 5.0), ), delay=1)
        msr4 = MeasureSubStep((m.dmm_IsVmon, ), timeout=5)
        msr5 = MeasureSubStep((m.ui_YesNoLddRed, ), timeout=5)
        dcs4 = DcSubStep(setting=((d.dcs_IsSet, 0.0), ), output=False)
        rly2 = RelaySubStep(
            ((d.rla_Crowbar, False), (d.rla_Interlock, False),
             (d.rla_EnableIs, False),))
        self.ldd_06V = Step((dcs1, rly1, msr1, dcs2, msr2))
        self.ldd_5V = Step((msr3, dcs3, msr4))
        self.ldd_off = Step((msr5, dcs4, rly2))
        # OCP:
        ld1 = LoadSubStep(
            ((d.dcl_Tec, 0.0), (d.dcl_15Vp, 1.0), (d.dcl_15VpSw, 0.0),
             (d.dcl_5V, 5.0)))
        msr1 = MeasureSubStep((m.ramp_OCP5V, ), timeout=5)
        msr2 = MeasureSubStep((m.ramp_OCP15Vp, ), timeout=5)
        msr3 = MeasureSubStep((m.ramp_OCP15VpSw, ), timeout=5)
        dcs1 = DcSubStep(setting=((d.dcs_TecVset, 5.0), ), delay=1)
        ld2 = LoadSubStep(((d.dcl_Tec, 0.5), ), delay=1)
        msr4 = MeasureSubStep((m.ramp_OCPTec, ), timeout=5)
        dcs2 = DcSubStep(setting=((d.dcs_5V, 0.0), ))
        acs1 = AcSubStep(acs=d.acsource, voltage=0.0, delay=3.5)
        acs2 = AcSubStep(acs=d.acsource, voltage=240.0, delay=1.0)
        dcs3 = DcSubStep(setting=((d.dcs_5V, 5.0), ))
        msr5 = MeasureSubStep((m.dmm_15Vp, ), timeout=5)
        self.ocp_5V = Step((ld1, msr1))
        self.ocp_15Vp = Step((msr2, ))
        self.ocp_15VpSw = Step((msr3, ))
        self.ocp_tec = Step((dcs1, ld2, msr4))
        self.restart = Step((ld1, dcs2, acs1, acs2, dcs3, msr5))
        # EmergStop:
        ld1 = LoadSubStep(
            ((d.dcl_Tec, 0.0), (d.dcl_15Vp, 1.0), (d.dcl_15VpSw, 0.0),
             (d.dcl_5V, 5.0)))
        rly1 = RelaySubStep(((d.rla_Emergency, True), ), delay=1)
        msr1 = MeasureSubStep(
            (m.dmm_TecOff, m.dmm_TecVmonOff, m.dmm_LddOff, m.dmm_IsVmonOff,
             m.dmm_15VOff, m.dmm__15VOff, m.dmm_15VpOff, m.dmm_15VpSwOff,
             m.dmm_5VOff, ), timeout=5)
        self.emg_stop = Step((ld1, rly1, msr1))
