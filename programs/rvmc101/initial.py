#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMC101 Initial Test Program."""

import inspect
import os

import tester

import share
from . import config


class Initial(share.TestSequence):

    """RVMC101 Initial Test Program."""

    limitdata = (
        tester.LimitDelta('Vin', 12.0, 0.5, doc='Input voltage present'),
        tester.LimitDelta('3V3', 3.3, 0.1, doc='3V3 present'),
        tester.LimitDelta('5V', 5.0, 0.2, doc='5V present'),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        # This is a multi-unit parallel program so we can't stop on errors.
        self.stop_on_failrdg = False
        # This is a multi-unit parallel program so we can't raise exceptions.
        tester.Tester.measurement_failure_exception = False
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program),
            tester.TestStep('CanBus', self._step_canbus),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        dev['rla_reset'].set_on()   # Hold device in RESET
        dev['dcs_vin'].output(12.0, output=True)
        mes['dmm_vin'](timeout=5)
        for pos in range(self.per_panel):
            self.measure(mes['dmm'][pos], timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM."""
        pgm = dev['program_arm']
        sel = dev['selector']
        for pos in range(self.per_panel):
            sel[pos].set_on()
            pgm.position = (pos + 1, )
            pgm.program
            sel[pos].set_off()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the CAN Bus."""
        dev['rla_reset'].pulse(0.1)
        candev = dev['can']
        sel = dev['selector']
#        import time
#        time.sleep(1)
#        self.send_led_display(candev)
#        time.sleep(1)

        for pos in range(self.per_panel):
            sel[pos].set_on()
            candev.flush_can()      # Flush all waiting packets
            try:
                candev.read_can()
                result = True
            except tester.devphysical.can.SerialToCanError:
                result = False
            mes['can_active'].sensor.position = (pos + 1, )
            mes['can_active'].sensor.store(result)
            mes['can_active']()
            sel[pos].set_off()

#    @staticmethod
#    def send_led_display(serial2can):
#        """Send a LED_DISPLAY packet."""
#        pkt = tester.devphysical.can.RVCPacket()
#        msg = pkt.header.message
#        msg.priority = 6
#        msg.reserved = 0
#        msg.DGN = tester.devphysical.can.RVCDGN.setec_led_display.value
#        msg.SA = tester.devphysical.can.RVCDeviceID.rvmn101.value
#        sequence = 1
#        # Show "88" on the display (for about 100msec)
#        # The 1st packet we send is ignored due to no previous sequence number
#        pkt.data.extend(b'\x01\xff\xff\xff\xff\xff')
#        pkt.data.extend(bytes([sequence & 0xff]))
#        pkt.data.extend(bytes([sum(pkt.data) & 0xff]))
#        serial2can.send('t{0}'.format(pkt))
#        sequence += 1
#        # The 2nd packet WILL be acted upon
#        pkt.data.clear()
#        pkt.data.extend(b'\x01\xFF\xFF\xFF\xFF\xFF')
#        pkt.data.extend(bytes([sequence & 0xff]))
#        pkt.data.extend(bytes([sum(pkt.data) & 0xff]))
#        serial2can.send('t{0}'.format(pkt))
#        sequence += 1


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS1'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_pos1', tester.Relay, 'RLA3'),
                ('rla_pos2', tester.Relay, 'RLA4'),
                ('rla_pos3', tester.Relay, 'RLA5'),
                ('rla_pos4', tester.Relay, 'RLA6'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['can'] = self.physical_devices['_CAN']
        self['can'].rvc_mode = True
        self['can'].verbose = True
        self.add_closer(self.close_can)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        arm_port = share.fixture.port('032870', 'ARM')
        self['program_arm'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, config.SW_IMAGE),
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        self['selector'] = [
            self['rla_pos1'], self['rla_pos2'],
            self['rla_pos3'], self['rla_pos4']]

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        for rla in (
            'rla_reset', 'rla_boot', 'rla_pos1',
            'rla_pos2', 'rla_pos3', 'rla_pos4'):
            self[rla].set_off()

    def close_can(self):
        """Restore CAN interface to default settings."""
        self['can'].rvc_mode = False
        self['can'].verbose = False


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(
                dmm, high=1, low=1, rng=100, res=0.01, position=(1, 2, 3, 4))
        self['a_3v3'] = sensor.Vdc(
                dmm, high=2, low=1, rng=10, res=0.01, position=1)
        self['b_3v3'] = sensor.Vdc(
                dmm, high=3, low=1, rng=10, res=0.01, position=2)
        self['c_3v3'] = sensor.Vdc(
                dmm, high=4, low=1, rng=10, res=0.01, position=3)
        self['d_3v3'] = sensor.Vdc(
                dmm, high=5, low=1, rng=10, res=0.01, position=4)
        self['a_5v'] = sensor.Vdc(
                dmm, high=6, low=1, rng=10, res=0.01, position=1)
        self['b_5v'] = sensor.Vdc(
                dmm, high=7, low=1, rng=10, res=0.01, position=2)
        self['c_5v'] = sensor.Vdc(
                dmm, high=8, low=1, rng=10, res=0.01, position=3)
        self['d_5v'] = sensor.Vdc(
                dmm, high=9, low=1, rng=10, res=0.01, position=4)
        self['MirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3a', '3V3', 'a_3v3', '3V3 rail voltage'),
            ('dmm_3v3b', '3V3', 'b_3v3', '3V3 rail voltage'),
            ('dmm_3v3c', '3V3', 'c_3v3', '3V3 rail voltage'),
            ('dmm_3v3d', '3V3', 'd_3v3', '3V3 rail voltage'),
            ('dmm_5va', '5V', 'a_5v', '5V rail voltage'),
            ('dmm_5vb', '5V', 'b_5v', '5V rail voltage'),
            ('dmm_5vc', '5V', 'c_5v', '5V rail voltage'),
            ('dmm_5vd', '5V', 'd_5v', '5V rail voltage'),
            ('can_active', 'CANok', 'MirCAN', 'CAN bus traffic seen'),
            ))
        self['dmm'] = (
            ('dmm_3v3a', 'dmm_5va'),
            ('dmm_3v3b', 'dmm_5vb'),
            ('dmm_3v3c', 'dmm_5vc'),
            ('dmm_3v3d', 'dmm_5vd'),
            )
