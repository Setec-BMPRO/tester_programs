#!/usr/bin/env python3
"""ATXG-450-2V Final Test Program."""

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
        # This DC Source controls the PS_ON signal (12V == Unit OFF)
        self.dcs_PsOn = dcsource.DCSource(devices['DCS1'])
        self.dcl_24V = dcload.DCLoad(devices['DCL1'])
        self.dcl_12V = dcload.DCLoad(devices['DCL2'])
        self.dcl_5V = dcload.DCLoad(devices['DCL3'])
        self.dcl_3V3 = dcload.DCLoad(devices['DCL4'])
        self.dcl_5Vsb = dcload.DCLoad(devices['DCL5'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Loads
        for ld in (self.dcl_24V, self.dcl_12V, self.dcl_5V,
                   self.dcl_3V3, self.dcl_5Vsb):
            ld.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oIec = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.o24V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.0001)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.o5Vsb = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.0001)
        self.on12V = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oPwrGood = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.oPwrFail = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('atxg450_2v_final', 'IsSwitchGreen?'),
            caption=translate('atxg450_2v_final', 'capSwitchGreen'))
        self.oYesNoFan = sensor.YesNo(
            message=translate('atxg450_2v_final', 'IsFanRunning?'),
            caption=translate('atxg450_2v_final', 'capFan'))
        self.o24Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_24V, sensor=self.o24V,
            detect_limit=(limits['24Vinocp'], ),
            start=17.5, stop=24.5, step=0.1, delay=0.1)
        self.o12Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_12V, sensor=self.o12V,
            detect_limit=(limits['12Vinocp'], ),
            start=19.5, stop=26.5, step=0.1, delay=0.1)
        self.o5Vocp = sensor.Ramp(
            stimulus=logical_devices.dcl_5V, sensor=self.o5V,
            detect_limit=(limits['5Vinocp'], ),
            start=19.5, stop=26.5, step=0.1, delay=0.1)
        self.o3V3ocp = sensor.Ramp(
            stimulus=logical_devices.dcl_3V3, sensor=self.o3V3,
            detect_limit=(limits['3V3inocp'], ),
            start=16.5, stop=26.5, step=0.1, delay=0.1)
        self.o5Vsbocp = sensor.Ramp(
            stimulus=logical_devices.dcl_5Vsb, sensor=self.o5Vsb,
            detect_limit=(limits['5Vsbinocp'], ),
            start=2.1, stop=4.7, step=0.1, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_5Vsb = Measurement(limits['5Vsb'], sense.o5Vsb)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V)
        self.dmm_5Voff = Measurement(limits['5Voff'], sense.o5V)
        self.dmm_3V3off = Measurement(limits['3V3off'], sense.o3V3)
        self.dmm_n12Voff = Measurement(limits['-12Voff'], sense.on12V)
        self.dmm_24Von = Measurement(limits['24Von'], sense.o24V)
        self.dmm_12Von = Measurement(limits['12Von'], sense.o12V)
        self.dmm_5Von = Measurement(limits['5Von'], sense.o5V)
        self.dmm_3V3on = Measurement(limits['3V3on'], sense.o3V3)
        self.dmm_n12Von = Measurement(limits['-12Von'], sense.on12V)
        self.dmm_PwrFailOff = Measurement(limits['PwrFailOff'], sense.oPwrFail)
        self.dmm_PwrGoodOff = Measurement(limits['PwrGoodOff'], sense.oPwrGood)
        self.dmm_PwrFailOn = Measurement(limits['PwrFailOn'], sense.oPwrFail)
        self.dmm_PwrGoodOn = Measurement(limits['PwrGoodOn'], sense.oPwrGood)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoFan = Measurement(limits['Notify'], sense.oYesNoFan)
        self.ramp_24Vocp = Measurement(limits['24Vocp'], sense.o24Vocp)
        self.ramp_12Vocp = Measurement(limits['12Vocp'], sense.o12Vocp)
        self.ramp_5Vocp = Measurement(limits['5Vocp'], sense.o5Vocp)
        self.ramp_3V3ocp = Measurement(limits['3V3ocp'], sense.o3V3ocp)
        self.ramp_5Vsbocp = Measurement(limits['5Vsbocp'], sense.o5Vsbocp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: Disable PS_ON, apply 240Vac, measure.
        dcs = DcSubStep(((d.dcs_PsOn, 12.0), ), output=True, delay=0.1)
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr = MeasureSubStep(
            (m.dmm_5Vsb, m.ui_YesNoGreen, m.dmm_24Voff, m.dmm_12Voff,
             m.dmm_5Voff, m.dmm_3V3off, m.dmm_n12Voff, m.dmm_PwrGoodOff,
             m.dmm_PwrFailOff), timeout=5)
        self.pwr_up = Step((dcs, acs, msr))

        # SwitchOn: Min load, enable PS_ON, measure.
        ld = LoadSubStep(((d.dcl_12V, 1.0), (d.dcl_24V, 1.0), (d.dcl_5V, 1.0)))
        dcs = DcSubStep(((d.dcs_PsOn, 0.0), ), output=True, delay=0.1)
        msr = MeasureSubStep(
            (m.dmm_24Von, m.dmm_12Von, m.dmm_5Von, m.dmm_3V3on, m.dmm_n12Von,
             m.dmm_PwrGoodOn, m.dmm_PwrFailOn, m.ui_YesNoFan), timeout=5)
        self.sw_on = Step((ld, dcs, msr))

        # Full Load: Apply full load, measure.
        ld = LoadSubStep(
            ((d.dcl_5Vsb, 1.0), (d.dcl_24V, 5.0), (d.dcl_5V, 10.0),
             (d.dcl_12V, 10.0), (d.dcl_3V3, 10.0)), delay=0.5)
        msr = MeasureSubStep(
            (m.dmm_5Vsb, m.dmm_24Von, m.dmm_12Von, m.dmm_5Von, m.dmm_3V3on,
             m.dmm_n12Von, m.dmm_PwrGoodOn, m.dmm_PwrFailOn), timeout=5)
        self.full_load = Step((ld, msr))

        # PowerFail: Switch AC off, measure.
        acs = AcSubStep(acs=d.acsource, voltage=0.0, output=False, delay=0.5)
        msr1 = MeasureSubStep((m.dmm_PwrFailOff, ))
        self.pwr_fail = Step((acs, msr1,))

        # Re-Start unit after OCP by using PS_ON.
        dcs1 = DcSubStep(((d.dcs_PsOn, 12.0), ), output=True, delay=0.5)
        dcs2 = DcSubStep(((d.dcs_PsOn, 0.0), ), output=True, delay=2.0)
        self.restart = Step((dcs1, dcs2,))
