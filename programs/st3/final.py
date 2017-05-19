#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""STxx-III Final Test Program."""
# FIXME: Upgrade this program to 3rd Generation standards with unittest.

import time
import tester

_COMMON = (
    ('Voff', 1, 2.0, None, None, None),
    ('Vout', 1, 13.60, 13.70, None, None),
    ('Vbat', 1, 13.40, 13.70, None, None),
    ('Vtrickle', 1, 3.90, 5.70, None, None),
    ('Vboost', 1, 13.80, 14.10, None, None),
    ('inOCP', 1, 11.6, None, None, None),
    ('FuseOut', 1, 0.5, None, None, None),
    ('FuseIn', 1, 13.60, 13.70, None, None),
    ('Notify', 2, None, None, None, True),
    )

LIMITS_20 = tester.testlimit.limitset(_COMMON + (
    ('FullLoad', 1, 20.1, None, None, None),
    ('LoadOCPramp', 1, 19.5, 28.0, None, None),
    ('LoadOCP', 1, 20.5, 26.0, None, None),
    ('BattOCPramp', 1, 8.0, 13.5, None, None),
    ('BattOCP', 1, 9.0, 11.5, None, None),
    ('FuseLabel', 1, None, None, '^ST20\-III$', None),
    ))

LIMITS_35 = tester.testlimit.limitset(_COMMON + (
    ('FullLoad', 1, 35.1, None, None, None),
    ('LoadOCPramp', 1, 34.1, 43.5, None, None),
    ('LoadOCP', 1, 35.1, 42.5, None, None),
    ('BattOCPramp', 1, 13.0, 19.0, None, None),
    ('BattOCP', 1, 14.0, 17.0, None, None),
    ('FuseLabel', 1, None, None, '^ST35\-III$', None),
    ))

