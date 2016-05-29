#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Initial Test Program."""

import time

import sensor
import tester

from . import msp


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_VccBias = tester.DCSource(devices['DCS1']) # Powers MSP430
        self.dcs_RS232 = tester.DCSource(devices['DCS2']) # Powers bootloader interface
        self.dcl_Vout = tester.DCLoad(devices['DCL1'])
        self.dcl_Vbat = tester.DCLoad(devices['DCL2'])
        self.rla_Prog = tester.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_Vout.output(2.0)
        self.dcl_Vbat.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_VccBias, self.dcs_RS232):
            dcs.output(0.0, False)
        for ld in (self.dcl_Vout, self.dcl_Vbat, ):
            ld.output(0.0, False)
        self.rla_Prog.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, mspdev):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm

        self.Lock = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self.oVac = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.oVccPri = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self.oVccBias = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self.oAlarm = sensor.Res(dmm, high=9, low=5, rng=100, res=0.001)
        self.oVout = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
#        self.oRed = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
#        self.oGreen = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)

        self.oMsp_Status = msp.Sensor(mspdev, 'MSP-NvStatus')
        self.oMsp_Vout = msp.Sensor(mspdev, 'MSP-Vout')


        ocp_start, ocp_stop = limits['BattOCPramp'].limit
        self.oBattOCP = sensor.Ramp(stimulus=logical_devices.dcl_Vbat,
                                    sensor=self.oVbat,
                                    detect_limit=(limits['inOCP'], ),
                                    start=ocp_start, stop=ocp_stop, step=0.05,
                                    delay=0.05)

        ocp_start, ocp_stop = limits['OutOCPramp'].limit
        self.oOutOCP = sensor.Ramp(stimulus=logical_devices.dcl_Vout,
                                    sensor=self.oVout,
                                    detect_limit=(limits['inOCP'], ),
                                    start=ocp_start, stop=ocp_stop, step=0.05,
                                    delay=0.05, reset=False)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        lim = limits
        sen = sense

        self.dmm_Lock = Measurement(lim['FixtureLock'], sen.Lock)
        self.dmm_VccBiasExt = Measurement(lim['VccBiasExt'], sen.oVccBias)
        self.dmm_Vac = Measurement(lim['Vac'], sen.oVac)
        self.dmm_Vbus = Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_VccPri = Measurement(lim['VccPri'], sen.oVccPri)
        self.dmm_VccBias = Measurement(lim['VccBias'], sen.oVccBias)
        self.dmm_VbatOff = Measurement(lim['VbatOff'], sen.oVbat)
        self.dmm_AlarmClosed = Measurement(lim['AlarmClosed'], sen.oAlarm)
        self.dmm_AlarmOpen = Measurement(lim['AlarmOpen'], sen.oAlarm)
        self.dmm_Vout = Measurement(lim['VoutPreCal'], sen.oVout)
        self.msp_Status = Measurement(lim['Status 0'], sen.oMsp_Status)
        self.msp_Vout = Measurement(lim['MspVout'], sen.oMsp_Vout)
        self.ramp_BattOCP = Measurement(lim['BattOCP'], sen.oBattOCP)
        self.ramp_OutOCP = Measurement(lim['OutOCP'], sen.oOutOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # ProgSetup:
        dcs1 = tester.DcSubStep(setting=((d.dcs_RS232, 9.0),
                            (d.dcs_VccBias, 15.0), ), output=True, delay=1)
        msr1 = tester.MeasureSubStep((m.dmm_VccBiasExt, ), timeout=5)
        self.prog_setup = tester.SubStep((dcs1, msr1))
        # PowerUp: Apply 240Vac, set min load, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True,
                                  delay=1.0)
        ld1 = tester.LoadSubStep(((d.dcl_Vbat, 0.1), ), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_Vac, m.dmm_Vbus, m.dmm_VccPri,
                                   m.dmm_VccBias, m.dmm_VbatOff,
                                   m.dmm_AlarmClosed, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl_Vbat, 0.0), ))
        self.pwr_up = tester.SubStep((acs1, ld1, msr1, ld2))
