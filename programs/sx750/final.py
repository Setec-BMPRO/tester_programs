#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Final Test Program."""

import time
from pydispatch import dispatcher
import tester

LIMITS = tester.testlimit.limitset((
    ('InRes', 1, 60000, 80000, None, None),
    ('IECoff', 1, 0.5, None, None, None),
    ('IEC', 1, 235, 245, None, None),
    ('5V', 1, 5.034, 5.177, None, None),
    ('12Voff', 1, 0.5, None, None, None),
    ('12Von', 1, 12.005, 12.495, None, None),
    ('24Von', 1, 23.647, 24.613, None, None),
    ('5Vfl', 1, 4.820, 5.380, None, None),
    ('12Vfl', 1, 11.270, 13.230, None, None),
    ('24Vfl', 1, 21.596, 26.663, None, None),
    ('PwrGood', 1, 0.5, None, None, None),
    ('AcFail', 1, 4.5, 5.5, None, None),
    ('Reg12V', 1, 0.5, 5.0, None, None),
    ('Reg24V', 1, 0.2, 5.0, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """SX-750 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('InputRes', self._step_inres),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('PowerOn', self._step_poweron),
            tester.TestStep('Load', self._step_load),
            )
        global d, s, m, t
        d = LogicalDevices(self._devices)
        s = Sensors(d)
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

    def _step_inres(self):
        """Verify that the hand loaded input discharge resistors are there."""
        self.fifo_push(((s.oInpRes, 70000), ))

        m.dmm_InpRes.measure(timeout=5)

    def _step_powerup(self):
        """Switch on unit at 240Vac, no load, not enabled."""
        self.fifo_push(
            ((s.oIec, (0.0, 240.0)), (s.o5v, 5.1), (s.o12v, 0.0),
             (s.oYesNoGreen, True)))

        t.pwr_up.run()

    def _step_poweron(self):
        """Enable all outputs and check that the LED goes blue."""
        self.fifo_push(
            ((s.oYesNoBlue, True), (s.o5v, 5.1), (s.oPwrGood, 0.1),
             (s.oAcFail, 5.1), ))

        t.pwr_on.run()

    def _step_load(self):
        """Measure outputs at load."""
        self.fifo_push(
            ((s.o5v, 5.1), (s.o12v, (12.2, 12.1)), (s.o24v, (24.2, 24.1)),
             (s.oPwrGood, 0.1), (s.oAcFail, 5.1), ))

        nl12v, nl24v = tester.MeasureGroup(
            (m.dmm_12von, m.dmm_24von, )).readings
        t.load.run()
        fl12v, fl24v = tester.MeasureGroup(
            (m.dmm_12vfl, m.dmm_24vfl, )).readings
        if self.running:
            reg12v = 100 * (nl12v - fl12v) / nl12v
            reg24v = 100 * (nl24v - fl24v) / nl24v
            s.oMir12v.store(reg12v)
            s.oMir24v.store(reg24v)
            tester.MeasureGroup((m.reg12v, m.reg24v, ))


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_12v = tester.DCLoad(devices['DCL1'])
        self.dcl_24v = tester.DCLoad(devices['DCL2'])
        self.dcl_5v = tester.DCLoad(devices['DCL3'])
        self.rla_PwrOn = tester.Relay(devices['RLA1'])

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
        sensor = tester.sensor
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
            message=tester.translate('sx750_final', 'IsLedGreen?'),
            caption=tester.translate('sx750_final', 'capLedGreen'))
        self.oYesNoBlue = sensor.YesNo(
            message=tester.translate('sx750_final', 'IsLedBlue?'),
            caption=tester.translate('sx750_final', 'capLedBlue'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMir12v.flush()
        self.oMir24v.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
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
        self.pwr_up = tester.SubStep((
            tester.LoadSubStep(
                ((d.dcl_5v, 0.0), (d.dcl_12v, 0.1), (d.dcl_24v, 0.1)),
                 output=True),
            tester.MeasureSubStep((m.dmm_Iecoff, ), timeout=5),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, frequency=50,
                output=True, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_Iec, m.dmm_5v, m.dmm_12voff, m.ui_YesNoGreen),
                 timeout=5),
            ))
        # PowerOn:
        self.pwr_on = tester.SubStep((
            tester.RelaySubStep(((d.rla_PwrOn, True), )),
            tester.MeasureSubStep(
                (m.ui_YesNoBlue, m.dmm_5v, m.dmm_PwrGood, m.dmm_AcFail, ),
                timeout=5),
            ))
        # Load: Apply loads, measure.
        self.load = tester.SubStep((
            tester.LoadSubStep(
                ((d.dcl_5v, 2.0), (d.dcl_12v, 32.0), (d.dcl_24v, 15.0)),
                output=True),
            tester.MeasureSubStep(
                (m.dmm_5vfl, m.dmm_PwrGood, m.dmm_AcFail, ), timeout=2),
            ))
