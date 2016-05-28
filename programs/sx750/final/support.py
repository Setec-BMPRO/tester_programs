#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Final Test Program."""

import time
from pydispatch import dispatcher

import sensor
import tester
from tester.devlogical import *
from tester.measure import *

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcl_12v = dcload.DCLoad(devices['DCL1'])
        self.dcl_24v = dcload.DCLoad(devices['DCL2'])
        self.dcl_5v = dcload.DCLoad(devices['DCL3'])
        self.rla_PwrOn = relay.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_12v.output(10)
        time.sleep(0.5)
        for ld in (self.dcl_12v, self.dcl_24v, self.dcl_5v):
            ld.output(0.0, output=False)
        self.rla_PwrOn.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oMir12v = sensor.Mirror()
        self.oMir24v = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.oInpRes = sensor.Res(dmm, high=1, low=1, rng=1000000, res=1)
        self.oIec = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.o5v = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.0001)
        self.o12v = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o24v = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oPwrGood = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self.oAcFail = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('sx750_final', 'IsLedGreen?'),
            caption=translate('sx750_final', 'capLedGreen'))
        self.oYesNoBlue = sensor.YesNo(
            message=translate('sx750_final', 'IsLedBlue?'),
            caption=translate('sx750_final', 'capLedBlue'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMir12v.flush()
        self.oMir24v.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.reg12v = Measurement(limits['Reg12V'], sense.oMir12v)
        self.reg24v = Measurement(limits['Reg24V'], sense.oMir24v)
        self.dmm_InpRes = Measurement(limits['InRes'], sense.oInpRes)
        self.dmm_Iecoff = Measurement(limits['IECoff'], sense.oIec)
        self.dmm_Iec = Measurement(limits['IEC'], sense.oIec)
        self.dmm_5v = Measurement(limits['5V'], sense.o5v)
        self.dmm_12voff = Measurement(limits['12Voff'], sense.o12v)
        self.dmm_12von = Measurement(limits['12Von'], sense.o12v)
        self.dmm_24von = Measurement(limits['24Von'], sense.o24v)
        self.dmm_PwrGood = Measurement(limits['PwrGood'], sense.oPwrGood)
        self.dmm_AcFail = Measurement(limits['AcFail'], sense.oAcFail)
        self.dmm_5vfl = Measurement(limits['5Vfl'], sense.o5v)
        self.dmm_12vfl = Measurement(limits['12Vfl'], sense.o12v)
        self.dmm_24vfl = Measurement(limits['24Vfl'], sense.o24v)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoBlue = Measurement(limits['Notify'], sense.oYesNoBlue)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: 240Vac, measure.
        self.pwr_up = Step((
            LoadSubStep(
                ((d.dcl_5v, 0.0), (d.dcl_12v, 0.1), (d.dcl_24v, 0.1)),
                 output=True),
            MeasureSubStep((m.dmm_Iecoff, ), timeout=5),
            AcSubStep(
                acs=d.acsource, voltage=240.0, frequency=50,
                output=True, delay=0.5),
            MeasureSubStep(
                (m.dmm_Iec, m.dmm_5v, m.dmm_12voff, m.ui_YesNoGreen),
                 timeout=5),
            ))
        # PowerOn:
        self.pwr_on = Step((
            RelaySubStep(((d.rla_PwrOn, True), )),
            MeasureSubStep(
                (m.ui_YesNoBlue, m.dmm_5v, m.dmm_PwrGood, m.dmm_AcFail, ),
                timeout=5),
            ))
        # Load: Apply loads, measure.
        self.load = Step((
            LoadSubStep(
                ((d.dcl_5v, 2.0), (d.dcl_12v, 32.0), (d.dcl_24v, 15.0)),
                output=True),
            MeasureSubStep(
                (m.dmm_5vfl, m.dmm_PwrGood, m.dmm_AcFail, ), timeout=2),
            ))
