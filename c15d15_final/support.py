#!/usr/bin/env python3
"""C15D-15 Final Test Program."""

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
        self.dmm = tester.devlogical.dmm.DMM(devices['DMM'])
        self.dcs_Input = dcsource.DCSource(devices['DCS1'])
        self.dcl = dcload.DCLoad(devices['DCL5'])
        self.rla_load = relay.Relay(devices['RLA2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Source
        self.dcs_Input.output(0.0, False)
        # Switch off DC Load
        self.dcl.output(0.0, False)
        # Switch off all Relays
        self.rla_load.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oVout = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('c15d15_final', 'IsPowerLedGreen?'),
            caption=translate('c15d15_final', 'capPowerLed'))
        self.oYesNoYellowOff = sensor.YesNo(
            message=translate('c15d15_final', 'IsYellowLedOff?'),
            caption=translate('c15d15_final', 'capOutputLed'))
        self.oNotifyYellow = sensor.Notify(
            message=translate('c15d15_final', 'WatchYellowLed'),
            caption=translate('c15d15_final', 'capOutputLed'))
        self.oYesNoYellowOn = sensor.YesNo(
            message=translate('c15d15_final', 'IsYellowLedOn?'),
            caption=translate('c15d15_final', 'capOutputLed'))
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=0.0, stop=0.5, step=0.05, delay=0.2)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.dmm_Vout = Measurement(
            limits['Vout'], sense.oVout)
        self.dmm_Voutfl = Measurement(
            limits['Voutfl'], sense.oVout)
        self.ui_YesNoGreen = Measurement(
            limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoYellowOff = Measurement(
            limits['Notify'], sense.oYesNoYellowOff)
        self.ui_NotifyYellow = Measurement(
            limits['Notify'], sense.oNotifyYellow)
        self.ui_YesNoYellowOn = Measurement(
            limits['Notify'], sense.oYesNoYellowOn)
        self.ramp_OCP = Measurement(
            limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements

        # PowerUp: Apply DC Input, measure.
        dcs = DcSubStep(setting=((d.dcs_Input, 12.0), ), output=True)
        ld = LoadSubStep(((d.dcl, 0.0), ), output=True)
        msr = MeasureSubStep(
            (m.dmm_Vout, m.ui_YesNoGreen, m.ui_YesNoYellowOff,
             m.ui_NotifyYellow,), timeout=5)
        self.pwr_up = Step((dcs, ld, msr))

        # OCP:
        rly1 = RelaySubStep(((d.rla_load, True), ))
        msr1 = MeasureSubStep((m.ramp_OCP, ), timeout=5)
        rly2 = RelaySubStep(((d.rla_load, False), ))
        msr2 = MeasureSubStep((m.ui_YesNoYellowOn, m.dmm_Vout, ), timeout=5)
        self.ocp = Step((rly1, msr1, rly2, msr2))

        # FullLoad: full load, measure, recover.
        ld = LoadSubStep(((d.dcl, 1.18), ), output=True)
        msr = MeasureSubStep((m.dmm_Voutfl, ), timeout=5)
        self.full_load = Step((ld, msr))

        # Recover: Input off and on.
        ld = LoadSubStep(((d.dcl, 0.0), ))
        dcs1 = DcSubStep(setting=((d.dcs_Input, 0.0), ), delay=1)
        dcs2 = DcSubStep(setting=((d.dcs_Input, 12.0), ))
        msr = MeasureSubStep((m.dmm_Vout, ), timeout=5)
        self.recover = Step((ld, dcs1, dcs2, msr))

        # PowerOff: Input DC off, discharge.
        ld = LoadSubStep(((d.dcl, 1.0), ))
        dcs = DcSubStep(setting=((d.dcs_Input, 0.0), ), delay=2)
        self.pwr_off = Step((ld, dcs))
