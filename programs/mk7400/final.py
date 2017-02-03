#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MK7-400-1 Final Test Program."""

import tester

LIMITS = tester.testlimit.limitset((
    ('ACon', 1, 230, 250, None, None),
    ('ACoff', 1, 10, None, None, None),
    ('5V', 1, 4.75, 5.25, None, None),
    ('12Voff', 1, 0.5, None, None, None),
    ('12Von', 1, 12.0, 12.6, None, None),
    ('24Voff', 1, 0.5, None, None, None),
    ('24Von', 1, 23.4, 24.6, None, None),
    ('24V2off', 1, 0.5, None, None, None),
    ('24V2on', 1, 23.4, 24.6, None, None),
    ('PwrFailOff', 1, None, 11.0, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """MK7-400-1 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('FullLoad', self._step_full_load),
            tester.TestStep('115V', self._step_115v),
            tester.TestStep('Poweroff', self._step_power_off),
            )
        super().open(sequence)
        global m, d, s, t
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

    def _step_power_up(self):
        """
        Switch on unit at 240Vac, not enabled.

        Measure output voltages at min load.

        """
        self.fifo_push(((s.o5V, 5.1), (s.o12V, 0.0),
                         (s.o24V, 0.0), (s.o24V2, 0.0), ))
        t.pwr_up.run()

    def _step_power_on(self):
        """Enable outputs, measure voltages at min load."""
        self.fifo_push(
            ((s.o12V, 12.0), (s.o24V, 24.0), (s.o24V2, 0.0),
            (s.oPwrFail, 24.1), (s.o24V2, 24.0), (s.oYesNoMains, True),
            (s.oAux, 240.0), (s.oAuxSw, 240.0), ))
        t.pwr_on.run()

    def _step_full_load(self):
        """Measure outputs at full-load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o12V, 12.1), (s.o24V, 24.1), (s.o24V2, 24.2), ))
        t.full_load.run()

    def _step_115v(self):
        """Measure outputs at 115Vac in, full-load."""
        self.fifo_push(
            ((s.o5V, 5.1), (s.o12V, 12.1), (s.o24V, 24.1), (s.o24V2, 24.2), ))
        t.full_load_115.run()

    def _step_power_off(self):
        """Switch off unit, measure Aux and 24V voltages."""
        self.fifo_push(
            ((s.oNotifyPwrOff, True), (s.oAux, 0.0), (s.oAuxSw, 0.0),
             (s.o24V, 0.0), ))
        t.pwr_off.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])
        self.dcl_12V = tester.DCLoad(devices['DCL2'])
        self.dcl_24V2 = tester.DCLoad(devices['DCL3'])
        self.dcl_5V = tester.DCLoad(devices['DCL4'])
        self.rla_24V2off = tester.Relay(devices['RLA2'])
        self.rla_pson = tester.Relay(devices['RLA3'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for ld in (self.dcl_12V, self.dcl_24V, self.dcl_5V, self.dcl_24V2):
            ld.output(0.0, False)
        for rla in (self.rla_24V2off, self.rla_pson):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oAux = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oAuxSw = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.01)
        self.o5V = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self.o24V = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o24V2 = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.oPwrFail = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self.oYesNoMains = sensor.YesNo(
            message=tester.translate('mk7_final', 'IsSwitchLightOn?'),
            caption=tester.translate('mk7_final', 'capSwitchLight'))
        self.oNotifyPwrOff = sensor.Notify(
            message=tester.translate('mk7_final', 'msgSwitchOff'),
            caption=tester.translate('mk7_final', 'capSwitchOff'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
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
        rly1 = tester.RelaySubStep(((d.rla_24V2off, True), ))
        ld = tester.LoadSubStep(
            ((d.dcl_5V, 0.5), (d.dcl_12V, 0.5), (d.dcl_24V, 0.5),
             (d.dcl_24V2, 0.5), ), output=True)
        acs = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, output=True, delay=0.5)
        msr1 = tester.MeasureSubStep(
            (m.dmm_5V, m.dmm_24Voff, m.dmm_12Voff, m.dmm_24V2off, ), timeout=5)
        self.pwr_up = tester.SubStep((rly1, ld, acs, msr1, ))
        # PowerOn: Turn on, measure at min load.
        rly1 = tester.RelaySubStep(((d.rla_pson, True), ))
        msr1 = tester.MeasureSubStep(
            (m.dmm_24Von, m.dmm_12Von, m.dmm_24V2off, m.dmm_PwrFailOff, ),
            timeout=5)
        rly2 = tester.RelaySubStep(((d.rla_24V2off, False), ))
        msr2 = tester.MeasureSubStep(
            (m.dmm_24V2on, m.dmm_AuxOn, m.dmm_AuxSwOn, ), timeout=5)
        msr3 = tester.MeasureSubStep((m.ui_YesNoMains, ))
        self.pwr_on = tester.SubStep((rly1, msr1, rly2, msr2, msr3, ))
        # Full Load: Apply full load, measure.
        # 115Vac Full Load: 115Vac, measure.
        ld = tester.LoadSubStep(
            ((d.dcl_5V, 2.0), (d.dcl_12V, 10.0),
             (d.dcl_24V, 6.5), (d.dcl_24V2, 4.5), ))
        msr1 = tester.MeasureSubStep(
            (m.dmm_5V, m.dmm_24Von, m.dmm_12Von, m.dmm_24V2on, ), timeout=5)
        acs = tester.AcSubStep(acs=d.acsource, voltage=115.0, delay=0.5)
        self.full_load = tester.SubStep((ld, msr1, ))
        self.full_load_115 = tester.SubStep((acs, msr1, ))
        # PowerOff: Set min load, switch off, measure.
        ld = tester.LoadSubStep(
            ((d.dcl_5V, 0.5), (d.dcl_12V, 0.5),
             (d.dcl_24V, 0.5), (d.dcl_24V2, 0.5), ))
        msr1 = tester.MeasureSubStep(
            (m.ui_NotifyPwrOff, m.dmm_AuxOff, m.dmm_AuxSwOff,  m.dmm_24Voff, ))
        self.pwr_off = tester.SubStep((ld, msr1, ))
