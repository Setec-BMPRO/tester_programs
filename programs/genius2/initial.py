#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Initial Test Program for GENIUS-II and GENIUS-II-H."""

import os
import inspect
import time
import tester
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_lo, lim_boolean, lim_hi)
import share
from share import oldteststep

PIC_HEX = 'genius2_3a.hex'

_BASE_DATA = (
    lim_lo('DetectDiode', 0.3),
    lim_hilo_delta('FlyLead', 30.0, 10.0),
    lim_hilo_delta('AcIn', 240.0, 5.0),
    lim_hilo_delta('Vbus', 330.0, 20.0),
    lim_hilo('Vcc', 13.8, 22.5),
    lim_lo('VccOff', 5.0),
    lim_hilo_delta('Vdd', 5.00, 0.1),
    lim_hilo('VbatCtl', 12.7, 13.5),
    lim_hilo_delta('Vctl', 12.0, 0.5),
    lim_hilo('VoutPre', 12.5, 15.0),
    lim_hilo_delta('Vout', 13.65, 0.05),
    lim_lo('VoutOff', 1.0),
    lim_hilo('VbatPre', 12.5, 15.0),
    lim_hilo_delta('Vbat', 13.65, 0.05),
    lim_hilo_delta('Vaux', 13.70, 0.5),
    lim_lo('FanOff', 0.5),
    lim_hilo('FanOn', 12.0, 14.1),
    lim_lo('InOCP', 13.24),
    lim_hilo('OCP', 34.0, 43.0),
    lim_boolean('Notify', True),
    lim_lo('FixtureLock', 20),
    )

LIMITS_STD = tester.testlimit.limitset(_BASE_DATA + (
    lim_lo('MaxBattLoad', 15.0),
    lim_lo('VbatOCP', 10.0),
    ))

LIMITS_H = tester.testlimit.limitset(_BASE_DATA + (
    lim_lo('MaxBattLoad', 30.0),
    lim_hi('VbatOCP', 13.0),
    ))

LIMITS = {      # Test limit selection keyed by program parameter
    None: LIMITS_STD,
    'STD': LIMITS_STD,
    'H': LIMITS_H,
    }


