#!/usr/bin/env python3
"""GENIUS-II and GENIUS-II-H Final Test Program."""

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor
translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        # This DC Source simulates the battery voltage
        self.dcs_Vbat = dcsource.DCSource(devices['DCS1'])
        dcl_vout = dcload.DCLoad(devices['DCL1'])
        dcl_vbat = dcload.DCLoad(devices['DCL3'])
        self.dcl = dcload.DCLoadParallel(((dcl_vout, 29), (dcl_vbat, 14)))
        self.dclh = dcload.DCLoadParallel(((dcl_vout, 5), (dcl_vbat, 30)))
        self.rla_RemoteSw = relay.Relay(devices['RLA1'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Loads
        self.dcl.output(0.0)
        # Switch off DC Source
        self.dcs_Vbat.output(0.0, False)
        # Switch off Relay
        self.rla_RemoteSw.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dcl = logical_devices.dcl
        dclh = logical_devices.dclh
        self.oInpRes = sensor.Res(dmm, high=1, low=1, rng=1000000, res=1)
        self.oVout = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=dcl, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)
        self.oOCP_H = sensor.Ramp(
            stimulus=dclh, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)
        self.oYesNoFuseOut = sensor.YesNo(
            message=translate(
                'geniusII_final', 'RemoveBattFuseIsLedRedFlashing?'),
            caption=translate('geniusII_final', 'capLedRed'))
        self.oYesNoFuseIn = sensor.YesNo(
            message=translate(
                'geniusII_final', 'ReplaceBattFuseIsLedGreen?'),
            caption=translate('geniusII_final', 'capLedRed'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_InpRes = Measurement(limits['InRes'], sense.oInpRes)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_VoutOff = Measurement(limits['VoutOff'], sense.oVout)
        self.dmm_VoutStartup = Measurement(limits['VoutStartup'], sense.oVout)
        self.dmm_VoutExt = Measurement(limits['ExtBatt'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_VbatOff = Measurement(limits['VbatOff'], sense.oVbat)
        self.dmm_VbatExt = Measurement(limits['ExtBatt'], sense.oVbat)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ramp_OCP_H = Measurement(limits['OCP'], sense.oOCP_H)
        self.ui_YesNoFuseOut = Measurement(
            limits['Notify'], sense.oYesNoFuseOut)
        self.ui_YesNoFuseIn = Measurement(limits['Notify'], sense.oYesNoFuseIn)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerOn: 240Vac, wait for Vout to start, measure.
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True)
        msr1 = MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=10)
        self.pwr_on = Step((acs1, msr1))
        # Shutdown: Apply overload to shutdown, recovery.
        ld1 = LoadSubStep(((d.dcl, 47.0), ), output=True)
        ld2 = LoadSubStep(((d.dclh, 47.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_VoutOff, ), timeout=10)
        ld3 = LoadSubStep(((d.dcl, 0.0), ), )
        ld4 = LoadSubStep(((d.dclh, 0.0), ), )
        msr2 = MeasureSubStep(
            (m.dmm_VoutStartup, m.dmm_Vout, m.dmm_Vbat,), timeout=10)
        self.shdn = Step((ld1, msr1, ld3, msr2))
        self.shdnH = Step((ld2, msr1, ld4, msr2))
        # RemoteSw: load, measure.
        acs1 = AcSubStep(acs=d.acsource, voltage=0.0)
        ld1 = LoadSubStep(((d.dcl, 2.0), ), delay=1)
        ld2 = LoadSubStep(((d.dcl, 0.1), ))
        dcs1 = DcSubStep(setting=((d.dcs_Vbat, 12.6),), output=True)
        msr1 = MeasureSubStep((m.dmm_VbatExt, m.dmm_VoutExt, ), timeout=5)
        rly1 = RelaySubStep(((d.rla_RemoteSw, True), ))
        msr2 = MeasureSubStep((m.dmm_VoutOff, ), timeout=10)
        rly2 = RelaySubStep(((d.rla_RemoteSw, False), ))
        msr3 = MeasureSubStep((m.dmm_VoutExt, ), timeout=5)
        self.remote_sw = Step(
            (acs1, ld1, ld2, dcs1, msr1, rly1, msr2, rly2, msr3))
