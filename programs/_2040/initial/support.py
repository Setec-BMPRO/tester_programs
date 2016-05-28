#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Initial Test Program."""

import time

import tester
import sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_Vout = tester.DCSource(devices['DCS1'])
        dcs_dcin1 = tester.DCSource(devices['DCS2'])
        dcs_dcin2 = tester.DCSource(devices['DCS3'])
        dcs_dcin3 = tester.DCSource(devices['DCS4'])
        dcs_dcin4 = tester.DCSource(devices['DCS5'])
        self.dcs_dcin = tester.DCSourceParallel(
            (dcs_dcin1, dcs_dcin2, dcs_dcin3, dcs_dcin4, ))
        self.dcl_Vout = tester.DCLoad(devices['DCL4'])
        self.discharge = tester.Discharge(devices['DIS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_dcin, self.dcs_Vout):
            dcs.output(0.0, False)
        self.dcl_Vout.output(1.0)
        time.sleep(1)
        self.discharge.pulse()
        self.dcl_Vout.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oLock = sensor.Res(dmm, high=12, low=6, rng=10000, res=1)
        self.oVccAC = sensor.Vdc(dmm, high=2, low=5, rng=100, res=0.001)
        self.oVccDC = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self.oVbus = sensor.Vdc(dmm, high=3, low=5, rng=1000, res=0.01)
        self.oSD = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oACin = sensor.Vac(dmm, high=5, low=4, rng=1000, res=0.01)
        self.oVout = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.oGreen = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oRedDC = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.001)
        self.oRedAC = sensor.Vdc(dmm, high=1, low=5, rng=100, res=0.001)
        self.oDCin = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=3.2, stop=4.3, step=0.05, delay=0.15)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_Lock = tester.Measurement(limits['FixtureLock'], sense.oLock)
        self.dmm_VccAC = tester.Measurement(limits['VccAC'], sense.oVccAC)
        self.dmm_VccDC = tester.Measurement(limits['VccDC'], sense.oVccDC)
        self.dmm_VbusMin = tester.Measurement(limits['VbusMin'], sense.oVbus)
        self.dmm_SDOff = tester.Measurement(limits['SDOff'], sense.oSD)
        self.dmm_SDOn = tester.Measurement(limits['SDOn'], sense.oSD)
        self.dmm_ACmin = tester.Measurement(limits['ACmin'], sense.oACin)
        self.dmm_ACtyp = tester.Measurement(limits['ACtyp'], sense.oACin)
        self.dmm_ACmax = tester.Measurement(limits['ACmax'], sense.oACin)
        self.dmm_VoutExt = tester.Measurement(limits['VoutExt'], sense.oVout)
        self.dmm_Vout = tester.Measurement(limits['Vout'], sense.oVout)
        self.dmm_GreenOn = tester.Measurement(limits['GreenOn'], sense.oGreen)
        self.dmm_RedDCOff = tester.Measurement(limits['RedDCOff'], sense.oRedDC)
        self.dmm_RedDCOn = tester.Measurement(limits['RedDCOn'], sense.oRedDC)
        self.dmm_RedACOff = tester.Measurement(limits['RedACOff'], sense.oRedAC)
        self.dmm_DCmin = tester.Measurement(limits['DCmin'], sense.oDCin)
        self.dmm_DCtyp = tester.Measurement(limits['DCtyp'], sense.oDCin)
        self.dmm_DCmax = tester.Measurement(limits['DCmax'], sense.oDCin)
        self.ramp_OCP = tester.Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # SecCheck: Apply Ext Vout, measure.
        self.sec_chk = tester.Step((
            tester.DcSubStep(setting=((d.dcs_Vout, 20.0), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_VoutExt, m.dmm_SDOff, m.dmm_GreenOn, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_Vout, 0.0), )),
            ))
        # DCPowerOn: Apply DC power, measure, OCP.
        self.dcpwr_on = tester.Step((
            tester.DcSubStep(setting=((d.dcs_dcin, 10.25), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_DCmin, m.dmm_VccDC, m.dmm_Vout,
                 m.dmm_GreenOn, m.dmm_RedDCOff), timeout=5),
            tester.LoadSubStep(((d.dcl_Vout, 1.0), ), output=True, delay=1.0),
            tester.MeasureSubStep((m.dmm_Vout, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_dcin, 40.0), )),
            tester.MeasureSubStep(
                (m.dmm_DCmax, m.dmm_VccDC, m.dmm_Vout, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_dcin, 25.0), )),
            tester.MeasureSubStep(
                (m.dmm_DCtyp, m.dmm_VccDC, m.dmm_Vout, m.ramp_OCP), timeout=5),
            tester.LoadSubStep(((d.dcl_Vout, 4.1), ), delay=0.5),
            tester.MeasureSubStep((m.dmm_SDOn, m.dmm_RedDCOn, ), timeout=5),
            tester.LoadSubStep(((d.dcl_Vout, 0.0), )),
            tester.DcSubStep(
                setting=((d.dcs_dcin, 0.0), ), output=False, delay=2),
            ))
        # ACPowerOn: Apply AC power, measure, OCP.
        self.acpwr_on = tester.Step((
            tester.AcSubStep(
                acs=d.acsource, voltage=90.0, output=True, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_ACmin, m.dmm_VbusMin, m.dmm_VccAC, m.dmm_Vout,
                 m.dmm_GreenOn, m.dmm_RedACOff), timeout=15),
            tester.LoadSubStep(((d.dcl_Vout, 2.0), ), delay=1.0),
            tester.MeasureSubStep((m.dmm_Vout, ), timeout=5),
            tester.AcSubStep(acs=d.acsource, voltage=265.0, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_ACmax, m.dmm_VccAC, m.dmm_Vout, ), timeout=5),
            tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_ACtyp, m.dmm_VccAC, m.dmm_Vout, m.ramp_OCP), timeout=5),
            ))
