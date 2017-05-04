#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Final Test Program."""

import os
from pydispatch import dispatcher
import tester
from tester.testlimit import lim_hilo_delta, lim_string, lim_boolean
import share

ARM_VERSION = '1.7.4080'        # Software binary version

BT_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM9'}[os.name]

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('12V', 12.0, 0.1),
    lim_boolean('BTscan', True),
    lim_boolean('BTpair', True),
    lim_boolean('ARMSerNum', True),
    lim_string('ARMSwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Final(tester.TestSequence):

    """BatteryCheck Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('TestBlueTooth', self._step_test_bluetooth),
            )
        self._limits = LIMITS
        global d, s, m
        d = LogicalDevices(self.physical_devices, self.fifo)
        s = Sensors(d)
        m = Measurements(s, self._limits)
        self._sernum = None

    def close(self):
        """Finished testing."""
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_power_up(self):
        """Power the battery check."""
        self.fifo_push(((s.oSnEntry, ('A1509020010', )), (s.o12V, 12.0), ))

        self._sernum = share.get_sernum(
            self.uuts, self._limits['SerNum'], m.ui_SnEntry)
        d.dcs_input.output(12.0, output=True)
        m.dmm_12V.measure(timeout=5)

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function.

        Scan for BT devices and match against serial number.

        """
        d.bt.puts('OK\r\n', preflush=2)
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('+RDDSRES=112233445566,BCheck A1509020010,2,3\r\n')
        d.bt.puts('+RDDSCNF=0\r\n')
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('+RPCI=\r\n') # Ask for PIN
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('+RUCE=\r\n') # Ask for 6-digit verify
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('+RCCRCNF=500,0000,0\r\n') # Pair response
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts(
            '{"jsonrpc": "2.0","id": 8256,'
            '"result": {"HardwareVersion": "2.0",'
            '"SoftwareVersion": "' + ARM_VERSION + '",'
            '"SerialID": "A1509020010"}}\r\n', preflush=1)
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('OK\r\n', preflush=1)
        d.bt.puts('+RDII\r\n')

        self._logger.debug('Testing Bluetooth Serial: "%s"', self._sernum)
        d.bt.open()
        found = d.bt.scan(self._sernum)
        s.oMirBT.store(found)
        m.BTscan.measure()
        try:
            d.bt.pair()
        except share.BtError:
            _paired = False
        _paired = True
        s.oMirBT.store(_paired)
        m.BTpair.measure()
        d.bt.data_mode_enter()
        _info = d.bt.jsonrpc('GetSystemInfo')
        s.oMirSwVer.store((_info['SoftwareVersion'], ))
        m.SwVerARM.measure()
        s.oMirBT.store(_info['SerialID'] == self._sernum)
        m.SerNumARM.measure()
        d.bt.data_mode_escape()
        d.bt.unpair()


class LogicalDevices():

    """BatteryCheck Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self.fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_input = tester.DCSource(devices['DCS2'])
        # Serial connection to the BT device
        self.btport = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=2)
        # Set port separately, as we don't want it opened yet
        self.btport.port = BT_PORT
        # BT Radio driver
        self.bt = share.BtRadio(self.btport)

    def reset(self):
        """Reset instruments."""
        self.bt.close()
        self.dcs_input.output(0.0, output=False)


class Sensors():

    """BatteryCheck Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dmm = logical_devices.dmm
        sensor = tester.sensor
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


class Measurements():

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
