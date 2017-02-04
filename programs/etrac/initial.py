#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ETrac-II Initial Test Program."""

import os
import inspect
import tester
import share

PIC_HEX = 'etracII-2A.hex'

LIMITS = tester.testlimit.limitset((
    ('Vin', 1, 12.9, 13.1, None, None),
    ('Vin2', 1, 10.8, 12.8, None, None),
    ('5V', 1, 4.95, 5.05, None, None),
    ('5Vusb', 1, 4.75, 5.25, None, None),
    ('Vbat', 1, 8.316, 8.484, None, None),
    ))


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """ETrac-II Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Load', self._step_load),
            )
        self._limits = LIMITS
        global m, d, s, t
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

    def _step_power_up(self):
        """Apply input DC and measure voltages."""
        self.fifo_push(((s.oVin, 13.0), (s.oVin2, 12.0),
                         (s.o5V, 5.0), ))

        t.pwr_up.run()

    def _step_program(self):
        """Program the PIC micro."""
        d.program_pic.program()

    def _step_load(self):
        """Load and measure voltages."""
        self.fifo_push(((s.o5Vusb, 5.1), (s.oVbat, (8.45, 8.4)), ))

        t.load.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_Vin = tester.DCSource(devices['DCS1'])
        self.rla_SS = tester.Relay(devices['RLA1'])
        self.rla_Prog = tester.Relay(devices['RLA2'])
        self.rla_BattLoad = tester.Relay(devices['RLA3'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            PIC_HEX, folder, '16F1828', self.rla_Prog)

    def reset(self):
        """Reset instruments."""
        self.dcs_Vin.output(0.0, False)
        for rla in (self.rla_SS, self.rla_Prog, self.rla_BattLoad):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oVin2 = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.o5Vusb = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_Vin2 = Measurement(limits['Vin2'], sense.oVin2)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_5Vusb = Measurement(limits['5Vusb'], sense.o5Vusb)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:
        rly1 = tester.RelaySubStep(((d.rla_SS, True), ))
        dcs1 = tester.DcSubStep(setting=((d.dcs_Vin, 13.0),), output=True)
        msr1 = tester.MeasureSubStep(
            (m.dmm_Vin, m.dmm_Vin2, m.dmm_5V, ), timeout=10)
        self.pwr_up = tester.SubStep((rly1, dcs1, msr1))
        # Load:
        msr1 = tester.MeasureSubStep(
            (m.dmm_5Vusb, m.dmm_Vbat, ), timeout=10)
        rly1 = tester.RelaySubStep(((d.rla_BattLoad, True), ))
        msr2 = tester.MeasureSubStep((m.dmm_Vbat, ), timeout=10)
        self.load = tester.SubStep((msr1, rly1, msr2))
