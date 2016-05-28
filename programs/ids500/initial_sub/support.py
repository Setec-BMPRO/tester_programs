#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Test Program."""

from pydispatch import dispatcher
import sensor
import tester
from tester.devlogical import *
from tester.measure import *


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.dcs_Vcc = dcsource.DCSource(devices['DCS1'])
        self.dcs_Fan = dcsource.DCSource(devices['DCS5'])
        self.dcl_5V = dcload.DCLoad(devices['DCL1'])
        self.dcl_15Vp = dcload.DCLoad(devices['DCL2'])
        self.rla_Prog = relay.Relay(devices['RLA10'])
        self.rla_EnAux = relay.Relay(devices['RLA1'])
        self.rla_En15VpSw = relay.Relay(devices['RLA2'])

    def reset(self):
        """Reset instruments."""
        self.dcs_Vcc.output(0.0, False)
        self.rla_Prog.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits, picdev):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.oMirPIC = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.Lock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.oVsec5VuP = sensor.Vdc(dmm, high=19, low=1, rng=10, res=0.001)
        self.o5V = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.o15V = sensor.Vdc(dmm, high=23, low=1, rng=100, res=0.001)
        self.o_15V = sensor.Vdc(dmm, high=22, low=1, rng=100, res=0.001)
        self.o15Vp = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self.o20VL = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self.o_20V = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self.o15VpSw = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.001)
        self.oAcI5V = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.oAcI15V = sensor.Vdc(dmm, high=16, low=1, rng=10, res=0.001)
        self.oAuxTemp = sensor.Vdc(dmm, high=17, low=1, rng=10, res=0.001)
        self.oPwrGood = sensor.Vdc(dmm, high=18, low=1, rng=10, res=0.001)
        self.oPic_SwRev = share.ids500.Sensor(picdev, 'PIC-SwRev')
        self.oPic_MicroTemp = share.ids500.Sensor(picdev, 'PIC-MicroTemp')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirPIC.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.pgmPIC = Measurement(limits['Program'], sense.oMirPIC)
        self.dmm_Lock = Measurement(limits['FixtureLock'], sense.Lock)
        self.dmm_Vsec5VuP = Measurement(limits['5V'], sense.oVsec5VuP)
        self.dmm_5VOff = Measurement(limits['5VOff'], sense.o5V)
        self.dmm_15VpOff = Measurement(limits['15VpOff'], sense.o15Vp)
        self.dmm_15VpSwOff = Measurement(limits['15VpSwOff'], sense.o15VpSw)
        self.dmm_PwrGoodOff = Measurement(limits['PwrGoodOff'], sense.oPwrGood)
        self.dmm_20VL = Measurement(limits['20VL'], sense.o20VL)
        self.dmm__20V = Measurement(limits['-20V'], sense.o_20V)
        self.dmm_15V = Measurement(limits['15V'], sense.o15V)
        self.dmm__15V = Measurement(limits['-15V'], sense.o_15V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_15Vp = Measurement(limits['15Vp'], sense.o15Vp)
        self.dmm_PwrGood = Measurement(limits['PwrGood'], sense.oPwrGood)
        self.pic_SwRev = Measurement(limits['SwRev'], sense.oPic_SwRev)
        self.pic_MicroTemp = Measurement(
            limits['MicroTemp'], sense.oPic_MicroTemp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:
        dcs1 = DcSubStep(setting=((d.dcs_Vcc, 5.0),), output=True)
        msr1 = MeasureSubStep((m.dmm_Vsec5VuP, ), timeout=5)
        dcs2 = DcSubStep(setting=((d.dcs_Fan, 12.0),), output=True)
        acs1 = AcSubStep(acs=d.acsource, voltage=240.0, output=True, delay=3.0)
        msr2 = MeasureSubStep(
            (m.dmm_20VL, m.dmm__20V, m.dmm_5VOff, m.dmm_15V, m.dmm__15V,
             m.dmm_15VpOff, m.dmm_15VpSwOff, m.dmm_PwrGoodOff, ), timeout=5)
        self.pwrup_micro = Step((dcs1, msr1))
        self.pwrup_aux = Step((dcs2, acs1, msr2))
        # KeySw: Turn on KeySwitches, measure.
        dcs1 = DcSubStep(setting=((d.dcs_Vcc, 5.0),), output=True)
        rly1 = RelaySubStep(((d.rla_EnAux, True), ))
        msr1 = MeasureSubStep(
            (m.dmm_5V, m.dmm_15V, m.dmm__15V, m.dmm_15Vp, m.dmm_15VpSwOff,
             m.dmm_PwrGood, ), timeout=5)
        self.key_sw1 = Step((dcs1, rly1, msr1))
