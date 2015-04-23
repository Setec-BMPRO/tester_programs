#!/usr/bin/env python3
"""MK7-400-1 Final Test Program."""

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
        self.dcl_24V = dcload.DCLoad(devices['DCL1'])
        self.dcl_12V = dcload.DCLoad(devices['DCL2'])
        self.dcl_24V2 = dcload.DCLoad(devices['DCL3'])
        self.dcl_5V = dcload.DCLoad(devices['DCL4'])
        self.rla_24V2off = relay.Relay(devices['RLA2'])
        self.rla_pson = relay.Relay(devices['RLA3'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Loads
        for ld in (self.dcl_12V, self.dcl_24V, self.dcl_5V, self.dcl_24V2):
            ld.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_24V2off, self.rla_pson):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oAux = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oAuxSw = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.01)
        self.o5V = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self.o24V = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o24V2 = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.oPwrFail = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        tester.TranslationContext = 'mk7_final'
        self.oYesNoMains = sensor.YesNo(
            message=translate('IsSwitchLightOn?'),
            caption=translate('capSwitchLight'))
        self.oNotifyPwrOff = sensor.Notify(
            message=translate('msgSwitchOff'),
            caption=translate('capSwitchOff'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_AuxOn = Measurement(limits['ACon'], sense.oAux)
        self.dmm_AuxOff = Measurement(limits['ACoff'], sense.oAux)
        self.dmm_AuxSwOn = Measurement(limits['ACon'], sense.oAuxSw)
        self.dmm_AuxSwOff = Measurement(limits['ACoff'], sense.oAuxSw)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.dmm_24V2off = Measurement(limits['24V2off'], sense.o24V2)
        self.dmm_12Von = Measurement(limits['12Von'], sense.o12V)
        self.dmm_24Von = Measurement(limits['24Von'], sense.o24V)
        self.dmm_24V2on = Measurement(limits['24V2on'], sense.o24V2)
        self.dmm_PwrFailOff = Measurement(limits['PwrFailOff'], sense.oPwrFail)
        self.ui_YesNoMains = Measurement(limits['Notify'], sense.oYesNoMains)
        self.ui_NotifyPwrOff = Measurement(
            limits['Notify'], sense.oNotifyPwrOff)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 240Vac, set min load, measure.
        rly1 = RelaySubStep(((d.rla_24V2off, True), ))
        ld = LoadSubStep(
            ((d.dcl_5V, 0.5), (d.dcl_12V, 0.5), (d.dcl_24V, 0.5),
             (d.dcl_24V2, 0.5), ), output=True)
        acs = AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr1 = MeasureSubStep(
            (m.dmm_5V, m.dmm_24Voff, m.dmm_12Voff, m.dmm_24V2off, ), timeout=5)
        self.pwr_up = Step((rly1, ld, acs, msr1, ))
        # PowerOn: Turn on, measure at min load.
        rly1 = RelaySubStep(((d.rla_pson, True), ))
        msr1 = MeasureSubStep(
            (m.dmm_24Von, m.dmm_12Von, m.dmm_24V2off, m.dmm_PwrFailOff, ),
            timeout=5)
        rly2 = RelaySubStep(((d.rla_24V2off, False), ))
        msr2 = MeasureSubStep(
            (m.dmm_24V2on, m.dmm_AuxOn, m.dmm_AuxSwOn, ), timeout=5)
        msr3 = MeasureSubStep((m.ui_YesNoMains, ))
        self.pwr_on = Step((rly1, msr1, rly2, msr2, msr3, ))
        # Full Load: Apply full load, measure.
        # 115Vac Full Load: 115Vac, measure.
        ld = LoadSubStep(
            ((d.dcl_5V, 2.0), (d.dcl_12V, 10.0),
             (d.dcl_24V, 6.5), (d.dcl_24V2, 4.5), ))
        msr1 = MeasureSubStep(
            (m.dmm_5V, m.dmm_24Von, m.dmm_12Von, m.dmm_24V2on, ), timeout=5)
        acs = AcSubStep(acs=d.acsource, voltage=115.0, delay=0.5)
        self.full_load = Step((ld, msr1, ))
        self.full_load_115 = Step((acs, msr1, ))
        # PowerOff: Set min load, switch off, measure.
        ld = LoadSubStep(
            ((d.dcl_5V, 0.5), (d.dcl_12V, 0.5),
             (d.dcl_24V, 0.5), (d.dcl_24V2, 0.5), ))
        msr1 = MeasureSubStep(
            (m.ui_NotifyPwrOff, m.dmm_AuxOff, m.dmm_AuxSwOff,  m.dmm_24Voff, ))
        self.pwr_off = Step((ld, msr1, ))
