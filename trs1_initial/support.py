#!/usr/bin/env python3
"""Trs1 Initial Test Program.

        Logical Devices
        Sensors
        Measurements

"""
import tester
from tester.devlogical import *
from tester.measure import *

sensor = tester.sensor


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])

        self.dso = dso.DSO(devices['DSO'])

        self.dcs_Vin = dcsource.DCSource(devices['DCS1'])

        self.rla_brksw = relay.Relay(devices['RLA1'])   # ON == Asserted


    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        # Switch off DC Sources
        for dcs in (self.dcs_Vin, ):
            dcs.output(0.0, False)
        # Switch off all Relays
        for rla in (self.rla_brksw, ):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o5V = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oBrake = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.01)
        self.oLight = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self.oRemote = sensor.Vdc(dmm, high=5, low=1, rng=100, res=0.01)
        self.oGreen = sensor.Vdc(dmm, high=6, low=1, rng=100, res=0.01)
        self.oRed = sensor.Vdc(dmm, high=7, low=1, rng=100, res=0.01)

        tbase = sensor.Timebase(
            range=10.0, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=1, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = ()
        for ch in range(1, 3):
            rdgs += (sensor.Freq(ch=ch), )
        chans = ()
        for ch in range(1, 3):
            chans += (sensor.Channel(
                ch=ch, mux=1, range=16.0, offset=(-15.0 + ch * 10),
                dc_coupling=True, att=1, bwlim=True), )
        self.oTimer = sensor.DSO(
            dso, chans, tbase, trg, rdgs)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_brakeoff = Measurement(limits['BrakeOff'], sense.oBrake)
        self.dmm_brakeon = Measurement(limits['BrakeOn'], sense.oBrake)
        self.dmm_lightoff = Measurement(limits['LightOff'], sense.oLight)
        self.dmm_lighton = Measurement(limits['LightOn'], sense.oLight)
        self.dmm_remoteoff = Measurement(limits['BrakeOff'], sense.oRemote)
        self.dmm_remoteon = Measurement(limits['BrakeOn'], sense.oRemote)
        self.dmm_greenoff = Measurement(limits['LedOff'], sense.oGreen)
        self.dmm_greenon = Measurement(limits['LedOn'], sense.oGreen)
        self.dmm_redoff = Measurement(limits['LedOff'], sense.oRed)
        self.dmm_redon = Measurement(limits['LedOn'], sense.oRed)
        self.dso_timerled = Measurement(limits['Freq1'], sense.oTimer)
        self.dso_timeout = Measurement(limits['Freq2'], sense.oTimer)


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
        dcs1 = DcSubStep(
            setting=((d.dcs_Vin, 12.0), ), output=True)
        msr1 = MeasureSubStep((m.dmm_Vin, m.dmm_brakeoff, m.dmm_lightoff,
                             m.dmm_remoteoff), timeout=5)
        self.pwr_up = Step((dcs1, msr1, ))

        # BreakAway:
        rly1 = RelaySubStep(((d.rla_brksw, True), ))
        msr1 = MeasureSubStep((m.dmm_brakeon, m.dmm_lighton, m.dmm_remoteon,
                             m.dmm_greenon, m.dmm_redoff), timeout=5)
        dcs1 = DcSubStep(
            setting=((d.dcs_Vin, 10.0), ))
        msr2 = MeasureSubStep((m.dmm_greenoff, m.dmm_redon), timeout=5)
        dcs2 = DcSubStep(
            setting=((d.dcs_Vin, 12.0), ))
        msr3 = MeasureSubStep((m.dso_timerled, m.dso_timeout), timeout=5)
        self.brkaway = Step((rly1, msr1, dcs1, msr2, dcs2, msr3))
