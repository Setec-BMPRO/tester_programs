#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""MB3 Initial Program."""

"""
pyupdi is a Python utility for programming AVR devices with UPDI interface
  using a standard TTL serial port.

  Connect RX and TX together with a suitable resistor and connect this node
  to the UPDI pin of the AVR device.

  Be sure to connect a common ground, and use a TTL serial adapter running at
   the same voltage as the AVR device.

                        Vcc                     Vcc
                        +-+                     +-+
                         |                       |
 +---------------------+ |                       | +--------------------+
 | Serial port         +-+                       +-+  AVR device        |
 |                     |      +----------+         |                    |
 |                  TX +------+   4k7    +---------+ UPDI               |
 |                     |      +----------+    |    |                    |
 |                     |                      |    |                    |
 |                  RX +----------------------+    |                    |
 |                     |                           |                    |
 |                     +--+                     +--+                    |
 +---------------------+  |                     |  +--------------------+
                         +-+                   +-+
                         GND                   GND

 Available from: https://github.com/mraardvark/pyupdi.git

"""

import inspect
import os

import tester
from tester import TestStep, LimitBetween, LimitDelta
import share
from . import config


class Initial(share.TestSequence):

    """MB3 Initial Test Program."""

    vaux = 13.0
    vsolar = 13.0

    limitdata = (
        LimitBetween('Vaux', 8.0, 13.5),
        LimitBetween('Vsolar', 8.0, 13.5),
        LimitDelta('5V', 5.0, 0.2),
        LimitBetween('Vbat', 12.5, 14.6),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerOn', self._step_power_on),
            TestStep('PgmARM', self.devices['program_arm'].program),
            TestStep('Initialise', self._step_initialise),
            TestStep('Output', self._step_output),
            )
        self.sernum = None

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Apply input power and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vaux'].output(self.vaux, output=True)
        dev['dcl_vbat'].output(0.1, True)
        self.measure(('dmm_vaux', 'dmm_5v', 'dmm_vbat'), timeout=5)

    @share.teststep
    def _step_initialise(self, dev, mes):
        """Initialise the unit."""
        # Cycle power to restart the unit
        dev['dcs_vaux'].output(0.0, delay=0.5)
        dev['dcs_vaux'].output(self.vaux, delay=1.0)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output of the unit."""
        mes['dmm_vbat'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS2'),
                ('dcs_vaux', tester.DCSource, 'DCS3'),
                ('dcs_vsol', tester.DCSource, 'DCS4'),
                ('dcl_vbat', tester.DCLoad, 'DCL1'),#        # Serial connection to the ARM console
#        arm_ser = serial.Serial(baudrate=115200, timeout=2.0)
#        # Set port separately - don't open until after programming
#        arm_ser.port = arm_port
#        self['arm'] = console.Console(arm_ser)

                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial port for the ARM. Used by programmer and ARM comms module.
        arm_port = share.fixture.port('999999', 'ARM')
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_arm'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, config.sw_image),
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Fixture USB hub power
        self['dcs_vcom'].output(9.0, output=True, delay=10)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_vaux', 'dcs_vsol'):
            self[dcs].output(0.0, False)
        self['dcl_vbat'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vaux'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vsolar'] = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.01)
        self['5V'] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01)
        self['vbat'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('mb3_initial', 'msgSnEntry'),
            caption=tester.translate('mb3_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vaux', 'Vaux', 'vaux', 'Aux power ok'),
            ('dmm_vsolar', 'Vsolar', 'vsolar', 'Solar input ok'),
            ('dmm_5v', '5V', '5V', '5V ok'),
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery output ok'),
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ))
