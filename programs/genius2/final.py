#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final Test Program for GENIUS-II and GENIUS-II-H."""

import tester

LIMITS_STD = tester.testlimit.limitset((
    ('InRes', 1, 80000, 170000, None, None),
    ('Vout', 1, 13.575, 13.725, None, None),
    ('VoutOff', 1, -0.5, 2.0, None, None),
    ('VoutStartup', 1, 13.60, 14.10, None, None),
    ('Vbat', 1, 13.575, 13.725, None, None),
    ('VbatOff', 1, -0.5, 1, None, None),
    ('ExtBatt', 1, 11.5, 12.8, None, None),
    ('InOCP', 1, 13.24, None, None, None),
    ('OCP', 1, 34.0, 43.0, None, None),
    ('MaxBattLoad', 1, 15.0, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

LIMITS_H = tester.testlimit.limitset((
    ('InRes', 1, 80000, 170000, None, None),
    ('Vout', 1, 13.575, 13.725, None, None),
    ('VoutOff', 1, -0.5, 2.0, None, None),
    ('VoutStartup', 1, 13.60, 14.10, None, None),
    ('Vbat', 1, 13.575, 13.725, None, None),
    ('VbatOff', 1, -0.5, 1, None, None),
    ('ExtBatt', 1, 11.5, 12.8, None, None),
    ('InOCP', 1, 13.24, None, None, None),
    ('OCP', 1, 34.0, 43.0, None, None),
    ('MaxBattLoad', 1, 30.0, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

LIMITS = {      # Test limit selection keyed by program parameter
    None: LIMITS_STD,
    'STD': LIMITS_STD,
    'H': LIMITS_H,
    }

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """GENIUS-II Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('InputRes', self._step_inres),
            tester.TestStep('PowerOn', self._step_poweron),
            tester.TestStep('BattFuse', self._step_battfuse),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            )
        self._limits = LIMITS[self.parameter]
        self._isH = (self.parameter == 'H')
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

    def _step_inres(self):
        """Verify that the hand loaded input discharge resistors are there."""
        self.fifo_push(((s.oInpRes, 135000), ))

        m.dmm_InpRes.measure(timeout=5)

    def _step_poweron(self):
        """Switch on unit at 240Vac, no load."""
        self.fifo_push(((s.oVout, 13.6), (s.oVbat, 13.6)))

        t.pwr_on.run()

    def _step_battfuse(self):
        """Remove and insert battery fuse, check red LED."""
        self.fifo_push(((s.oYesNoFuseOut, True), (s.oVbat, 0.0),
                        (s.oYesNoFuseIn, True), (s.oVout, 13.6)))
        tester.MeasureGroup(
            (m.ui_YesNoFuseOut, m.dmm_VbatOff, m.ui_YesNoFuseIn, m.dmm_Vout),
            timeout=5)

    def _step_ocp(self):
        """
        Ramp up load until OCP.

        Shutdown and recover.

        """
        self.fifo_push(((s.oVout, (13.5, ) * 11 + (13.0, ), ),
                        (s.oVout, (0.1, 13.6, 13.6)), (s.oVbat, 13.6)))
        d.dcl.output(0.0, output=True)
        d.dcl.binary(0.0, 32.0, 5.0)
        if self._isH:
            m.ramp_OCP_H.measure()
            t.shdnH.run()
        else:
            m.ramp_OCP.measure()
            t.shdn.run()

    def _step_remote_sw(self):
        """
        Switch off AC, apply external Vbat.

        Check function of remote switch.

        """
        self.fifo_push(((s.oVbat, 12.0), (s.oVout, (12.0, 0.0, 12.0)), ))
        t.remote_sw.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        # This DC Source simulates the battery voltage
        self.dcs_Vbat = tester.DCSource(devices['DCS1'])
        dcl_vout = tester.DCLoad(devices['DCL1'])
        dcl_vbat = tester.DCLoad(devices['DCL3'])
        self.dcl = tester.DCLoadParallel(((dcl_vout, 29), (dcl_vbat, 14)))
        self.dclh = tester.DCLoadParallel(((dcl_vout, 5), (dcl_vbat, 30)))
        self.rla_RemoteSw = tester.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.reset()
        self.dcl.output(0.0)
        self.dcs_Vbat.output(0.0, False)
        self.rla_RemoteSw.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dcl = logical_devices.dcl
        dclh = logical_devices.dclh
        sensor = tester.sensor
        self.oInpRes = sensor.Res(dmm, high=1, low=1, rng=1000000, res=1)
        self.oVout = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=dcl, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)
        self.oOCP_H = sensor.Ramp(
            stimulus=dclh, sensor=self.oVout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)
        self.oYesNoFuseOut = sensor.YesNo(
            message=tester.translate(
                'geniusII_final', 'RemoveBattFuseIsLedRedFlashing?'),
            caption=tester.translate('geniusII_final', 'capLedRed'))
        self.oYesNoFuseIn = sensor.YesNo(
            message=tester.translate(
                'geniusII_final', 'ReplaceBattFuseIsLedGreen?'),
            caption=tester.translate('geniusII_final', 'capLedRed'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_InpRes = Measurement(limits['InRes'], sense.oInpRes)
        self.dmm_Vout = Measurement(limits['Vout'], sense.oVout)
        self.dmm_VoutOff = Measurement(limits['VoutOff'], sense.oVout)
        self.dmm_VoutStartup = Measurement(limits['VoutStartup'], sense.oVout)
        self.dmm_VoutExt = Measurement(limits['ExtBatt'], sense.oVout)
        self.dmm_Vbat = Measurement(limits['Vbat'], sense.oVbat)
        self.dmm_VbatOff = Measurement(limits['VbatOff'], sense.oVbat)
        self.dmm_VbatExt = Measurement(limits['ExtBatt'], sense.oVbat)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ramp_OCP_H = Measurement(limits['OCP'], sense.oOCP_H)
        self.ui_YesNoFuseOut = Measurement(
            limits['Notify'], sense.oYesNoFuseOut)
        self.ui_YesNoFuseIn = Measurement(limits['Notify'], sense.oYesNoFuseIn)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerOn: 240Vac, wait for Vout to start, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True)
        msr1 = tester.MeasureSubStep((m.dmm_Vout, m.dmm_Vbat), timeout=10)
        self.pwr_on = tester.SubStep((acs1, msr1))
        # Shutdown: Apply overload to shutdown, recovery.
        ld1 = tester.LoadSubStep(((d.dcl, 47.0), ), output=True)
        ld2 = tester.LoadSubStep(((d.dclh, 47.0), ), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_VoutOff, ), timeout=10)
        ld3 = tester.LoadSubStep(((d.dcl, 0.0), ), )
        ld4 = tester.LoadSubStep(((d.dclh, 0.0), ), )
        msr2 = tester.MeasureSubStep(
            (m.dmm_VoutStartup, m.dmm_Vout, m.dmm_Vbat,), timeout=10)
        self.shdn = tester.SubStep((ld1, msr1, ld3, msr2))
        self.shdnH = tester.SubStep((ld2, msr1, ld4, msr2))
        # RemoteSw: load, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        ld1 = tester.LoadSubStep(((d.dcl, 2.0), ), delay=1)
        ld2 = tester.LoadSubStep(((d.dcl, 0.1), ))
        dcs1 = tester.DcSubStep(setting=((d.dcs_Vbat, 12.6),), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_VbatExt, m.dmm_VoutExt, ), timeout=5)
        rly1 = tester.RelaySubStep(((d.rla_RemoteSw, True), ))
        msr2 = tester.MeasureSubStep((m.dmm_VoutOff, ), timeout=10)
        rly2 = tester.RelaySubStep(((d.rla_RemoteSw, False), ))
        msr3 = tester.MeasureSubStep((m.dmm_VoutExt, ), timeout=5)
        self.remote_sw = tester.SubStep(
            (acs1, ld1, ld2, dcs1, msr1, rly1, msr2, rly2, msr3))
