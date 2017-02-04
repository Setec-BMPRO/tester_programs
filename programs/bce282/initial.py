#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Initial Test Program."""

# FIXME: This program is not finished yet!

import os
import time
import tester
from . import msp

LIMITS_12 = tester.testlimit.limitset((
        ('VccBiasExt', 1, 14.0, 16.0, None, None),
        ('Vac', 1, 235.0, 245.0, None, None),
        ('Vbus', 1, 330.0, 350.0, None, None),
        # 15.60 +/- 5%
        ('VccPri', 1, 14.82, 16.38, None, None),
        # 15.0 +/ 13%
        ('VccBias', 1, 13.05, 16.95, None, None),
        ('VbatOff', 1, 0.5, None, None, None),
        ('AlarmClosed', 1, 1000, 3000, None, None),
        ('AlarmOpen', 1, 11000, 13000, None, None),
        ('FullLoad', 1, 20.1, None, None, None),
        ('BattOCPramp', 1, 14.0, 16.0, None, None),
        ('BattOCP', 1, 14.175, 15.825, None, None),
        ('OutOCPramp', 1, 19.5, 25.0, None, None),
        ('OutOCP', 1, 20.05, 24.00, None, None),
        ('inOCP', 1, 13.0, None, None, None),
        ('FixtureLock', 0, 20, None, None, None),
        # 13.8 +/- 2.6%
        ('VoutPreCal', 1, 13.4412, 14.1588, None, None),
        # Data reported by the MSP430
        ('Status 0', 0, -0.1, 0.1, None, None),
        ('MspVout', 0, 13.0, 14.6, None, None),
        ))

LIMITS_24 = tester.testlimit.limitset((
        ('VccBiasExt', 1, 14.0, 16.0, None, None),
        ('Vac', 1, 235.0, 245.0, None, None),
        ('Vbus', 1, 330.0, 350.0, None, None),
        # 15.60 +/- 5%
        ('VccPri', 1, 14.82, 16.38, None, None),
        # 15.0 +/ 13%
        ('VccBias', 1, 13.05, 16.95, None, None),
        ('VbatOff', 1, 0.5, None, None, None),
        ('AlarmClosed', 1, 1000, 3000, None, None),
        ('AlarmOpen', 1, 11000, 13000, None, None),
        ('FullLoad', 1, 10.1, None, None, None),
        ('BattOCPramp', 1, 5.5, 9.5, None, None),
        ('BattOCP', 1, 6.0, 9.0, None, None),
        ('OutOCPramp', 1, 9.5, 12.5, None, None),
        ('OutOCP', 1, 10.0, 12.0, None, None),
        ('inOCP', 1, 26.0, None, None, None),
        ('FixtureLock', 0, 20, None, None, None),
        # 27.5 +/- 2.6%
        ('VoutPreCal', 1, 26.785, 28.215, None, None),
        # Data reported by the MSP430
        ('Status 0', 0, -0.1, 0.1, None, None),
        ('MspVout', 0, 13.0, 14.6, None, None),
        ))

LIMITS = {      # Test limit selection keyed by program parameter
    None: LIMITS_12,
    '12': LIMITS_12,
    '24': LIMITS_24
    }