class Initial(tester.TestSequence):

    """GENIUS-II Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self._isH = (self.parameter == 'H')
        self.limits = LIMITS[self.parameter]
        self.logdev = LogicalDevices(self.physical_devices)
        self.sensor = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensor, self.limits)
        self.subtest = SubTests(self.logdev, self.meas)
        self.steps = (
            tester.TestStep('Prepare', self.subtest.prepare.run),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Aux', self.subtest.aux.run),
            tester.TestStep('PowerUp', self.subtest.pwrup.run),
            tester.TestStep('VoutAdj', self._step_vout_adj),
            tester.TestStep('ShutDown', self.subtest.shdn.run),
            tester.TestStep('OCP', self._step_ocp),
            )

    def close(self):
        """Finished testing."""
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_program(self, dev, mes):
        """Program the board."""
        dev.program_pic.program()
        dev.dcs_vbatctl.output(0.0, False)

    @oldteststep
    def _step_vout_adj(self, dev, mes):
        """Vout adjustment."""
        mes.ui_AdjVout.measure(timeout=5)
        dev.dcl.output(2.0)
        tester.MeasureGroup(
            (mes.dmm_vout, mes.dmm_vbatctl, mes.dmm_vbat, mes.dmm_vdd),
            timeout=5)

    @oldteststep
    def _step_ocp(self, dev, mes):
        """Ramp up load until OCP."""
        # Check for correct model (GENIUS-II/GENIUS-II-H)
        dev.dcl_vbat.binary(0.0, 18.0, 5.0)
        mes.dmm_vbatocp.measure(timeout=2)
        dev.dcl_vbat.output(0.0)
        mes.dmm_vbat.measure(timeout=10)
        time.sleep(2)
        if self._isH:
            dev.dclh.binary(0.0, 32.0, 5.0)
            mes.ramp_OCP_H.measure()
        else:
            dev.dcl.binary(0.0, 32.0, 5.0)
            mes.ramp_OCP.measure()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_vout = tester.DCSource(devices['DCS1'])
        self.dcs_vbat = tester.DCSource(devices['DCS2'])
        self.dcs_vaux = tester.DCSource(devices['DCS4'])
        self.dcs_vbatctl = tester.DCSource(devices['DCS5'])
        self.dcl_vout = tester.DCLoad(devices['DCL1'])
        self.dcl_vbat = tester.DCLoad(devices['DCL5'])
        self.dcl = tester.DCLoadParallel(
            ((self.dcl_vout, 29), (self.dcl_vbat, 14)))
        self.dclh = tester.DCLoadParallel(
            ((self.dcl_vout, 5), (self.dcl_vbat, 30)))
        self.rla_prog = tester.Relay(devices['RLA1'])
        self.rla_vbus = tester.Relay(devices['RLA2'])
        self.rla_batfuse = tester.Relay(devices['RLA3'])
        self.rla_fan = tester.Relay(devices['RLA5'])
        self.rla_shdwn1 = tester.Relay(devices['RLA6'])
        self.rla_shdwn2 = tester.Relay(devices['RLA7'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            PIC_HEX, folder, '16F1828', self.rla_prog)

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source & discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.dcl.output(10.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (
            self.dcs_vout, self.dcs_vbat, self.dcs_vaux, self.dcs_vbatctl):
            dcs.output(0.0, False)
        for dcl in (self.dcl, self.dclh, ):
            dcl.output(0.0, False)
        for rla in (
                self.rla_prog, self.rla_vbus, self.rla_batfuse,
                self.rla_fan, self.rla_shdwn1, self.rla_shdwn2):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dcl = logical_devices.dcl
        dclh = logical_devices.dclh
        sensor = tester.sensor
        self.diode = sensor.Vdc(dmm, high=7, low=8, rng=10, res=0.001)
        self.olock = sensor.Res(dmm, high=16, low=4, rng=10000, res=1)
        self.oacin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oflyld = sensor.Vac(dmm, high=15, low=7, rng=1000, res=0.01)
        self.ovcap = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.ovbus = sensor.Vdc(dmm, high=3, low=2, rng=1000, res=0.01)
        self.ovcc = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.001)
        self.ovout = sensor.Vdc(dmm, high=5, low=4, rng=100, res=0.001)
        self.ovbat = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self.ovaux = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self.ovbatfuse = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.ovctl = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.001)
        self.ovbatctl = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.001)
        self.ovdd = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.001)
        self.ofan = sensor.Vdc(dmm, high=13, low=5, rng=100, res=0.01)
        self.oshdwn = sensor.Vdc(dmm, high=14, low=6, rng=100, res=0.01)
        lo_lim, hi_lim = limits['Vout'].limit
        self.oAdjVout = sensor.AdjustAnalog(
            sensor=self.ovout,
            low=lo_lim, high=hi_lim,
            message=tester.translate('GENIUS-II Initial', 'AdjR39'),
            caption=tester.translate('GENIUS-II Initial', 'capAdjVout'))
        self.oOCP = sensor.Ramp(
            stimulus=dcl, sensor=self.ovout,
            detect_limit=(limits['InOCP'], ),
            start=33.6, stop=44.0, step=0.2)
        self.oOCP_H = sensor.Ramp(
            stimulus=dclh, sensor=self.ovout,
            detect_limit=(limits['InOCP'], ),
            start=33.6, stop=44.0, step=0.2)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_diode = Measurement(limits['DetectDiode'], sense.diode)
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_flyld = Measurement(limits['FlyLead'], sense.oflyld)
        self.dmm_acin = Measurement(limits['AcIn'], sense.oacin)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.ovbus)
        self.dmm_vcc = Measurement(limits['Vcc'], sense.ovcc)
        self.dmm_vccoff = Measurement(limits['VccOff'], sense.ovcc)
        self.dmm_vdd = Measurement(limits['Vdd'], sense.ovdd)
        self.dmm_vbatctl = Measurement(limits['VbatCtl'], sense.ovbatctl)
        self.dmm_vctl = Measurement(limits['Vctl'], sense.ovctl)
        self.dmm_voutpre = Measurement(limits['VoutPre'], sense.ovout)
        self.dmm_vout = Measurement(limits['Vout'], sense.ovout)
        self.dmm_voutoff = Measurement(limits['VoutOff'], sense.ovout)
        self.dmm_vbatpre = Measurement(limits['VbatPre'], sense.ovbat)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.ovbat)
        self.dmm_vbatocp = Measurement(limits['VbatOCP'], sense.ovbat)
        self.dmm_vaux = Measurement(limits['Vaux'], sense.ovaux)
        self.dmm_fanoff = Measurement(limits['FanOff'], sense.ofan)
        self.dmm_fanon = Measurement(limits['FanOn'], sense.ofan)
        self.ui_AdjVout = Measurement(limits['Notify'], sense.oAdjVout)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ramp_OCP_H = Measurement(limits['OCP'], sense.oOCP_H)


class SubTests():

    """SubTest Steps."""

    def __init__(self, dev, mes):
        """Create SubTest Step instances."""
        # Prepare:  Dc input, measure.
        self.prepare = tester.SubStep((
            tester.DcSubStep(setting=((dev.dcs_vaux, 12.0), ), output=True),
            tester.LoadSubStep(((dev.dcl_vbat, 0.4), ), output=True, delay=1.0),
            tester.MeasureSubStep((mes.dmm_diode, ), timeout=5),
            tester.LoadSubStep(((dev.dcl_vbat, 0.0), )),
            tester.DcSubStep(setting=(
                (dev.dcs_vaux, 0.0), (dev.dcs_vbatctl, 13.0), ), output=True),
            tester.RelaySubStep(((dev.rla_prog, True), )),
            tester.MeasureSubStep(
                (mes.dmm_lock, mes.dmm_vbatctl, mes.dmm_vdd, ), timeout=5),
            ))
        # Aux:  Dc input, measure.
        self.aux = tester.SubStep((
            tester.DcSubStep(setting=((dev.dcs_vaux, 13.8), ), output=True),
            tester.LoadSubStep(((dev.dcl, 0.1), ), output=True),
            tester.MeasureSubStep((mes.dmm_voutpre, mes.dmm_vaux, ), timeout=5),
            tester.DcSubStep(setting=((dev.dcs_vaux, 0.0), ), output=False),
            tester.LoadSubStep(((dev.dcl, 10.0), ), delay=2),
            tester.LoadSubStep(((dev.dcl, 0.0), )),
            ))
        # PowerUp:  Check flying leads, AC input, measure.
        self.pwrup = tester.SubStep((
            tester.AcSubStep(acs=dev.acsource, voltage=30.0, output=True),
            tester.MeasureSubStep((mes.dmm_flyld, ), timeout=5),
            tester.LoadSubStep(((dev.dcl, 0.1), )),
            tester.AcSubStep(acs=dev.acsource, voltage=240.0, delay=0.5),
            tester.MeasureSubStep(
                (mes.dmm_acin, mes.dmm_vbus, mes.dmm_vcc, mes.dmm_vbatpre,
                 mes.dmm_voutpre, mes.dmm_vdd, mes.dmm_vctl), timeout=5),
            ))
        # Shutdown:
        self.shdn = tester.SubStep((
            tester.MeasureSubStep((mes.dmm_fanoff, ), timeout=5),
            tester.RelaySubStep(((dev.rla_fan, True), )),
            tester.MeasureSubStep((mes.dmm_fanon, ), timeout=5),
            tester.RelaySubStep(((dev.rla_fan, False), )),
            tester.MeasureSubStep((mes.dmm_vout, ), timeout=5),
            tester.RelaySubStep(((dev.rla_shdwn2, True), )),
            tester.MeasureSubStep((mes.dmm_vccoff, mes.dmm_voutoff, ), timeout=5),
            tester.RelaySubStep(((dev.rla_shdwn2, False), )),
            tester.MeasureSubStep((mes.dmm_vout, ), timeout=5),
            ))
