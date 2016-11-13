#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Final Test Program."""

import tester


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_24V = tester.DCLoad(devices['DCL1'])
        self.dcl_12V = tester.DCLoad(devices['DCL2'])
        self.dcl_12V2 = tester.DCLoad(devices['DCL3'])
        self.dcl_5V = tester.DCLoad(devices['DCL4'])
        self.rla_12V2off = tester.Relay(devices['RLA2'])
        self.rla_pson = tester.Relay(devices['RLA3'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for load in (self.dcl_12V, self.dcl_24V, self.dcl_5V, self.dcl_12V2):
            load.output(0.0, False)
        for rla in (self.rla_12V2off, self.rla_pson):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oIec = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.o5V = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self.o24V = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12V2 = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.oPwrFail = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self.oYesNoMains = sensor.YesNo(
            message=tester.translate('gen8_final', 'IsSwitchGreen?'),
            caption=tester.translate('gen8_final', 'capSwitchGreen'))
        self.oNotifyPwrOff = sensor.Notify(
            message=tester.translate('gen8_final', 'msgSwitchOff'),
            caption=tester.translate('gen8_final', 'capSwitchOff'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self._limits = limits
        maker = self._maker
        self.dmm_Iecon = maker('Iecon', sense.oIec)
        self.dmm_Iecoff = maker('Iecoff', sense.oIec)
        self.dmm_5V = maker('5V', sense.o5V)
        self.dmm_24Voff = maker('24Voff', sense.o24V)
        self.dmm_12Voff = maker('12Voff', sense.o12V)
        self.dmm_12V2off = maker('12V2off', sense.o12V2)
        self.dmm_24Von = maker('24Von', sense.o24V)
        self.dmm_12Von = maker('12Von', sense.o12V)
        self.dmm_12V2on = maker('12V2on', sense.o12V2)
        self.dmm_PwrFailOff = maker('PwrFailOff', sense.oPwrFail)
        self.ui_YesNoMains = maker('Notify', sense.oYesNoMains)
        self.ui_NotifyPwrOff = maker('Notify', sense.oNotifyPwrOff)

    def _maker(self, limitname, sensor):
        """Create a Measurement.

        @param limitname Test Limit name
        @param sensor Sensor to use
        @return tester.Measurement instance

        """
        return tester.Measurement(self._limits[limitname], sensor)