# Serial port for MSP430 console.
_MSP430_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM2'}[os.name]

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.testsequence.TestSequence):

    """BCE282-12/24 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep(
                'ProgramMicro', self._step_program_micro, not self.fifo),
            tester.TestStep('PowerUp', self._step_power_up, False),
            tester.TestStep('Calibration', self._step_cal, False),
            tester.TestStep('OCP', self._step_ocp, False),
            )
        self._limits = LIMITS[self.parameter]
        self._isbce12 = (self.parameter != '24')
        self._msp = msp.Console(port=_MSP430_PORT)
        global d, s, m, t
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d, self._limits, self._msp)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._msp.close()
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.Lock, 10.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_program_micro(self):
        """Program the microprocessor.

           Powers bootloader interface and MSP430.
           Dumps existing password if any.
           Programs.

        """
        self.fifo_push(((s.oVccBias, 15.0), ))
        t.prog_setup.run()
        if not self.fifo:
            self._msp.open()
        d.rla_Prog.set_on()
        d.rla_Prog.set_off()
        d.dcs_VccBias.output(0.0)

    def _step_power_up(self):
        """Power up the unit at 240Vac and measure voltages at min load."""
        self.fifo_push(((s.oVac, 240.0), (s.oVbus, 340.0), (s.oVccPri, 15.5),
                       (s.oVccBias, 15.0), (s.oVbat, 0.1), (s.oAlarm, 2200), ))
        t.pwr_up.run()

    def _step_cal(self):
        """Calibration."""
        self._msp.defaults()
        m.msp_Status.measure(timeout=5)
        self._msp.test_mode_enable()
#        dmm_Vout = m.dmm_Vout.measure(timeout=5).reading1
#        msp_Vout = m.msp_Vout.measure(timeout=5).reading1

    def _step_ocp(self):
        """Measure Vout and Vbat OCP points."""
        if self._isbce12:
            self.fifo_push(((s.oAlarm, 12000),
                            (s.oVbat, (13.6, ) * 15 + (12.9, ), ),
                            (s.oVout, (13.6, ) * 15 + (12.9, ), ), ))
        else:
            self.fifo_push(((s.oAlarm, 12000),
                            (s.oVbat, (27.3, ) * 15 + (25.9, ), ),
                            (s.oVout, (27.3, ) * 15 + (25.9, ), ), ))
        tester.MeasureGroup((m.dmm_AlarmOpen, m.ramp_BattOCP,
                             m.ramp_OutOCP, ), timeout=5)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_VccBias = tester.DCSource(devices['DCS1']) # Powers MSP430
        self.dcs_RS232 = tester.DCSource(devices['DCS2']) # Powers bootloader interface
        self.dcl_Vout = tester.DCLoad(devices['DCL1'])
        self.dcl_Vbat = tester.DCLoad(devices['DCL2'])
        self.rla_Prog = tester.Relay(devices['RLA1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_Vout.output(2.0)
        self.dcl_Vbat.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_VccBias, self.dcs_RS232):
            dcs.output(0.0, False)
        for ld in (self.dcl_Vout, self.dcl_Vbat, ):
            ld.output(0.0, False)
        self.rla_Prog.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, mspdev):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.Lock = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self.oVac = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oVbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.oVccPri = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self.oVccBias = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.oVbat = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self.oAlarm = sensor.Res(dmm, high=9, low=5, rng=100, res=0.001)
        self.oVout = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
#        self.oRed = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
#        self.oGreen = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.oMsp_Status = msp.Sensor(mspdev, 'MSP-NvStatus')
        self.oMsp_Vout = msp.Sensor(mspdev, 'MSP-Vout')
        ocp_start, ocp_stop = limits['BattOCPramp'].limit
        self.oBattOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Vbat,sensor=self.oVbat,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.05)
        ocp_start, ocp_stop = limits['OutOCPramp'].limit
        self.oOutOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_Vout, sensor=self.oVout,
            detect_limit=(limits['inOCP'], ),
            start=ocp_start, stop=ocp_stop, step=0.05, delay=0.05, reset=False)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        lim = limits
        sen = sense
        self.dmm_Lock = Measurement(lim['FixtureLock'], sen.Lock)
        self.dmm_VccBiasExt = Measurement(lim['VccBiasExt'], sen.oVccBias)
        self.dmm_Vac = Measurement(lim['Vac'], sen.oVac)
        self.dmm_Vbus = Measurement(lim['Vbus'], sen.oVbus)
        self.dmm_VccPri = Measurement(lim['VccPri'], sen.oVccPri)
        self.dmm_VccBias = Measurement(lim['VccBias'], sen.oVccBias)
        self.dmm_VbatOff = Measurement(lim['VbatOff'], sen.oVbat)
        self.dmm_AlarmClosed = Measurement(lim['AlarmClosed'], sen.oAlarm)
        self.dmm_AlarmOpen = Measurement(lim['AlarmOpen'], sen.oAlarm)
        self.dmm_Vout = Measurement(lim['VoutPreCal'], sen.oVout)
        self.msp_Status = Measurement(lim['Status 0'], sen.oMsp_Status)
        self.msp_Vout = Measurement(lim['MspVout'], sen.oMsp_Vout)
        self.ramp_BattOCP = Measurement(lim['BattOCP'], sen.oBattOCP)
        self.ramp_OutOCP = Measurement(lim['OutOCP'], sen.oOutOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # ProgSetup:
        dcs1 = tester.DcSubStep(setting=((d.dcs_RS232, 9.0),
                            (d.dcs_VccBias, 15.0), ), output=True, delay=1)
        msr1 = tester.MeasureSubStep((m.dmm_VccBiasExt, ), timeout=5)
        self.prog_setup = tester.SubStep((dcs1, msr1))
        # PowerUp: Apply 240Vac, set min load, measure.
        acs1 = tester.AcSubStep(acs=d.acsource, voltage=240.0, output=True,
                                  delay=1.0)
        ld1 = tester.LoadSubStep(((d.dcl_Vbat, 0.1), ), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_Vac, m.dmm_Vbus, m.dmm_VccPri,
                                   m.dmm_VccBias, m.dmm_VbatOff,
                                   m.dmm_AlarmClosed, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl_Vbat, 0.0), ))
        self.pwr_up = tester.SubStep((acs1, ld1, msr1, ld2))
