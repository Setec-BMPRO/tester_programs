#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15D-15 Final Test Program."""

import sensor
import tester

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Input = tester.DCSource(devices['DCS1'])
        self.dcl = tester.DCLoad(devices['DCL5'])
        self.rla_load = tester.Relay(devices['RLA2'])

    def reset(self):
        """Reset instruments."""
        self.dcs_Input.output(0.0, False)
        self.dcl.output(0.0, False)
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
            # Adds to a resistor load!


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_Voutfl = Measurement(limits['Voutfl'], sense.oVout)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.ui_YesNoYellowOff = Measurement(
            limits['Notify'], sense.oYesNoYellowOff)
        self.ui_NotifyYellow = Measurement(
            limits['Notify'], sense.oNotifyYellow)
        self.ui_YesNoYellowOn = Measurement(
            limits['Notify'], sense.oYesNoYellowOn)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply DC Input, measure.
        self.pwr_up = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Input, 12.0), ), output=True),
            tester.LoadSubStep(((d.dcl, 0.0), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_Vout, m.ui_YesNoGreen, m.ui_YesNoYellowOff,
                 m.ui_NotifyYellow,), timeout=5),
            ))
        # OCP:
        self.ocp = tester.SubStep((
            tester.RelaySubStep(((d.rla_load, True), )),
            tester.MeasureSubStep((m.ramp_OCP, ), timeout=5),
            tester.RelaySubStep(((d.rla_load, False), )),
            tester.MeasureSubStep((m.ui_YesNoYellowOn, m.dmm_Vout, ), timeout=5),
            ))
        # FullLoad: full load, measure, recover.
        self.full_load = tester.SubStep((
            tester.LoadSubStep(((d.dcl, 1.18), ), output=True),
            tester.MeasureSubStep((m.dmm_Voutfl, ), timeout=5),
            ))
        # Recover: Input off and on.
        self.recover = tester.SubStep((
            tester.LoadSubStep(((d.dcl, 0.0), )),
            tester.DcSubStep(setting=((d.dcs_Input, 0.0), ), delay=1),
            tester.DcSubStep(setting=((d.dcs_Input, 12.0), )),
            tester.MeasureSubStep((m.dmm_Vout, ), timeout=5),
            ))
        # PowerOff: Input DC off, discharge.
        self.pwr_off = tester.SubStep((
            tester.LoadSubStep(((d.dcl, 1.0), )),
            tester.DcSubStep(setting=((d.dcs_Input, 0.0), ), delay=2),
            ))
