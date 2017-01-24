#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Final Test Program."""

import logging
import tester
import share


class Final(tester.TestSequence):

    """GEN8 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.devices = physical_devices
        self.support = None

    def open(self, sequence=None):
        """Prepare for testing."""
        self._logger.info('Open')
        self.support = Support(self.devices)
        sequence = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('PowerOn', self._step_pwron),
            tester.TestStep('FullLoad', self._step_fullload),
            tester.TestStep('115V', self._step_fullload115),
            tester.TestStep('Poweroff', self._step_pwroff),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.support.reset()

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power Up step."""
        tester.dcl_substep(
            ((dev.dcl_5v, 0.0), (dev.dcl_24v, 0.1), (dev.dcl_12v, 3.5),
             (dev.dcl_12v2, 0.5), ),
            output=True)
        dev.acsource.output(voltage=240.0, output=True, delay=1.0)
        tester.MeasureGroup(
            (mes.dmm_5v, mes.dmm_24voff, mes.dmm_12voff, ), timeout=5)
        tester.relay_substep(((dev.rla_12v2off, True), ))
        tester.MeasureGroup((mes.dmm_12v2off, ), timeout=5)

    @share.teststep
    def _step_pwron(self, dev, mes):
        """Power On step."""
        tester.relay_substep(((dev.rla_pson, True), ))
        tester.MeasureGroup(
            (mes.dmm_24von, mes.dmm_12von, mes.dmm_12v2off,
             mes.dmm_pwrfailoff, ),
            timeout=5)
        tester.relay_substep(((dev.rla_12v2off, False), ))
        tester.MeasureGroup(
            (mes.dmm_12v2on, mes.dmm_iec_on, ),
            timeout=5)
        tester.MeasureGroup((mes.ui_yesno_mains, ))

    @share.teststep
    def _step_fullload(self, dev, mes):
        """Full Load step."""
        tester.dcl_substep(
            ((dev.dcl_5v, 2.5), (dev.dcl_24v, 5.0),
             (dev.dcl_12v, 15.0), (dev.dcl_12v2, 7.0), ),
            delay=0.5)
        tester.MeasureGroup(
            (mes.dmm_5v, mes.dmm_24von, mes.dmm_12von, mes.dmm_12v2on, ),
            timeout=5)

    @share.teststep
    def _step_fullload115(self, dev, mes):
        """115Vac step."""
        dev.acsource.output(voltage=115.0, delay=0.5)
        tester.MeasureGroup(
            (mes.dmm_5v, mes.dmm_24von, mes.dmm_12von, mes.dmm_12v2on, ),
            timeout=5)

    @share.teststep
    def _step_pwroff(self, dev, mes):
        """Power Off step."""
        tester.dcl_substep(
            ((dev.dcl_5v, 0.5), (dev.dcl_24v, 0.5), (dev.dcl_12v, 4.0), ))
        tester.MeasureGroup(
            (mes.ui_notify_pwroff, mes.dmm_iec_off, mes.dmm_24voff, ))


class Support():

    """Supporting data."""

    def __init__(self, physical_devices):
        """Create all supporting classes."""
        self.devices = LogicalDevices(physical_devices)
        self.sensors = Sensors(self.devices)
        self.limits = tester.limitdict((
            tester.LimitHiLoDelta('Iecon', (240, 10)),
            tester.LimitLo('Iecoff', 10),
            tester.LimitHiLo('5V', (4.998, 5.202)),
            tester.LimitLo('24Voff', 0.5),
            tester.LimitLo('12Voff', 0.5),
            tester.LimitLo('12V2off', 0.5),
            tester.LimitHiLo('24Von', (22.80, 25.44)),
            tester.LimitHiLo('12Von', (11.8755, 12.4845)),
            tester.LimitHiLo('12V2on', (11.8146, 12.4845)),
            tester.LimitHi('PwrFailOff', 11.0),
            tester.LimitBoolean('Notify', True),
            ))
        self.measurements = Measurements(self.sensors, self.limits)

    def reset(self):
        """Reset instruments."""
        self.devices.reset()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcl_24v = tester.DCLoad(devices['DCL1'])
        self.dcl_12v = tester.DCLoad(devices['DCL2'])
        self.dcl_12v2 = tester.DCLoad(devices['DCL3'])
        self.dcl_5v = tester.DCLoad(devices['DCL4'])
        self.rla_12v2off = tester.Relay(devices['RLA2'])
        self.rla_pson = tester.Relay(devices['RLA3'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for load in (self.dcl_12v, self.dcl_24v, self.dcl_5v, self.dcl_12v2):
            load.output(0.0, False)
        for rla in (self.rla_12v2off, self.rla_pson):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sen = tester.sensor
        self.iec = sen.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.o5v = sen.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        self.o24v = sen.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.o12v = sen.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o12v2 = sen.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.pwrfail = sen.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        self.yn_mains = sen.YesNo(
            message=tester.translate('gen8_final', 'IsSwitchGreen?'),
            caption=tester.translate('gen8_final', 'capSwitchGreen'))
        self.not_pwroff = sen.Notify(
            message=tester.translate('gen8_final', 'msgSwitchOff'),
            caption=tester.translate('gen8_final', 'capSwitchOff'))


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self.limits = limits
        maker = self._maker
        self.dmm_iec_on = maker('Iecon', sense.iec)
        self.dmm_iec_off = maker('Iecoff', sense.iec)
        self.dmm_5v = maker('5V', sense.o5v)
        self.dmm_24voff = maker('24Voff', sense.o24v)
        self.dmm_12voff = maker('12Voff', sense.o12v)
        self.dmm_12v2off = maker('12V2off', sense.o12v2)
        self.dmm_24von = maker('24Von', sense.o24v)
        self.dmm_12von = maker('12Von', sense.o12v)
        self.dmm_12v2on = maker('12V2on', sense.o12v2)
        self.dmm_pwrfailoff = maker('PwrFailOff', sense.pwrfail)
        self.ui_yesno_mains = maker('Notify', sense.yn_mains)
        self.ui_notify_pwroff = maker('Notify', sense.not_pwroff)

    def _maker(self, limitname, sensor):
        """Create a Measurement.

        @param limitname Test Limit name
        @param sensor Sensor to use
        @return tester.Measurement instance

        """
        return tester.Measurement(self.limits[limitname], sensor)
