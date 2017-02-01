#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Final Test Program."""

import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_Input = tester.DCSource(devices['DCS1'])
        self.dcl_Output = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_Input.output(0.0, False)
        self.dcl_Output.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        sensor = tester.sensor
        self.o20V = sensor.Vdc(
            logical_devices.dmm, high=3, low=3, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsPowerLedGreen?'),
            caption=tester.translate('_2040_final', 'capPowerLed'))
        self.oYesNoDCOff = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsDcRedLedOff?'),
            caption=tester.translate('_2040_final', 'capDcLed'))
        self.oYesNoDCOn = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsDcRedLedOn?'),
            caption=tester.translate('_2040_final', 'capDcLed'))
        self.oYesNoACOff = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsAcRedLedOff?'),
            caption=tester.translate('_2040_final', 'capAcLed'))
        self.oYesNoACOn = sensor.YesNo(
            message=tester.translate('_2040_final', 'IsAcRedLedOn?'),
            caption=tester.translate('_2040_final', 'capAcLed'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_20V = tester.Measurement(limits['20V'], sense.o20V)
        self.dmm_20Vload = tester.Measurement(limits['20Vload'], sense.o20V)
        self.dmm_20Voff = tester.Measurement(limits['20Voff'], sense.o20V)
        self.ui_YesNoGreen = tester.Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoDCOff = tester.Measurement(limits['Notify'], sense.oYesNoDCOff)
        self.ui_YesNoDCOn = tester.Measurement(limits['Notify'], sense.oYesNoDCOn)
        self.ui_YesNoACOff = tester.Measurement(limits['Notify'], sense.oYesNoACOff)
        self.ui_YesNoACOn = tester.Measurement(limits['Notify'], sense.oYesNoACOn)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # DCPowerOn: Apply DC Input, measure.
        self.dcpwr_on = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Input, 10.0), ), output=True),
            tester.MeasureSubStep((m.dmm_20V, m.ui_YesNoGreen, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_Input, 35.0), )),
            tester.MeasureSubStep((m.dmm_20V, ), timeout=5),
            ))
        # DCLoad: Full load, measure, discharge, power off.
        self.full_load = tester.SubStep((
            tester.LoadSubStep(((d.dcl_Output, 2.0),), output=True),
            tester.MeasureSubStep(
                (m.dmm_20Vload, m.ui_YesNoDCOff, ), timeout=5),
            tester.DcSubStep(
                setting=((d.dcs_Input, 0.0), ), output=False, delay=5),
            ))
        # ACPowerOn: Apply AC Input, measure.
        self.acpwr_on = tester.SubStep((
            tester.LoadSubStep(((d.dcl_Output, 0.0),)),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=0.5),
            tester.MeasureSubStep((m.dmm_20V, ), timeout=5),
            ))
        # ACLoad: Peak load, measure, shutdown.
        self.peak_load = tester.SubStep((
            tester.LoadSubStep(((d.dcl_Output, 3.5),)),
            tester.MeasureSubStep(
                (m.dmm_20Vload, m.ui_YesNoACOff, ), timeout=5),
            tester.LoadSubStep(((d.dcl_Output, 4.05),)),
            tester.MeasureSubStep((m.dmm_20Voff, m.ui_YesNoACOn, ), timeout=5),
            ))
        # Recover: AC off, load off, AC on.
        self.recover = tester.SubStep((
            tester.AcSubStep(acs=d.acsource, voltage=0.0, delay=0.5),
            tester.MeasureSubStep((m.dmm_20Voff, ), timeout=5),
            tester.LoadSubStep(((d.dcl_Output, 0.0),)),
            tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5),
            tester.MeasureSubStep((m.dmm_20V, ), timeout=5),
            ))
