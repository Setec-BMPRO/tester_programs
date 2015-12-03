#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Main Test Program."""

from pydispatch import dispatcher
import sensor
import tester
from tester.devlogical import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_TecVset = dcsource.DCSource(devices['DCS1'])
        self.dcs_IsSet = dcsource.DCSource(devices['DCS2'])
        self.dcs_5V = dcsource.DCSource(devices['DCS3'])
        self.dcl_Tec = dcload.DCLoad(devices['DCL1'])
        self.dcl_15Vp = dcload.DCLoad(devices['DCL2'])
        self.dcl_15Vpsw = dcload.DCLoad(devices['DCL5'])
        self.dcl_5V = dcload.DCLoad(devices['DCL6'])
        self.rla_KeySw1 = relay.Relay(devices['RLA1'])
        self.rla_KeySw2 = relay.Relay(devices['RLA2'])
        self.rla_Emergency = relay.Relay(devices['RLA3'])
        self.rla_Crowbar = relay.Relay(devices['RLA4'])
        self.rla_EnableIS = relay.Relay(devices['RLA5'])
        self.rla_Interlock = relay.Relay(devices['RLA6'])
        self.rla_Enable = relay.Relay(devices['RLA7'])
        self.rla_TecPhase = relay.Relay(devices['RLA8'])
        self.rla_LedSel0 = relay.Relay(devices['RLA9'])
        self.rla_LedSel1 = relay.Relay(devices['RLA10'])
        self.rla_LedSel2 = relay.Relay(devices['RLA11'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_TecVset, self.dcs_IsSet, self.dcs_5V):
            dcs.output(0.0, False)
        for ld in (self.dcl_Tec, self.dcl_15Vp, self.dcl_15Vpsw, self.dcl_5V):
            ld.output(0.0, False)
        for rla in (self.rla_KeySw1, self.rla_KeySw2, self.rla_Emergency,
                    self.rla_Crowbar, self.rla_EnableIS, self.rla_Interlock,
                    self.rla_Enable, self.rla_TecPhase, self.rla_LedSel0,
                    self.rla_LedSel1, self.rla_LedSel2):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirPIC = s_mirror.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.Lock = sensor.Res(dmm, high=18, low=3, rng=10000, res=1)
        self.oTec = sensor.Vdc(dmm, high=1, low=4, rng=100, res=0.001)
        self.oLdd = sensor.Vdc(dmm, high=2, low=5, rng=100, res=0.001)
        self.oTecVset = sensor.Vdc(dmm, high=3, low=7, rng=10, res=0.001)
        self.oTecVmon = sensor.Vdc(dmm, high=4, low=7, rng=10, res=0.001)
        self.oIsSet = sensor.Vdc(dmm, high=5, low=7, rng=10, res=0.001)
        self.oIsIout = sensor.Vdc(dmm, high=6, low=7, rng=10, res=0.001)
        self.oIsVmon = sensor.Vdc(dmm, high=7, low=7, rng=10, res=0.001)
        self.oIsOut = sensor.Vdc(dmm, high=14, low=6, rng=10, res=0.001)
        self.o15V = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.om15V = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.001)
        self.o15Vp = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.001)
        self.o15VpSw = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=12, low=3, rng=100, res=0.001)
        self.oPwrOk = sensor.Vdc(dmm, high=13, low=8, rng=100, res=0.01)
        self.oActive = sensor.Vac(dmm, high=20, low=1, rng=1000, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=15, low=2, rng=1000, res=0.01)
        self.oRed = sensor.Vdc(dmm, high=16, low=7, rng=10, res=0.01)
        self.oGreen = sensor.Vdc(dmm, high=17, low=7, rng=10, res=0.01)
        self.oFan1 = sensor.Vdc(dmm, high=18, low=7, rng=100, res=0.001)
        self.oFan2 = sensor.Vdc(dmm, high=19, low=7, rng=100, res=0.001)
        self.oVsec13V = sensor.Vdc(dmm, high=21, low=7, rng=100, res=0.01)
        self.o5VLddTec = sensor.Vdc(dmm, high=22, low=7, rng=10, res=0.01)
        self.o5VuPAux = sensor.Vdc(dmm, high=23, low=7, rng=10, res=0.01)
        self.o5VuP = sensor.Vdc(dmm, high=24, low=7, rng=10, res=0.01)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirPIC.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        mes = tester.measure
        lim = limits
        sen = sense
        self.dmm_Lock = mes.Measurement(lim['FixtureLock'], sen.Lock)
        self.dmm_TecOff = mes.Measurement(lim['Off'], sen.oTec)
        self.dmm_TecVmonOff = mes.Measurement(lim['Off'], sen.oTecVmon)
        self.dmm_LddOff = mes.Measurement(lim['Off'], sen.oLdd)
        self.dmm_IsVmonOff = mes.Measurement(lim['Off'], sen.oIsVmon)
        self.dmm_15VOff = mes.Measurement(lim['Off'], sen.o15V)
        self.dmm_m15VOff = mes.Measurement(lim['Off'], sen.om15V)
        self.dmm_15VpOff = mes.Measurement(lim['Off'], sen.o15Vp)
        self.dmm_15VpSwOff = mes.Measurement(lim['Off'], sen.o15VpSw)
        self.dmm_5VOff = mes.Measurement(lim['Off'], sen.o5V)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_Vbus = mes.Measurement(lim['Vbus'], sen.oVbus)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        mes = tester.measure
        d = logical_devices
        m = measurements

        # PowerUp: Min load, input AC, measure.
        ld1 = mes.LoadSubStep(
            ((d.dcl_Tec, 0.1), (d.dcl_15Vp, 1.0),
             (d.dcl_15Vpsw, 0.0), (d.dcl_5V, 5.0)),
            output=True)
        acs1 = mes.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=1.0)
        msr1 = mes.MeasureSubStep(
            (m.dmm_Vbus, m.dmm_TecOff, m.dmm_TecVmonOff, m.dmm_LddOff,
             m.dmm_IsVmonOff, m.dmm_15VOff, m.dmm_m15VOff, m.dmm_15VpOff,
             m.dmm_5VOff, m.dmm_15VpSwOff,  ), timeout=5)
        self.pwr_up = mes.Step((ld1, acs1, msr1))
