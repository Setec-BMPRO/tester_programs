#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C15A-15 Initial Test Program."""

import tester
from tester.testlimit import lim_hilo, lim_hilo_percent, lim_hi, lim_lo

LIMITS = tester.testlimit.limitset((
    lim_hilo('AcMin', 85, 95),
    lim_hilo('VbusMin', 120, 135),
    lim_hilo('VccMin', 7, 14),
    lim_hilo('Ac', 230, 245),
    lim_hilo('Vbus', 330, 350),
    lim_hilo('Vcc', 10, 14),
    lim_hi('LedOn', 6.5),
    lim_lo('LedOff', 0.5),
    lim_hilo_percent('Vout', 15.5, 2.0),
    lim_hilo('OCP_Range', 0.9, 1.4),
    lim_lo('inOCP', 15.2),
    lim_hilo('OCP', 1.05, 1.35),
    lim_hilo('VoutOcp', 5, 16),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """C15A-15 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('Power90', self._step_power_90),
            tester.TestStep('Power240', self._step_power_240),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('PowerOff', self._step_power_off),
            )
        self._limits = LIMITS
        global d, s, m, t
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_power_90(self):
        """Power up at 90Vac."""
        self.fifo_push(
            ((s.vin, 90.0), (s.vbus, 130), (s.vcc, 9), (s.vout, 15.5),
             (s.green, 11), (s.yellow, 0.2),))
        t.pwr_90.run()

    def _step_power_240(self):
        """Power up at 240Vac."""
        self.fifo_push(
            ((s.vin, 240.0), (s.vbus, 340), (s.vcc, 12), (s.vout, 15.5),
             (s.green, 11), (s.yellow, 0.2),))
        t.pwr_240.run()

    def _step_ocp(self):
        """Measure OCP."""
        self.fifo_push(
            ((s.vout, (15.5, ) * 15 + (13.5, ), ),
             (s.yellow, 8), (s.green, 9), (s.vout, (10, 15.5)), ))
        t.ocp.run()

    def _step_power_off(self):
        """Input AC off and discharge."""
        t.pwr_off.run()


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
        self.acsource.reset()
        self.dcl.output(0.0, False)
        self.rla_load.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
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
