#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import sensor
import tester

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.dso = tester.DSO(devices['DSO'])
        self.dcs_Vin = tester.DCSource(devices['DCS4'])
        # Pin for breakaway switch.
        self.rla_pin = tester.Relay(devices['RLA5'])   # ON == Asserted

    def reset(self):
        """Reset instruments."""
        self.dcs_Vin.output(0.0, False)
        self.rla_pin.set_off()


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
            range=3.0, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=1, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = (sensor.Freq(ch=1), )
        chan1 = (
            sensor.Channel(
                ch=1, mux=1, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        chan2 = (
            sensor.Channel(
                ch=1, mux=2, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        chan3 = (
            sensor.Channel(
                ch=1, mux=3, range=16.0, offset=6.0,
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
        Measurement = tester.Measurement
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_pinin = Measurement(limits['BrkawayPinIn'], sense.oPin)
        self.dmm_pinout = Measurement(limits['BrkawayPinOut'], sense.oPin)
        self.dmm_5VOff = Measurement(limits['5VOff'], sense.o5V)
        self.dmm_tp8off = Measurement(limits['TP8Off'], sense.oGreen)
        self.dmm_tp9off = Measurement(limits['TP9Off'], sense.oRed)
        self.dmm_5VOn = Measurement(limits['5VOn'], sense.o5V)
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
        self.dso_tp11 = Measurement(limits['FreqTP11'], sense.tp11)
        self.dso_tp3 = Measurement(limits['FreqTP3'], sense.tp3)
        self.dso_tp8 = Measurement(limits['FreqTP8'], sense.tp8)


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
        self.pwr_up = tester.SubStep((
            tester.RelaySubStep(((d.rla_pin, True), )),
            tester.DcSubStep(setting=((d.dcs_Vin, 12.0), ), output=True, delay=0.8),
            tester.MeasureSubStep(
                (m.dmm_vin, m.dmm_pinin, m.dmm_5VOff, m.dmm_brakeoff,
                 m.dmm_lightoff, m.dmm_remoteoff, m.dmm_tp8off,
                 m.dmm_tp9off), timeout=5),
            ))
        # BreakAway:
        self.brkaway1 = tester.SubStep((
            tester.RelaySubStep(((d.rla_pin, False), )),
            tester.MeasureSubStep(
                (m.dmm_pinout, m.dmm_5VOn, m.dmm_brakeon, m.dmm_lighton,
                 m.dmm_remoteon), timeout=5),
            ))
        self.brkaway2 = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Vin, 14.2), )),
            tester.MeasureSubStep((m.dmm_redoff, m.ui_YesNoGreen), timeout=5),
            ))
        self.brkaway3 = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Vin, 10.0), )),
            tester.MeasureSubStep((m.dmm_redon, m.dmm_greenoff), timeout=5),
            ))
        self.brkaway4 = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Vin, 11.2), )),
            tester.MeasureSubStep((m.dmm_greenon, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_Vin, 14.2), )),
            ))