LIMITS = {      # Test limit selection keyed by program parameter
    None: LIMITS_35,
    '20': LIMITS_20,
    '35': LIMITS_35,
    }

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """STxx-III Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('FuseLabel', self._step_label),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Battery', self._step_battery),
            tester.TestStep('LoadOCP', self._step_load_ocp),
            tester.TestStep('BattOCP', self._step_batt_ocp),
            )
        self._limits = LIMITS[self.parameter]
        self._is35 = (self.parameter != '20')
        self._fullload = self._limits['FullLoad'].limit
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

    def _step_label(self):
        """Check Fuse Label."""
        barcode = 'ST35-III' if self._is35 else 'ST20-III'
        self.fifo_push(((s.oBarcode, (barcode, )), ))
        m.barcode.measure()

    def _step_power_up(self):
        """Power up unit."""
        self.fifo_push(
            ((s.oLoad, 14.0), (s.oFuse1, 13.65), (s.oFuse2, 13.65),
             (s.oFuse3, 13.65), (s.oFuse4, 13.65), (s.oFuse5, 13.65),
             (s.oFuse6, 13.65), (s.oFuse7, 13.65), (s.oFuse8, 13.65),
             (s.oBatt, 13.65), (s.oYesNoOrGr, True), ))
        t.power_up.run()

    def _step_battery(self):
        """Battery checks."""
        self.fifo_push(
            ((s.oBatt, (0.4, 13.65)), (s.oYesNoRedOn, True),
             (s.oYesNoRedOff, True), ))
        t.battery.run()

    def _step_load_ocp(self):
        """Measure Load OCP point."""
        self.fifo_push(((s.oLoad, (13.5, ) * 15 + (11.0, 0.5, 13.6), ), ))
        m.ramp_LoadOCP.measure()
        d.dcl_Load.output(self._fullload * 1.30)
        m.dmm_Overload.measure(timeout=5)
        d.dcl_Load.output(0.0)
        m.dmm_Load.measure(timeout=10)
        time.sleep(1)

    def _step_batt_ocp(self):
        """Measure Batt OCP point."""
        self.fifo_push(((s.oBatt, (13.5, ) * 12 + (11.0, 13.6, ), ), ))
        m.ramp_BattOCP.measure()
        d.dcl_Batt.output(0.1)
        m.dmm_Batt.measure(timeout=5)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_Load = tester.DCLoad(devices['DCL1'])
        self.dcl_Batt = tester.DCLoad(devices['DCL5'])
        self.rla_BattSw = tester.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.reset()
        self.dcl_Load.output(5.0, True)
        time.sleep(0.5)
        for dcl in (self.dcl_Load, self.dcl_Batt):
            dcl.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oLoad = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oFuse1 = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oFuse2 = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.001)
        self.oFuse3 = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self.oFuse4 = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self.oFuse5 = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.001)
        self.oFuse6 = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.001)
        self.oFuse7 = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.001)
        self.oFuse8 = sensor.Vdc(dmm, high=8, low=1, rng=100, res=0.001)
        self.oBatt = sensor.Vdc(dmm, high=9, low=2, rng=100, res=0.001)
        self.oAlarm = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.01)
        self.oBarcode = sensor.DataEntry(
            message=tester.translate('st3_final', 'ScanBarcode'),
            caption=tester.translate('st3_final', 'capBarcode'))
        self.oYesNoOrGr = sensor.YesNo(
            message=tester.translate('st3_final', 'AreOrangeGreen?'),
            caption=tester.translate('st3_final', 'capOrangeGreen'))
        self.oYesNoRedOn = sensor.YesNo(
            message=tester.translate('st3_final', 'RemoveBattFuseIsRedBlink?'),
            caption=tester.translate('st3_final', 'capRed'))
        self.oYesNoRedOff = sensor.YesNo(
            message=tester.translate('st3_final', 'ReplaceBattFuseIsRedOff?'),
            caption=tester.translate('st3_final', 'capRed'))
        ocp_start, ocp_stop = limits['LoadOCPramp'].limit
        self.oLoadOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Load, sensor=self.oLoad,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.2, delay=0.1, reset=False)
        ocp_start, ocp_stop = limits['BattOCPramp'].limit
        self.oBattOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Batt, sensor=self.oBatt,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.2, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.barcode = Measurement(limits['FuseLabel'], sense.oBarcode)
        self.dmm_Load = Measurement(limits['Vout'], sense.oLoad)
        self.dmm_Boost = Measurement(limits['Vboost'], sense.oLoad)
        self.dmm_Batt = Measurement(limits['Vbat'], sense.oBatt)
        self.dmm_Fuse1 = Measurement(limits['FuseIn'], sense.oFuse1)
        self.dmm_Fuse2 = Measurement(limits['FuseIn'], sense.oFuse2)
        self.dmm_Fuse3 = Measurement(limits['FuseIn'], sense.oFuse3)
        self.dmm_Fuse4 = Measurement(limits['FuseIn'], sense.oFuse4)
        self.dmm_Fuse5 = Measurement(limits['FuseIn'], sense.oFuse5)
        self.dmm_Fuse6 = Measurement(limits['FuseIn'], sense.oFuse6)
        self.dmm_Fuse7 = Measurement(limits['FuseIn'], sense.oFuse7)
        self.dmm_Fuse8 = Measurement(limits['FuseIn'], sense.oFuse8)
        self.ui_YesNoOrGr = Measurement(limits['Notify'], sense.oYesNoOrGr)
        self.ui_YesNoRedOn = Measurement(limits['Notify'], sense.oYesNoRedOn)
        self.ui_YesNoRedOff = Measurement(limits['Notify'], sense.oYesNoRedOff)
        self.dmm_BattFuseOut = Measurement(limits['FuseOut'], sense.oBatt)
        self.dmm_BattFuseIn = Measurement(limits['FuseIn'], sense.oBatt)
        self.ramp_LoadOCP = Measurement(limits['LoadOCP'], sense.oLoadOCP)
        self.dmm_Overload = Measurement(limits['Voff'], sense.oLoad)
        self.ramp_BattOCP = Measurement(limits['BattOCP'], sense.oBattOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: 240Vac, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True)
        msr1 = tester.MeasureSubStep(
            (m.dmm_Boost, m.dmm_Fuse1, m.dmm_Fuse2, m.dmm_Fuse3, m.dmm_Fuse4,
             m.dmm_Fuse5, m.dmm_Fuse6, m.dmm_Fuse7, m.dmm_Fuse8,
             m.dmm_Batt, m.ui_YesNoOrGr, ), timeout=10)
        self.power_up = tester.SubStep((acs1, msr1, ))
        # Battery: Load, SwitchOff, measure, SwitchOn,
        #           PullFuse, measure, ReplaceFuse, measure, unload
        dcl1 = tester.LoadSubStep(
            ((d.dcl_Batt, 2.0), (d.dcl_Load, 0.0), ), output=True)
        rla1 = tester.RelaySubStep(((d.rla_BattSw, True), ))
        msr1 = tester.MeasureSubStep((m.dmm_BattFuseOut, ), timeout=5)
        dcl2 = tester.LoadSubStep(((d.dcl_Batt, 0.0), ))
        rla2 = tester.RelaySubStep(((d.rla_BattSw, False), ), delay=0.5)
        msr2 = tester.MeasureSubStep(
            (m.dmm_BattFuseIn, m.ui_YesNoRedOn, m.ui_YesNoRedOff, ), timeout=5)
        self.battery = tester.SubStep((dcl1, rla1, msr1, dcl2, rla2, msr2, ))
