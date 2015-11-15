#!/usr/bin/env python3
"""RM-50-24 Final Test Program."""

from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.pwr = power.Power(devices['PWR'])
        self.dcs_24V = dcsource.DCSource(devices['DCS1'])
        self.dcl_out = dcload.DCLoad(devices['DCL1'])
        self.dcl_dcout = dcload.DCLoad(devices['DCL5'])
        self.rla_rsense = relay.Relay(devices['RLA1'])
        self.discharge = discharge.Discharge(devices['DIS'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Source
        self.dcs_24V.output(0.0, False)
        # Switch off DC Loads
        for ld in (self.dcl_out, self.dcl_dcout):
            ld.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_rsense, ):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        pwr = logical_devices.pwr
        self.oMirVdcDrop = sensor.Mirror()
        self.oMirPowNL = sensor.Mirror()
        self.oMirEff = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
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
        msr1 = MeasureSubStep((m.dmm_Rsense, ), timeout=5)
        rly = RelaySubStep(((d.rla_rsense, True), ))
        dcs = DcSubStep(setting=((d.dcs_24V, 24.0), ), output=True)
        msr2 = MeasureSubStep((m.dmm_Vsense, ), timeout=5)
        self.dcinp_leak = Step((msr1, rly, dcs, msr2))
        # ACInput: Set AC input, measure at no load and full load.
        acs1 = AcSubStep(
            acs=d.acsource, voltage=240.0, frequency=50,
            output=True, delay=0.5)
        acs2 = AcSubStep(
            acs=d.acsource, voltage=110.0, frequency=60, delay=0.5)
        acs3 = AcSubStep(
            acs=d.acsource, voltage=90.0, frequency=60, delay=0.5)
        ld1 = LoadSubStep(((d.dcl_out, 0.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_24Vnl, ), timeout=5)
        ld2 = LoadSubStep(((d.dcl_out, 2.1), ))
        msr2 = MeasureSubStep((m.dmm_24Vfl, ), timeout=5)
        self.acinput_240V = Step((ld1, acs1, msr1, ld2, msr2))
        self.acinput_110V = Step((ld1, acs2, msr1, ld2, msr2))
        self.acinput_90V = Step((ld1, acs3, msr1, ld2, msr2))
        # OCP: Ocp, turn off.
        acs1 = AcSubStep(
            acs=d.acsource, voltage=240.0, frequency=50, delay=0.5)
        msr1 = MeasureSubStep((m.dmm_24Vpl, m.ramp_OCP, ), timeout=5)
        acs2 = AcSubStep(acs=d.acsource, voltage=0.0)
        ld1 = LoadSubStep(((d.dcl_out, 2.1), ), delay=1)
        msr2 = MeasureSubStep((m.dmm_24Voff, ), timeout=5)
        self.ocp = Step((acs1, msr1, acs2, ld1, msr2))
        # NoLoadPower: Startup at no load, measure input power.
        acs = AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5)
        ld = LoadSubStep(((d.dcl_out, 0.05), ), delay=0.5)
        msr = MeasureSubStep((m.dmm_24Vnl, m.dmm_powerNL, ), timeout=5)
        self.pow_nl = Step((acs, ld, msr))
