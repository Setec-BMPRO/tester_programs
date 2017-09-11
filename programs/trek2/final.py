#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Test Program."""

import os
import tester
from tester import (
    TestStep,
    LimitInteger, LimitBoolean, LimitRegExp
    )
import share
from . import console

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
CAN_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]

BIN_VERSION = '1.5.15833.150'   # Software binary version


LIMITS = (
    LimitRegExp('SwVer', '^{0}$'.format(BIN_VERSION.replace('.', r'\.'))),
    LimitBoolean('Notify', True),
    LimitInteger('ARM-level1', 1),
    LimitInteger('ARM-level2', 2),
    LimitInteger('ARM-level3', 3),
    LimitInteger('ARM-level4', 4),
    )


class Final(share.TestSequence):

    """Trek2 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('TunnelOpen', self._step_tunnel_open),
            TestStep('Display', self._step_display),
            TestStep('Tanks', self._step_test_tanks),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        # Switch on the USB hub & Serial ports
        dev['dcs_Vcom'].output(12.0, output=True)
        dev['dcs_Vin'].output(12.0, output=True, delay=9) # Wait for CAN bind

    @share.teststep
    def _step_tunnel_open(self, dev, mes):
        """Open console tunnel."""
        dev['trek2'].open()
        dev['trek2'].testmode(True)

    @share.teststep
    def _step_display(self, dev, mes):
        """Display tests."""
        self.measure(('trek2_SwVer', 'ui_YesNoSeg', 'ui_YesNoBklight', ))
        dev['trek2'].testmode(False)

    @share.teststep
    def _step_test_tanks(self, dev, mes):
        """Test all tanks one level at a time."""
        dev['trek2']['CONFIG'] = 0x7E00      # Enable all 4 tanks
        dev['trek2']['TANK_SPEED'] = 0.1     # Change update interval
        # No sensors - Tanks empty!
        tester.MeasureGroup(mes['arm_level1'], timeout=12)
        # 1 sensor
        dev['rla_s1'].set_on()
        tester.MeasureGroup(mes['arm_level2'], timeout=12)
        # 2 sensors
        dev['rla_s2'].set_on()
        tester.MeasureGroup(mes['arm_level3'], timeout=12)
        # 3 sensors
        dev['rla_s3'].set_on()
        tester.MeasureGroup(mes['arm_level4'], timeout=12)


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                # Power USB devices + Fixture Trek2.
                ('dcs_Vcom', tester.DCSource, 'DCS2'),
                # Power unit under test.
                ('dcs_Vin', tester.DCSource, 'DCS3'),
                # As the water level rises the "switches" close. The order of switch
                # closure does not matter, just the number closed.
                # The lowest bar always flashes. Closing these relays makes the other
                # bars come on.
                ('rla_s1', tester.Relay, 'RLA3'),
                ('rla_s2', tester.Relay, 'RLA4'),
                ('rla_s3', tester.Relay, 'RLA5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Connection to the Serial-to-CAN Trek2 inside the fixture
        ser_can = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        ser_can.port = CAN_PORT
        # CAN Console tunnel driver
        self['tunnel'] = share.console.OldConsoleCanTunnel(
            port=ser_can, simulation=self.fifo)
        # Trek2 Console driver (using the CAN Tunnel)
        self['trek2'] = console.TunnelConsole(port=self['tunnel'])

    def reset(self):
        """Reset instruments."""
        try:
            self['trek2'].close()
        except Exception:   # Ignore serial port close errors
            pass
        for src in ('dcs_Vin', 'dcs_Vcom'):
            self[src].output(0.0, output=False)
        for rla in ('rla_s1', 'rla_s2', 'rla_s3'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        trek2 = self.devices['trek2']
        sensor = tester.sensor
        self['oYesNoSeg'] = sensor.YesNo(
            message=tester.translate('trek2_final', 'AreSegmentsOn?'),
            caption=tester.translate('trek2_final', 'capSegments'))
        self['oYesNoBklight'] = sensor.YesNo(
            message=tester.translate('trek2_final', 'IsBacklightOk?'),
            caption=tester.translate('trek2_final', 'capBacklight'))
        self['otanks'] = (
            console.Sensor(trek2, 'TANK1'),
            console.Sensor(trek2, 'TANK2'),
            console.Sensor(trek2, 'TANK3'),
            console.Sensor(trek2, 'TANK4'),
            )
        # Console sensors
        self['oSwVer'] = console.Sensor(
            trek2, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('ui_YesNoSeg', 'Notify', 'oYesNoSeg', ''),
            ('ui_YesNoBklight', 'Notify', 'oYesNoBklight', ''),
            ('trek2_SwVer', 'SwVer', 'oSwVer', ''),
            ))
        self['arm_level1'] = []
        self['arm_level2'] = []
        self['arm_level3'] = []
        self['arm_level4'] = []
        meas = tester.Measurement
        for sens in self.sensors['otanks']:
            self['arm_level1'].append(
                meas(self.limits['ARM-level1'], sens))
            self['arm_level2'].append(
                meas(self.limits['ARM-level2'], sens))
            self['arm_level3'].append(
                meas(self.limits['ARM-level3'], sens))
            self['arm_level4'].append(
                meas(self.limits['ARM-level4'], sens))
