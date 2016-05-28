#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spa RGB/TRI Initial Test Program."""

import sensor
from tester.devlogical import *
from tester.measure import *


# Scale factor for AC Input Current sensors.
#   0R1 current sense resistor
_AC_I_SCALE = 5.0

# Scale factor for DSO LED Current sensors.
#   0R1 current sense resistor
#   Differential Amplifier
_DSO_LED_SCALE = 0.1


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self._devices = devices
        self.dmm = dmm.DMM(devices['DMM'])
        self.dso = dso.DSO(devices['DSO'])
        self.acsource = acsource.ACSource(devices['ACS'])
        # DC Source that power the test fixture
        self.dcsFixture = dcsource.DCSource(devices['DCS1'])
        self.dcsAuxPos = dcsource.DCSource(devices['DCS4'])
        self.dcsAuxNeg = dcsource.DCSource(devices['DCS3'])
        # Relay to drive the Arduino reset generator
        self.rla_isp = relay.Relay(devices['RLA1'])
        # Relay to reset all 4 uCs
        self.rla_rst = relay.Relay(devices['RLA2'])

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for rla in (self.rla_isp, self.rla_rst):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        # Mirror sensors for Programming result logging (1 per UUT)
        self.oMir1 = sensor.Mirror(1)
        self.oMir2 = sensor.Mirror(2)
        self.oMir3 = sensor.Mirror(3)
        self.oMir4 = sensor.Mirror(4)
        # AC input voltage of all UUTs
        self.oAcVin = sensor.Vac(
            dmm, high=1, low=1, rng=100, res=0.0001, position=(1, 2, 3, 4))
        # AC input current of each UUT
        self.oAcIin1 = sensor.Vac(
            dmm, high=2, low=1, rng=1, res=0.0001,
            position=1, scale=_AC_I_SCALE)
        self.oAcIin2 = sensor.Vac(
            dmm, high=3, low=1, rng=1, res=0.0001,
            position=2, scale=_AC_I_SCALE)
        self.oAcIin3 = sensor.Vac(
            dmm, high=4, low=1, rng=1, res=0.0001,
            position=3, scale=_AC_I_SCALE)
        self.oAcIin4 = sensor.Vac(
            dmm, high=5, low=1, rng=1, res=0.0001,
            position=4, scale=_AC_I_SCALE)
        # uC Vcc of each unit
        self.oVcc1 = sensor.Vdc(
            dmm, high=6, low=2, rng=10, res=0.001, position=1)
        self.oVcc2 = sensor.Vdc(
            dmm, high=7, low=2, rng=10, res=0.001, position=2)
        self.oVcc3 = sensor.Vdc(
            dmm, high=8, low=2, rng=10, res=0.001, position=3)
        self.oVcc4 = sensor.Vdc(
            dmm, high=9, low=2, rng=10, res=0.001, position=4)
        # LED current sensors using DSO - Same colour on all UUTs at once.
        #   Timebase is common to all colours
        tbase = sensor.Timebase(
            range=0.05, main_mode=True, delay=0, centre_ref=True)
        #   Trigger is common to all colours
        trg = sensor.Trigger(
            ch=1, level=5.0, normal_mode=False, pos_slope=True)
        #   Readings are common to all colours
        rdgs = ()
        for ch in range(1, 5):
            rdgs += (sensor.Vavg(ch=ch, position=ch, scale=_DSO_LED_SCALE), )
        #   RED channels
        reds = ()
        for ch in range(1, 5):
            reds += (sensor.Channel(ch=ch, mux=1, range=16.0,
                     offset=8.0 - ch, dc_coupling=True, att=1, bwlim=True), )
        #   GREEN channels
        greens = ()
        for ch in range(1, 5):
            greens += (sensor.Channel(ch=ch, mux=2, range=16.0,
                       offset=8.0 - ch, dc_coupling=True, att=1, bwlim=True), )
        #   BLUE channels
        blues = ()
        for ch in range(1, 5):
            blues += (sensor.Channel(ch=ch, mux=3, range=16.0,
                      offset=8.0 - ch, dc_coupling=True, att=1, bwlim=True), )
        #   RED sensor
        self.dso_red = sensor.DSO(dso, reds, tbase, trg, rdgs)
        #   GREEN sensor
        self.dso_green = sensor.DSO(dso, greens, tbase, trg, rdgs)
        #   BLUE sensor
        self.dso_blue = sensor.DSO(dso, blues, tbase, trg, rdgs)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        # Programming results
        pgmlim = limits['Program']
        self.pgm1 = Measurement(pgmlim, sense.oMir1)
        self.pgm2 = Measurement(pgmlim, sense.oMir2)
        self.pgm3 = Measurement(pgmlim, sense.oMir3)
        self.pgm4 = Measurement(pgmlim, sense.oMir4)
        # AC Input Voltages for all UUTs
        self.dmm_AcVin10 = Measurement(limits['AcVin10'], sense.oAcVin)
        self.dmm_AcVin12 = Measurement(limits['AcVin12'], sense.oAcVin)
        self.dmm_AcVin24 = Measurement(limits['AcVin24'], sense.oAcVin)
        self.dmm_AcVin32 = Measurement(limits['AcVin32'], sense.oAcVin)
        self.dmm_AcVin35 = Measurement(limits['AcVin35'], sense.oAcVin)
        # AC Input Currents UUT #1
        self.dmm_AcIin1_10 = Measurement(limits['AcIin10'], sense.oAcIin1)
        self.dmm_AcIin1_12 = Measurement(limits['AcIin12'], sense.oAcIin1)
        self.dmm_AcIin1_24 = Measurement(limits['AcIin24'], sense.oAcIin1)
        self.dmm_AcIin1_32 = Measurement(limits['AcIin32'], sense.oAcIin1)
        self.dmm_AcIin1_35 = Measurement(limits['AcIin35'], sense.oAcIin1)
        # AC Input Currents UUT #2
        self.dmm_AcIin2_10 = Measurement(limits['AcIin10'], sense.oAcIin2)
        self.dmm_AcIin2_12 = Measurement(limits['AcIin12'], sense.oAcIin2)
        self.dmm_AcIin2_24 = Measurement(limits['AcIin24'], sense.oAcIin2)
        self.dmm_AcIin2_32 = Measurement(limits['AcIin32'], sense.oAcIin2)
        self.dmm_AcIin2_35 = Measurement(limits['AcIin35'], sense.oAcIin2)
        # AC Input Currents UUT #3
        self.dmm_AcIin3_10 = Measurement(limits['AcIin10'], sense.oAcIin3)
        self.dmm_AcIin3_12 = Measurement(limits['AcIin12'], sense.oAcIin3)
        self.dmm_AcIin3_24 = Measurement(limits['AcIin24'], sense.oAcIin3)
        self.dmm_AcIin3_32 = Measurement(limits['AcIin32'], sense.oAcIin3)
        self.dmm_AcIin3_35 = Measurement(limits['AcIin35'], sense.oAcIin3)
        # AC Input Currents UUT #4
        self.dmm_AcIin4_10 = Measurement(limits['AcIin10'], sense.oAcIin4)
        self.dmm_AcIin4_12 = Measurement(limits['AcIin12'], sense.oAcIin4)
        self.dmm_AcIin4_24 = Measurement(limits['AcIin24'], sense.oAcIin4)
        self.dmm_AcIin4_32 = Measurement(limits['AcIin32'], sense.oAcIin4)
        self.dmm_AcIin4_35 = Measurement(limits['AcIin35'], sense.oAcIin4)
        # uC Vcc rails
        vcclim = limits['Vcc']
        self.dmm_Vcc1 = Measurement(vcclim, sense.oVcc1)
        self.dmm_Vcc2 = Measurement(vcclim, sense.oVcc2)
        self.dmm_Vcc3 = Measurement(vcclim, sense.oVcc3)
        self.dmm_Vcc4 = Measurement(vcclim, sense.oVcc4)
        # LED currents at 12Vac to 35Vac
        lims = (limits['Iled'], limits['Iled'], limits['Iled'], limits['Iled'])
        self.dso_red = Measurement(lims, sense.dso_red)
        self.dso_green = Measurement(lims, sense.dso_green)
        self.dso_blue = Measurement(lims, sense.dso_blue)
        # LED currents at 10.5Vac
        lim10s = (limits['Iled10'], limits['Iled10'],
                  limits['Iled10'], limits['Iled10'])
        self.dso_green10 = Measurement(lim10s, sense.dso_green)
