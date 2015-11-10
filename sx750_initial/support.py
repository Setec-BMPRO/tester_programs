#!/usr/bin/env python3
"""SX-750 Initial Test Program."""

from pydispatch import dispatcher

import tester
from tester.devlogical import *
from tester.measure import *
from share.console import Sensor as con_sensor
from . import digpot


sensor = tester.sensor


class LogicalDevices():

    """SX-750 Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dmm = dmm.DMM(devices['DMM'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_PriCtl = dcsource.DCSource(devices['DCS1'])
        self.dcs_5Vsb = dcsource.DCSource(devices['DCS3'])
        self.dcl_5Vsb = dcload.DCLoad(devices['DCL2'])
        self.dcl_12V = dcload.DCLoad(devices['DCL1'])
        self.dcl_24V = dcload.DCLoad(devices['DCL5'])
        self.rla_pic = relay.Relay(devices['RLA1'])
        self.rla_boot = relay.Relay(devices['RLA2'])
        self.rla_pson = relay.Relay(devices['RLA3'])
        self.rla_pot_ud = relay.Relay(devices['RLA6'])
        self.rla_pot_12 = relay.Relay(devices['RLA5'])
        self.rla_pot_24 = relay.Relay(devices['RLA4'])
        self.ocp_pot = digpot.OCPAdjust(
            self.rla_pot_ud, self.rla_pot_12, self.rla_pot_24)

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source
        self.acsource.output(voltage=0.0, output=False)
        # Switch off DC Loads
        for ld in (self.dcl_5Vsb, self.dcl_12V, self.dcl_24V):
            ld.output(0.0)
        # Switch off DC Sources
        for dcs in (self.dcs_PriCtl, self.dcs_5Vsb):
            dcs.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_pic, self.rla_boot, self.rla_pson):
            rla.set_off()
        # Disable digital pots
        self.ocp_pot.disable()


class Sensors():

    """SX-750 Sensors."""

    def __init__(self, logical_devices, limits, armdev):
        """Create all Sensor instances."""
        d = logical_devices
        dmm = d.dmm
        # Mirror sensors for Programming result logging
        self.oMirARM = sensor.Mirror()
        self.oMirPIC = sensor.Mirror()
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        self.o5Vsb = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o12VinOCP = sensor.Vdc(dmm, high=10, low=2, rng=100, res=0.01)
        self.o24V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o24VinOCP = sensor.Vdc(dmm, high=11, low=2, rng=100, res=0.01)
        self.PriCtl = sensor.Vdc(dmm, high=8, low=2, rng=100, res=0.01)
        self.PFC = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.PGOOD = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.01)
        self.ACFAIL = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self.ACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.Lock = sensor.Res(dmm, high=12, low=4, rng=1000, res=0.01)
        self.Part = sensor.Res(dmm, high=13, low=4, rng=1000, res=0.01)
        self.R601 = sensor.Res(dmm, high=14, low=5, rng=10000, res=0.01)
        self.R602 = sensor.Res(dmm, high=15, low=5, rng=10000, res=0.01)
        self.R609 = sensor.Res(dmm, high=16, low=6, rng=10000, res=0.01)
        self.R608 = sensor.Res(dmm, high=17, low=6, rng=10000, res=0.01)
        self.OCP12V = sensor.Ramp(
            stimulus=d.dcl_12V, sensor=self.o12VinOCP,
            detect_limit=(limits['12V_inOCP'], ),
            start=36.6 * 0.9, stop=36.6 * 1.1, step=0.1, delay=0,
            reset=True, use_opc=True)
        self.OCP24V = sensor.Ramp(
            stimulus=d.dcl_24V, sensor=self.o24VinOCP,
            detect_limit=(limits['24V_inOCP'], ),
            start=18.3 * 0.9, stop=18.3 * 1.1, step=0.1, delay=0,
            reset=True, use_opc=True)
        self.AcStart = sensor.Ramp(
            stimulus=d.acsource, sensor=self.ACFAIL,
            detect_limit=(limits['ACFAIL'], ),
            start=75.0, stop=95.0, step=0.5, delay=0.3,
            reset=False, use_opc=False)
        self.AcStop = sensor.Ramp(
            stimulus=d.acsource, sensor=self.ACFAIL,
            detect_limit=(limits['ACOK'], ),
            start=95.0, stop=75.0, step=-0.5, delay=0.3,
            reset=False, use_opc=False)
        self.ARM_AcDuty = con_sensor(armdev, 'ARM-AcDuty')
        self.ARM_AcPer = con_sensor(armdev, 'ARM-AcPer')
        self.ARM_AcFreq = con_sensor(armdev, 'ARM-AcFreq')
        self.ARM_AcVolt = con_sensor(armdev, 'ARM-AcVolt')
        self.ARM_PfcTrim = con_sensor(armdev, 'ARM-PfcTrim')
        self.ARM_12V = con_sensor(armdev, 'ARM-12V')
        self.ARM_24V = con_sensor(armdev, 'ARM-24V')
        self.ARM_SwVer = con_sensor(
            armdev, 'ARM_SwVer', rdgtype=tester.sensor.ReadingString)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirARM.flush()
        self.oMirPIC.flush()


class Measurements():

    """SX-750 Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        # Programming results
        pgmlim = limits['Program']
        self.pgmARM = Measurement(pgmlim, sense.oMirARM)
        self.pgmPIC = Measurement(pgmlim, sense.oMirPIC)
        self.dmm_5Voff = Measurement(limits['5Voff'], sense.o5Vsb)
        self.dmm_5Vsb_set = Measurement(limits['5Vsb_set'], sense.o5Vsb)
        self.dmm_5Vsb = Measurement(limits['5Vsb'], sense.o5Vsb)
        self.dmm_12V_set = Measurement(limits['12V_set'], sense.o12V)
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.dmm_12Voff = Measurement(limits['12Voff'], sense.o12V)
        self.dmm_12V_inOCP = Measurement(limits['12V_inOCP'], sense.o12VinOCP)
        self.dmm_24V = Measurement(limits['24V'], sense.o24V)
        self.dmm_24V_set = Measurement(limits['24V_set'], sense.o24V)
        self.dmm_24Voff = Measurement(limits['24Voff'], sense.o24V)
        self.dmm_24V_inOCP = Measurement(limits['24V_inOCP'], sense.o24VinOCP)
        self.dmm_PriCtl = Measurement(limits['PriCtl'], sense.PriCtl)
        self.dmm_PFCpre = Measurement(limits['PFCpre'], sense.PFC)
        self.dmm_PFCpost = Measurement(limits['PFCpost'], sense.PFC)
        self.dmm_ACin = Measurement(limits['ACin'], sense.ACin)
        self.dmm_PGOOD = Measurement(limits['PGOOD'], sense.PGOOD)
        self.dmm_ACFAIL = Measurement(limits['ACFAIL'], sense.ACFAIL)
        self.dmm_ACOK = Measurement(limits['ACOK'], sense.ACFAIL)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.Lock)
        self.dmm_Part = Measurement(limits['PartCheck'], sense.Part)
        self.dmm_R601 = Measurement(limits['Snubber'], sense.R601)
        self.dmm_R602 = Measurement(limits['Snubber'], sense.R602)
        self.dmm_R609 = Measurement(limits['Snubber'], sense.R609)
        self.dmm_R608 = Measurement(limits['Snubber'], sense.R608)
        self.rampOcp12V = Measurement(limits['12V_OCPchk'], sense.OCP12V)
        self.rampOcp24V = Measurement(limits['24V_OCPchk'], sense.OCP24V)
        self.rampAcStart = Measurement(limits['ACstart'], sense.AcStart)
        self.rampAcStop = Measurement(limits['ACstop'], sense.AcStop)
        self.arm_AcDuty = Measurement(limits['ARM-AcDuty'], sense.ARM_AcDuty)
        self.arm_AcPer = Measurement(limits['ARM-AcPer'], sense.ARM_AcPer)
        self.arm_AcFreq = Measurement(limits['ARM-AcFreq'], sense.ARM_AcFreq)
        self.arm_AcVolt = Measurement(limits['ARM-AcVolt'], sense.ARM_AcVolt)
        self.arm_PfcTrim = Measurement(
            limits['ARM-PfcTrim'], sense.ARM_PfcTrim)
        self.arm_12V = Measurement(limits['ARM-12V'], sense.ARM_12V)
        self.arm_24V = Measurement(limits['ARM-24V'], sense.ARM_24V)
        self.arm_SwVer = Measurement(limits['ARM-SwVer'], sense.ARM_SwVer)
