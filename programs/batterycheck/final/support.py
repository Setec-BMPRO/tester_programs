#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Final Test Program."""

from pydispatch import dispatcher

import share
import tester
import sensor
from . import limit


class LogicalDevices(object):

    """BatteryCheck Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_input = tester.DCSource(devices['DCS1'])
        # Serial connection to the BT device
        self.btport = share.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        self.btport.port = limit.BT_PORT
        # BT Radio driver
        self.bt = share.BtRadio(self.btport)

    def bt_puts(self,
                 string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the BT buffer only if FIFOs are enabled."""
        if self._fifo:
            self.btport.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.bt.close()
        self.dcs_input.output(0.0, output=False)


class Sensors(object):

    """BatteryCheck Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        self.oMirBT = sensor.Mirror()
        self.oMirSwVer = sensor.Mirror(rdgtype=sensor.ReadingString)
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.o12V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('batterycheck_final', 'msgSnEntry'),
            caption=tester.translate('batterycheck_final', 'capSnEntry'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirBT.flush()
        self.oMirSwVer.flush()


class Measurements(object):

    """BatteryCheck Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        self.BTscan = Measurement(limits['BTscan'], sense.oMirBT)
        self.BTpair = Measurement(limits['BTpair'], sense.oMirBT)
        self.SerNumARM = Measurement(limits['ARMSerNum'], sense.oMirBT)
        self.SwVerARM = Measurement(limits['ARMSwVer'], sense.oMirSwVer)
        self.dmm_12V = Measurement(limits['12V'], sense.o12V)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
