#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import sensor
import tester
from tester.devlogical import *
from tester.measure import *

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dso = dso.DSO(devices['DSO'])
        self.dcs_Vin = dcsource.DCSource(devices['DCS4'])
        # Pin for breakaway switch.
        self.rla_pin = relay.Relay(devices['RLA5'])   # ON == Asserted

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_Vin, ):
            dcs.output(0.0, False)
        for rla in (self.rla_pin, ):
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
        self.oVin = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.01)
        self.oPin = sensor.Vdc(dmm, high=10, low=4, rng=100, res=0.01)
        self.o5V = sensor.Vdc(dmm, high=11, low=4, rng=10, res=0.01)
        self.oBrake = sensor.Vdc(dmm, high=12, low=4, rng=100, res=0.01)
        self.oLight = sensor.Vdc(dmm, high=13, low=4, rng=100, res=0.01)
        self.oRemote = sensor.Vdc(dmm, high=14, low=4, rng=100, res=0.01)
        self.oGreen = sensor.Vdc(dmm, high=15, low=4, rng=100, res=0.01)
        self.oRed = sensor.Vdc(dmm, high=16, low=4, rng=100, res=0.01)
        self.oYesNoGreen = sensor.YesNo(
            message=translate('trs1_initial', 'IsGreenLedFlash?'),
            caption=translate('trs1_initial', 'capGreenLed'))
        tbase = sensor.Timebase(
            range=10.0, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=1, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = (sensor.Freq(ch=1), )
        chan1 = (
            sensor.Channel(
                ch=1, mux=0, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        chan2 = (
            sensor.Channel(
                ch=1, mux=1, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        chan3 = (
            sensor.Channel(
                ch=1, mux=2, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        self.tp11 = sensor.DSO(dso, chan1, tbase, trg, rdgs)
        self.tp3 = sensor.DSO(dso, chan2, tbase, trg, rdgs)
        self.tp8 = sensor.DSO(dso, chan3, tbase, trg, rdgs)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_pinin = Measurement(limits['PinIn'], sense.oPin)
        self.dmm_pinout = Measurement(limits['PinOut'], sense.oPin)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_brakeoff = Measurement(limits['BrakeOff'], sense.oBrake)
        self.dmm_brakeon = Measurement(limits['BrakeOn'], sense.oBrake)
        self.dmm_lightoff = Measurement(limits['LightOff'], sense.oLight)
        self.dmm_lighton = Measurement(limits['LightOn'], sense.oLight)
        self.dmm_remoteoff = Measurement(limits['RemoteOff'], sense.oRemote)
        self.dmm_remoteon = Measurement(limits['RemoteOn'], sense.oRemote)
        self.dmm_greenoff = Measurement(limits['GrnLedOff'], sense.oGreen)
        self.dmm_greenon = Measurement(limits['GrnLedOn'], sense.oGreen)
        self.dmm_redoff = Measurement(limits['RedLedOff'], sense.oRed)
        self.dmm_redon = Measurement(limits['RedLedOn'], sense.oRed)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.dso_tp11 = Measurement(limits['Freq1'], sense.tp11)
        self.dso_tp3 = Measurement(limits['Freq2'], sense.tp3)
        self.dso_tp8 = Measurement(limits['Freq1'], sense.tp8)


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
        rly1 = RelaySubStep(((d.rla_pin, True), ))
        dcs1 = DcSubStep(setting=((d.dcs_Vin, 12.5), ), output=True)
        msr1 = MeasureSubStep(
                (m.dmm_vin, m.dmm_pinin, m.dmm_brakeoff, m.dmm_lightoff,
                   m.dmm_remoteoff), timeout=5)
        self.pwr_up = Step((rly1, dcs1, msr1))

        # BreakAway:
        rly1 = RelaySubStep(((d.rla_pin, False), ))
        msr1 = MeasureSubStep(
                (m.dmm_pinout, m.dmm_5V, m.dmm_brakeon, m.dmm_lighton,
                m.dmm_remoteon, m.dmm_greenon, m.dmm_redoff), timeout=5)
        dcs1 = DcSubStep(setting=((d.dcs_Vin, 14.5), ))
        msr2 = MeasureSubStep((m.dmm_redoff, m.ui_YesNoGreen), timeout=5)
        dcs2 = DcSubStep(setting=((d.dcs_Vin, 10.0), ))
        msr3 = MeasureSubStep((m.dmm_redon, m.dmm_greenoff), timeout=5)
        dcs3 = DcSubStep(setting=((d.dcs_Vin, 11.0), ))
        msr4 = MeasureSubStep((m.dmm_greenon, ), timeout=5)
        dcs4 = DcSubStep(setting=((d.dcs_Vin, 14.5), ))
        msr5 = MeasureSubStep((m.dso_tp11, m.dso_tp3, m.dso_tp8), timeout=5)
        self.brkaway = Step(
            (rly1, msr1, dcs1, msr2, dcs2, msr3, dcs3, msr4, dcs4, msr5))
