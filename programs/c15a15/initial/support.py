#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Initial Test Program."""

import sensor
import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl = tester.DCLoad(devices['DCL5'])
        self.rla_load = tester.Relay(devices['RLA2'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(0.0, False)
        self.rla_load.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.vin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.vbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self.vcc = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self.green = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self.yellow = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self.vout = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl, sensor=self.vout,
            detect_limit=(limits['inOCP'], ),
            start=0.9, stop=1.4, step=0.02, delay=0.5)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_vin90 = Measurement(limits['AcMin'], sense.vin)
        self.dmm_vin = Measurement(limits['Ac'], sense.vin)
        self.dmm_vbus90 = Measurement(limits['VbusMin'], sense.vbus)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.vbus)
        self.dmm_vcc90 = Measurement(limits['VccMin'], sense.vcc)
        self.dmm_vcc = Measurement(limits['Vcc'], sense.vcc)
        self.dmm_green_on = Measurement(limits['LedOn'], sense.green)
        self.dmm_yellow_off = Measurement(limits['LedOff'], sense.yellow)
        self.dmm_yellow_on = Measurement(limits['LedOn'], sense.yellow)
        self.dmm_vout = Measurement(limits['Vout'], sense.vout)
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
        self.dmm_vout_ocp = Measurement(limits['VoutOcp'], sense.vout)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 90Vac, measure.
        self.pwr_90 = tester.SubStep((
            tester.AcSubStep(acs=d.acsource, voltage=90.0, output=True, delay=0.5),
            tester.LoadSubStep(((d.dcl, 0.0), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_vin90, m.dmm_vbus90, m.dmm_vcc90, m.dmm_vout,
                 m.dmm_green_on, m.dmm_yellow_off),
                timeout=5),
            ))
        # PowerUp: Apply 240Vac, measure.
        self.pwr_240 = tester.SubStep((
            tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_vin, m.dmm_vbus, m.dmm_vcc, m.dmm_vout,
                 m.dmm_green_on, m.dmm_yellow_off),
                timeout=5),
            ))
        # OCP:
        self.ocp = tester.SubStep((
            tester.LoadSubStep(((d.dcl, 0.9), )),
            tester.MeasureSubStep((m.dmm_vout, m.ramp_ocp)),
            tester.LoadSubStep(((d.dcl, 0.0), )),
            tester.RelaySubStep(((d.rla_load, True), ), delay=1.0),
            tester.MeasureSubStep(
                (m.dmm_yellow_on, m.dmm_green_on, m.dmm_vout_ocp)),
            tester.RelaySubStep(((d.rla_load, False), )),
            tester.MeasureSubStep((m.dmm_vout, ), timeout=2.0),
            ))
        # PowerOff:
        self.pwr_off = tester.SubStep((
            tester.LoadSubStep(((d.dcl, 1.0),)),
            tester.AcSubStep(acs=d.acsource, voltage=0.0, output=False, delay=2),
            ))
