#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2040 Initial Test Program."""

import time
import tester

LIMITS = tester.testlimit.limitset((
    ('VccAC', 1, 9.0, 16.5, None, None),
    ('VccDC', 1, 7.8, 14.0, None, None),
    ('VbusMin', 1, 120.0, 140.0, None, None),
    ('SDOff', 1, 19.0, 21.0, None, None),
    ('SDOn', 1, 5.0, None, None, None),
    ('ACmin', 1, 88.0, 92.0, None, None),
    ('ACtyp', 1, 238.0, 242.0, None, None),
    ('ACmax', 1, 263.0, 267.0, None, None),
    ('VoutExt', 1, 19.8, 20.2, None, None),
    ('Vout', 1, 19.6, 20.4, None, None),
    ('GreenOn', 1, 15.0, 20.0, None, None),
    ('RedDCOff', 1, 9.0, 15.0, None, None),
    ('RedDCOn', 1, 1.8, 3.5, None, None),
    ('RedACOff', 1, 9.0, 50.0, None, None),
    ('DCmin', 1, 9.0, 11.0, None, None),
    ('DCtyp', 1, 23.0, 26.0, None, None),
    ('DCmax', 1, 38.0, 42.0, None, None),
    ('OCP', 1, 3.5, 4.1, None, None),
    ('inOCP', 1, 19.0, None, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """2040 Initial Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence.

           @param physical_devices Physical instruments of the Tester

        """
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('SecCheck', self._step_sec_check),
            tester.TestStep('DCPowerOn', self._step_dcpower_on),
            tester.TestStep('ACPowerOn', self._step_acpower_on),
            )
        super().open(sequence)
        global d, s, m, t
        d = LogicalDevices(self._devices)
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

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.oLock, 10.0), ))

        m.dmm_Lock.measure(timeout=5)

    def _step_sec_check(self):
        """Apply External DC voltage to output and measure voltages."""
        self.fifo_push(((s.oVout, 20.0), (s.oSD, 20.0), (s.oGreen, 17.0), ))

        t.sec_chk.run()

    def _step_dcpower_on(self):
        """Test with DC power in.

        Power with DC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        self.fifo_push(
            ((s.oDCin, (10.0, 40.0, 25.0)), (s.oGreen, 17.0),
             (s.oRedDC, (12.0, 2.5)), (s.oVccDC, (12.0,) * 3),
             (s.oVout, (20.0, ) * 15 + (18.0, ), ), (s.oSD, 4.0),))

        t.dcpwr_on.run()

    def _step_acpower_on(self):
        """Test with AC power in.

        Power with AC Min/Max/Typ Inputs, measure voltages.
        Do an OCP check.

        """
        self.fifo_push(
            ((s.oACin, (90.0, 265.0, 240.0)), (s.oGreen, 17.0),
             (s.oRedAC, 12.0), (s.oVbus, (130.0, 340)),
             (s.oVccAC, (13.0,) * 3), (s.oVout, (20.0, ) * 15 + (18.0, ), ), ))

        t.acpwr_on.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_Vout = tester.DCSource(devices['DCS1'])
        dcs_dcin1 = tester.DCSource(devices['DCS2'])
        dcs_dcin2 = tester.DCSource(devices['DCS3'])
        dcs_dcin3 = tester.DCSource(devices['DCS4'])
        dcs_dcin4 = tester.DCSource(devices['DCS5'])
        self.dcs_dcin = tester.DCSourceParallel(
            (dcs_dcin1, dcs_dcin2, dcs_dcin3, dcs_dcin4, ))
        self.dcl_Vout = tester.DCLoad(devices['DCL4'])
        self.discharge = tester.Discharge(devices['DIS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_dcin, self.dcs_Vout):
            dcs.output(0.0, False)
        self.dcl_Vout.output(1.0)
        time.sleep(1)
        self.discharge.pulse()
        self.dcl_Vout.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oLock = sensor.Res(dmm, high=12, low=6, rng=10000, res=1)
        self.oVccAC = sensor.Vdc(dmm, high=2, low=5, rng=100, res=0.001)
        self.oVccDC = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self.oVbus = sensor.Vdc(dmm, high=3, low=5, rng=1000, res=0.01)
        self.oSD = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oACin = sensor.Vac(dmm, high=5, low=4, rng=1000, res=0.01)
        self.oVout = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.oGreen = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oRedDC = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.001)
        self.oRedAC = sensor.Vdc(dmm, high=1, low=5, rng=100, res=0.001)
        self.oDCin = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=3.2, stop=4.3, step=0.05, delay=0.15)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_Lock = tester.Measurement(limits['FixtureLock'], sense.oLock)
        self.dmm_VccAC = tester.Measurement(limits['VccAC'], sense.oVccAC)
        self.dmm_VccDC = tester.Measurement(limits['VccDC'], sense.oVccDC)
        self.dmm_VbusMin = tester.Measurement(limits['VbusMin'], sense.oVbus)
        self.dmm_SDOff = tester.Measurement(limits['SDOff'], sense.oSD)
        self.dmm_SDOn = tester.Measurement(limits['SDOn'], sense.oSD)
        self.dmm_ACmin = tester.Measurement(limits['ACmin'], sense.oACin)
        self.dmm_ACtyp = tester.Measurement(limits['ACtyp'], sense.oACin)
        self.dmm_ACmax = tester.Measurement(limits['ACmax'], sense.oACin)
        self.dmm_VoutExt = tester.Measurement(limits['VoutExt'], sense.oVout)
        self.dmm_Vout = tester.Measurement(limits['Vout'], sense.oVout)
        self.dmm_GreenOn = tester.Measurement(limits['GreenOn'], sense.oGreen)
        self.dmm_RedDCOff = tester.Measurement(limits['RedDCOff'], sense.oRedDC)
        self.dmm_RedDCOn = tester.Measurement(limits['RedDCOn'], sense.oRedDC)
        self.dmm_RedACOff = tester.Measurement(limits['RedACOff'], sense.oRedAC)
        self.dmm_DCmin = tester.Measurement(limits['DCmin'], sense.oDCin)
        self.dmm_DCtyp = tester.Measurement(limits['DCtyp'], sense.oDCin)
        self.dmm_DCmax = tester.Measurement(limits['DCmax'], sense.oDCin)
        self.ramp_OCP = tester.Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # SecCheck: Apply Ext Vout, measure.
        self.sec_chk = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Vout, 20.0), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_VoutExt, m.dmm_SDOff, m.dmm_GreenOn, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_Vout, 0.0), )),
            ))
        # DCPowerOn: Apply DC power, measure, OCP.
        self.dcpwr_on = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_dcin, 10.25), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_DCmin, m.dmm_VccDC, m.dmm_Vout,
                 m.dmm_GreenOn, m.dmm_RedDCOff), timeout=5),
            tester.LoadSubStep(((d.dcl_Vout, 1.0), ), output=True, delay=1.0),
            tester.MeasureSubStep((m.dmm_Vout, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_dcin, 40.0), )),
            tester.MeasureSubStep(
                (m.dmm_DCmax, m.dmm_VccDC, m.dmm_Vout, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_dcin, 25.0), )),
            tester.MeasureSubStep(
                (m.dmm_DCtyp, m.dmm_VccDC, m.dmm_Vout, m.ramp_OCP), timeout=5),
            tester.LoadSubStep(((d.dcl_Vout, 4.1), ), delay=0.5),
            tester.MeasureSubStep((m.dmm_SDOn, m.dmm_RedDCOn, ), timeout=5),
            tester.LoadSubStep(((d.dcl_Vout, 0.0), )),
            tester.DcSubStep(
                setting=((d.dcs_dcin, 0.0), ), output=False, delay=2),
            ))
        # ACPowerOn: Apply AC power, measure, OCP.
        self.acpwr_on = tester.SubStep((
            tester.AcSubStep(
                acs=d.acsource, voltage=90.0, output=True, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_ACmin, m.dmm_VbusMin, m.dmm_VccAC, m.dmm_Vout,
                 m.dmm_GreenOn, m.dmm_RedACOff), timeout=15),
            tester.LoadSubStep(((d.dcl_Vout, 2.0), ), delay=1.0),
            tester.MeasureSubStep((m.dmm_Vout, ), timeout=5),
            tester.AcSubStep(acs=d.acsource, voltage=265.0, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_ACmax, m.dmm_VccAC, m.dmm_Vout, ), timeout=5),
            tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5),
            tester.MeasureSubStep(
                (m.dmm_ACtyp, m.dmm_VccAC, m.dmm_Vout, m.ramp_OCP), timeout=5),
            ))
