#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        for ld in (self.dcl_12V, self.dcl_24V, self.dcl_5V, self.dcl_12V2):
            ld.output(0.0, False)
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


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        m = measurements
        # PowerUp: Apply 240Vac, set min load, measure.
        self.pwr_up = tester.SubStep((
            tester.LoadSubStep(
                ((d.dcl_5V, 0.0), (d.dcl_24V, 0.1), (d.dcl_12V, 3.5),
                 (d.dcl_12V2, 0.5)), output=True),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=1.0),
            tester.MeasureSubStep(
                (m.dmm_5V, m.dmm_24Voff, m.dmm_12Voff, ), timeout=5),
            tester.RelaySubStep(((d.rla_12V2off, True), )),
            tester.MeasureSubStep((m.dmm_12V2off, ), timeout=5),
            ))
        # PowerOn: Turn on, measure at min load.
        self.pwr_on = tester.SubStep((
            tester.RelaySubStep(((d.rla_pson, True), )),
            tester.MeasureSubStep(
                (m.dmm_24Von, m.dmm_12Von, m.dmm_12V2off,
                 m.dmm_PwrFailOff, ), timeout=5),
            tester.RelaySubStep(((d.rla_12V2off, False), )),
            tester.MeasureSubStep((m.dmm_12V2on, m.dmm_Iecon, ), timeout=5),
            tester.MeasureSubStep((m.ui_YesNoMains, )),
            ))
        # Full Load: Apply full load, measure.
        # 115Vac Full Load: 115Vac, measure.
        mss = tester.MeasureSubStep(
            (m.dmm_5V, m.dmm_24Von, m.dmm_12Von, m.dmm_12V2on,), timeout=5)
        self.full_load = tester.SubStep((
            tester.LoadSubStep(
                ((d.dcl_5V, 2.5), (d.dcl_24V, 5.0),
                 (d.dcl_12V, 15.0), (d.dcl_12V2, 7.0)), delay=0.5),
            mss,
            ))
        self.full_load_115 = tester.SubStep((
            tester.AcSubStep(acs=d.acsource, voltage=115.0, delay=0.5),
            mss,
            ))
        # PowerOff: Set min load, switch off, measure.
        self.pwr_off = tester.SubStep((
            tester.LoadSubStep(
                ((d.dcl_5V, 0.5), (d.dcl_24V, 0.5), (d.dcl_12V, 4.0))),
            tester.MeasureSubStep(
                (m.ui_NotifyPwrOff, m.dmm_Iecoff, m.dmm_24Voff,)),
            ))
