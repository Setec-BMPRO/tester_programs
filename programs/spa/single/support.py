#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spa SINGLE Initial Test Program."""

import tester

# Scale factor for AC Input Current sensors.
#   0R1 current sense resistor
# FIXME: Put correct AC Current scale factor here.
_AC_I_SCALE = 5.0

# Scale factor for DSO LED Current sensors.
#   0R1 current sense resistor
#   Differential Amplifier
# FIXME: Put correct DSO scale factor here.
_DSO_LED_SCALE = 0.1


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.dso = tester.DSO(devices['DSO'])
        self.acsource = tester.ACSource(devices['ACS'])
        # DC Source that power the test fixture
        self.dcsAuxPos = tester.DCSource(devices['DCS4'])
        self.dcsAuxNeg = tester.DCSource(devices['DCS3'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        sensor = tester.sensor
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
        # LED current sensors using DSO.
        tbase = sensor.Timebase(
            range=0.05, main_mode=True, delay=0, centre_ref=True)
        trg = sensor.Trigger(
            ch=1, level=2.0, normal_mode=False, pos_slope=True)
        rdgs = ()
        for ch in range(1, 5):
            rdgs += (sensor.Vavg(ch=ch, position=ch, scale=_DSO_LED_SCALE), )
        leds = ()
        for ch in range(1, 5):
            leds += (sensor.Channel(ch=ch, mux=1, range=16.0, offset=8.0 - ch,
                     dc_coupling=True, att=1, bwlim=True), )
        self.dso_led = sensor.DSO(dso, leds, tbase, trg, rdgs)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
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
        # LED currents at 12Vac to 35Vac
        lims = (limits['Iled'], limits['Iled'],
                limits['Iled'], limits['Iled'])
        self.dso_led = Measurement(lims, sense.dso_led)
        # LED currents at 10.5Vac
        lim10s = (limits['Iled10'], limits['Iled10'],
                  limits['Iled10'], limits['Iled10'])
        self.dso_led10 = Measurement(lim10s, sense.dso_led)
