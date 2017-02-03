#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RM-50-24 Final Test Program."""

import time
from pydispatch import dispatcher
import tester

LIMITS = tester.testlimit.limitset((
    ('Rsense', 1, 980, 1020, None, None),
    ('Vsense', 1, 0.0001, None, None, None),
    ('uSwitch', 0, 0, 100, None, None),
    ('Vdrop', 1, 0.4, None, None, None),
    ('24Vdcin', 1, 23.0, 24.4, None, None),
    ('24Vdcout', 1, 23.6, 24.4, None, None),
    ('24Voff', 1, 1.0, None, None, None),
    ('24Vnl', 1, 23.6, 24.4, None, None),
    ('24Vfl', 1, 23.4, 24.1, None, None),
    ('24Vpl', 1, 23.0, 24.1, None, None),
    ('OCP', 1, 3.2, 4.3, None, None),
    ('inOCP', 1, 23.0, None, None, None),
    ('CurrShunt', 1, 2.5, None, None, None),
    ('PowNL', 1, 1.0, 5.0, None, None),
    ('PowFL', 1, 40.0, 70.0, None, None),
    ('Eff', 1, None, 84.0, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """RM-50-24 Final Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('DCInputLeakage', self._step_dcinput_leakage),
            tester.TestStep('DCInputTrack', self._step_dcinput_track),
            tester.TestStep('ACInput240V', self._step_acinput240v),
            tester.TestStep('ACInput110V', self._step_acinput110v),
            tester.TestStep('ACInput90V', self._step_acinput90v),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('PowerNoLoad', self._step_power_noload),
            tester.TestStep('Efficiency', self._step_efficiency),
            )
        super().open(sequence)
        global m, d, s, t
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
        self.fifo_push(((s.Lock, 1.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_dcinput_leakage(self):
        """Test for input leakage current at the DC input with no load."""
        self.fifo_push(((s.oRsense, 1000), (s.oVsense, 0.05), ))
        t.dcinp_leak.run()

    def _step_dcinput_track(self):
        """
        Measure the drop in the track between dc input and output at full load.
        """
        self.fifo_push(
            ((s.o24Vdcin, 23.6), (s.o24Vdcin, 24.0), (s.o24Vdcout, 23.65), ))
        d.dcl_dcout.output(2.1, True)
        val = m.dmm_24Vdcin.measure(timeout=5).reading1
        # Slightly higher dc input to compensate for drop in fixture cabling
        d.dcs_24V.output(24.0 + (24.0 - val))
        vals = tester.MeasureGroup(
            (m.dmm_24Vdcin, m.dmm_24Vdcout), timeout=5).readings
        s.oMirVdcDrop.store(vals[0] - vals[1])
        m.dmm_vdcDrop.measure()
        d.dcs_24V.output(0.0, output=False)
        d.dcl_dcout.output(0.0)

    def _step_acinput240v(self):
        """Apply 240V AC input and measure output at no load and full load."""
        self.fifo_push(((s.o24V, (24.0, ) * 2), ))
        t.acinput_240V.run()

    def _step_acinput110v(self):
        """Apply 110V AC input and measure output at no load and full load."""
        self.fifo_push(((s.o24V, (24.0, ) * 2), ))
        t.acinput_110V.run()

    def _step_acinput90v(self):
        """Apply 90V AC input and measure outputs at various load steps."""
        self.fifo_push(((s.o24V, (24.0, ) * 4), ))
        t.acinput_90V.run()
        d.dcl_out.linear(2.7, 2.95, step=0.05, delay=0.05)
        for curr in (3.0, 3.05):
            with tester.PathName(str(curr)):
                time.sleep(0.5)
                d.dcl_out.output(curr)
                d.dcl_out.opc()
                m.dmm_24Vpl.measure(timeout=5)

    def _step_ocp(self):
        """Measure OCP point, turn off and recover."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o24V, (24.0, ) * 15 + (22.5, ), ),
             (s.o24V, 0.0), ))
        t.ocp.run()

    def _step_power_noload(self):
        """Measure input power at no load."""
        self.fifo_push(((s.o24V, 24.0), (s.oInputPow, 2.0), ))
        t.pow_nl.run()

    def _step_efficiency(self):
        """Measure efficiency."""
        self.fifo_push(
            ((s.oInputPow, 59.0), (s.o24V, 24.0), (s.oCurrshunt, 0.0021), ))
        d.dcl_out.output(2.1)
        inp_pwr_fl = m.dmm_powerFL.measure(timeout=5).reading1
        out_volts_fl = m.dmm_24Vfl.measure(timeout=5).reading1
        out_curr_fl = m.dmm_currShunt.measure(timeout=5).reading1
        eff = 100 * out_volts_fl * out_curr_fl / inp_pwr_fl
        s.oMirEff.store(eff)
        m.dmm_eff.measure()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.pwr = tester.Power(devices['PWR'])
        self.dcs_24V = tester.DCSource(devices['DCS1'])
        self.dcl_out = tester.DCLoad(devices['DCL1'])
        self.dcl_dcout = tester.DCLoad(devices['DCL5'])
        self.rla_rsense = tester.Relay(devices['RLA1'])
        self.discharge = tester.Discharge(devices['DIS'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_out.output(2.1)
        time.sleep(1)
        self.discharge.pulse()
        self.dcs_24V.output(0.0, False)
        for ld in (self.dcl_out, self.dcl_dcout):
            ld.output(0.0, False)
        for rla in (self.rla_rsense, ):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        pwr = logical_devices.pwr
        sensor = tester.sensor
        self.oMirVdcDrop = sensor.Mirror()
        self.oMirPowNL = sensor.Mirror()
        self.oMirEff = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.Lock = sensor.Res(dmm, high=9, low=5, rng=10000, res=1)
        self.oRsense = sensor.Res(dmm, high=1, low=1, rng=10000, res=1)
        self.oVsense = sensor.Vdc(
            dmm, high=1, low=1, rng=1, res='MAX', scale=0.001)
        self.o24Vdcin = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self.o24Vdcout = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o24V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.oCurrshunt = sensor.Vdc(
            dmm, high=5, low=4, rng=0.1, res='MAX', scale=1000, nplc=100)
        self.oInputPow = sensor.Power(pwr)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_out, sensor=self.o24V,
            detect_limit=(limits['inOCP'], ),
            start=3.05, stop=4.4, step=0.05, delay=0.1)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirVdcDrop.flush()
        self.oMirPowNL.flush()
        self.oMirEff.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_vdcDrop = Measurement(limits['Vdrop'], sense.oMirVdcDrop)
        self.dmm_eff = Measurement(limits['Eff'], sense.oMirEff)
        self.dmm_Lock = Measurement(limits['uSwitch'], sense.Lock)
        self.dmm_Rsense = Measurement(limits['Rsense'], sense.oRsense)
        self.dmm_Vsense = Measurement(limits['Vsense'], sense.oVsense)
        self.dmm_24Vdcin = Measurement(limits['24Vdcin'], sense.o24Vdcin)
        self.dmm_24Vdcout = Measurement(limits['24Vdcout'], sense.o24Vdcout)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.dmm_24Vnl = Measurement(limits['24Vnl'], sense.o24V)
        self.dmm_24Vfl = Measurement(limits['24Vfl'], sense.o24V)
        self.dmm_24Vpl = Measurement(limits['24Vpl'], sense.o24V)
        self.dmm_currShunt = Measurement(limits['CurrShunt'], sense.oCurrshunt)
        self.dmm_powerNL = Measurement(limits['PowNL'], sense.oInputPow)
        self.dmm_powerFL = Measurement(limits['PowFL'], sense.oInputPow)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # DCInputLeakage: DC input, measure input current.
        msr1 = tester.MeasureSubStep((m.dmm_Rsense, ), timeout=5)
        rly = tester.RelaySubStep(((d.rla_rsense, True), ))
        dcs = tester.DcSubStep(setting=((d.dcs_24V, 24.0), ), output=True)
        msr2 = tester.MeasureSubStep((m.dmm_Vsense, ), timeout=5)
        self.dcinp_leak = tester.SubStep((msr1, rly, dcs, msr2))
        # ACInput: Set AC input, measure at no load and full load.
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, frequency=50,
            output=True, delay=0.5)
        acs2 = tester.AcSubStep(
            acs=d.acsource, voltage=110.0, frequency=60, delay=0.5)
        acs3 = tester.AcSubStep(
            acs=d.acsource, voltage=90.0, frequency=60, delay=0.5)
        ld1 = tester.LoadSubStep(((d.dcl_out, 0.0), ), output=True)
        msr1 = tester.MeasureSubStep((m.dmm_24Vnl, ), timeout=5)
        ld2 = tester.LoadSubStep(((d.dcl_out, 2.1), ))
        msr2 = tester.MeasureSubStep((m.dmm_24Vfl, ), timeout=5)
        self.acinput_240V = tester.SubStep((ld1, acs1, msr1, ld2, msr2))
        self.acinput_110V = tester.SubStep((ld1, acs2, msr1, ld2, msr2))
        self.acinput_90V = tester.SubStep((ld1, acs3, msr1, ld2, msr2))
        # OCP: Ocp, turn off.
        acs1 = tester.AcSubStep(
            acs=d.acsource, voltage=240.0, frequency=50, delay=0.5)
        msr1 = tester.MeasureSubStep((m.dmm_24Vpl, m.ramp_OCP, ), timeout=5)
        acs2 = tester.AcSubStep(acs=d.acsource, voltage=0.0)
        ld1 = tester.LoadSubStep(((d.dcl_out, 2.1), ), delay=1)
        msr2 = tester.MeasureSubStep((m.dmm_24Voff, ), timeout=5)
        self.ocp = tester.SubStep((acs1, msr1, acs2, ld1, msr2))
        # NoLoadPower: Startup at no load, measure input power.
        acs = tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        ld = tester.LoadSubStep(((d.dcl_out, 0.05), ), delay=0.5)
        msr = tester.MeasureSubStep((m.dmm_24Vnl, m.dmm_powerNL, ), timeout=5)
        self.pow_nl = tester.SubStep((acs, ld, msr))
