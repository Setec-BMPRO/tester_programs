#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GENIUS-II and GENIUS-II-H Initial Test Program."""
import os
import inspect

import share
import tester
import sensor
from . import limit

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_vout = tester.DCSource(devices['DCS1'])
        self.dcs_vbat = tester.DCSource(devices['DCS2'])
        self.dcs_vaux = tester.DCSource(devices['DCS4'])
        self.dcs_vbatctl = tester.DCSource(devices['DCS5'])
        dcl_vout = tester.DCLoad(devices['DCL1'])
        dcl_vbat = tester.DCLoad(devices['DCL5'])
        self.dcl = tester.DCLoadParallel(((dcl_vout, 29), (dcl_vbat, 14)))
        self.dclh = tester.DCLoadParallel(((dcl_vout, 5), (dcl_vbat, 30)))
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
            limit.PIC_HEX, folder, '16F1828', self.rla_prog)

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_vout, self.dcs_vbat, self.dcs_vaux,
                        self.dcs_vbatctl):
            dcs.output(0.0, False)
        for dcl in (self.dcl, self.dclh, ):
            dcl.output(0.0, False)
        for rla in (self.rla_prog, self.rla_vbus, self.rla_batfuse,
                        self.rla_fan, self.rla_shdwn1, self.rla_shdwn2):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dcl = logical_devices.dcl
        dclh = logical_devices.dclh
        self.olock = sensor.Res(dmm, high=16, low=8, rng=10000, res=1)
        self.oacin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.oflyld = sensor.Vac(dmm, high=15, low=7, rng=1000, res=0.01)
        self.ovcap = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.ovbus = sensor.Vdc(dmm, high=3, low=2, rng=1000, res=0.01)
        self.ovcc = sensor.Vdc(dmm, high=4, low=2, rng=100, res=0.001)
        self.ovout = sensor.Vdc(dmm, high=5, low=4, rng=100, res=0.001,
                                                        nplc=10)
        self.ovbat = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self.ovaux = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self.ovbatfuse = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self.ovctl = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.001)
        self.ovbatctl = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.001)
        self.ovdd = sensor.Vdc(dmm, high=11, low=3, rng=100, res=0.001)
        self.ofan = sensor.Vdc(dmm, high=13, low=5, rng=100, res=0.001)
        self.oshdwn = sensor.Vdc(dmm, high=14, low=6, rng=100, res=0.001)
        lo_lim, hi_lim = limits['Vout'].limit
        self.oAdjVout = sensor.AdjustAnalog(
            sensor=self.ovout,
            low=lo_lim, high=hi_lim,
            message=tester.translate('GENIUS-II Initial', 'AdjR39'),
            caption=tester.translate('GENIUS-II Initial', 'capAdjVout'))
        self.oOCP = sensor.Ramp(
            stimulus=dcl, sensor=self.ovout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)
        self.oOCP_H = sensor.Ramp(
            stimulus=dclh, sensor=self.ovout,
            detect_limit=(limits['InOCP'], ),
            start=32.0, stop=48.0, step=0.2, delay=0.1)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_vbatctl = Measurement(limits['VbatCtl'], sense.ovbatctl)
        self.dmm_vdd = Measurement(limits['Vdd'], sense.ovdd)
        self.dmm_vout = Measurement(limits['Vout'], sense.ovout)
        self.dmm_voutoff = Measurement(limits['VoutOff'], sense.ovout)
        self.dmm_vaux = Measurement(limits['Vaux'], sense.ovaux)
        self.dmm_flyld = Measurement(limits['FlyLead'], sense.oflyld)
        self.dmm_acin = Measurement(limits['AcIn'], sense.oacin)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.ovbus)
        self.dmm_vcc = Measurement(limits['Vcc'], sense.ovcc)
        self.dmm_vccoff = Measurement(limits['VccOff'], sense.ovcc)
        self.dmm_vbatpre = Measurement(limits['VoutPre'], sense.ovbat)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.ovbat)
        self.dmm_voutpre = Measurement(limits['VoutPre'], sense.ovout)
        self.dmm_vout = Measurement(limits['Vout'], sense.ovout)
        self.dmm_vctl = Measurement(limits['Vctl'], sense.ovctl)
        self.dmm_fanoff = Measurement(limits['FanOff'], sense.ofan)
        self.dmm_fanon = Measurement(limits['FanOn'], sense.ofan)
        self.ui_AdjVout = Measurement(limits['Notify'], sense.oAdjVout)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)
        self.ramp_OCP_H = Measurement(limits['OCP'], sense.oOCP_H)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # Aux:  Dc input, measure.
        self.aux = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_vaux, 13.8), ), output=True),
            tester.LoadSubStep(((d.dcl, 0.5), )),
            tester.MeasureSubStep((m.dmm_vout, m.dmm_vaux, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_vaux, 0.0), ), output=False),
            tester.LoadSubStep(((d.dcl, 0.0), )),
            ))
        # PowerUp:  Check flying leads, AC input, measure.
        self.pwrup = tester.SubStep((
            tester.AcSubStep(acs=d.acsource, voltage=30.0, output=True),
            tester.MeasureSubStep((m.dmm_flyld, ), timeout=5),
            tester.LoadSubStep(((d.dcl, 0.5), )),
            tester.AcSubStep(acs=d.acsource, voltage=240.0, delay=0.5),
            tester.MeasureSubStep((m.dmm_acin, m.dmm_vbus, m.dmm_vcc,
                                m.dmm_vbatpre, m.dmm_voutpre, m.dmm_vdd,
                                m.dmm_vctl), timeout=5),
            ))
        # Shutdown:
        self.Shdn = tester.SubStep((
            tester.MeasureSubStep((m.dmm_fanoff, ), timeout=5),
            tester.RelaySubStep(((d.rla_fan, True), )),
            tester.MeasureSubStep((m.dmm_fanon, ), timeout=5),
            tester.RelaySubStep(((d.rla_fan, False), )),
            tester.MeasureSubStep((m.dmm_vout, ), timeout=5),
            tester.RelaySubStep(((d.rla_shdwn2, True), )),
            tester.MeasureSubStep((m.dmm_vccoff, m.dmm_voutoff, ), timeout=5),
            tester.RelaySubStep(((d.rla_shdwn2, False), )),
            tester.MeasureSubStep((m.dmm_vout, ), timeout=5),
            ))
