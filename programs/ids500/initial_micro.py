#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Micro Initial Test Program."""

import os
import inspect
import tester
from tester import TestStep, LimitRegExp, LimitBetween
import share
from . import console


class InitialMicro(share.TestSequence):

    """IDS-500 Initial Micro Test Program."""

    # Serial port for the PIC.
    pic_port = share.port('017056', 'PIC')
    # Firmware image
    pic_hex_mic = 'ids_picMic_2.hex'
    # test limits
    limitdata = (
        LimitBetween('5V', 4.95, 5.05),
        LimitRegExp('SwRev', '2'),
        LimitRegExp('MicroTemp', 'MICRO Temp'),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Program', self._step_program, not self.fifo),
            TestStep('Comms', self._step_comms),
            )

    @share.teststep
    def _step_program(self, dev, mes):
        """Apply Vcc and program the board."""
        dev['dcs_vcc'].output(5.0, True)
        mes['dmm_vsec5VuP'](timeout=5)
        dev['program_picMic'].program()

    @share.teststep
    def _step_comms(self, dev, mes):
        """Communicate with the PIC console."""
        pic = dev['pic']
        pic.open()
        pic.clear_port()
        pic.expected = 1
        self.measure(('swrev', 'microtemp', ))


class Devices(share.LogicalDevices):

    """Micro Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcc', tester.DCSource, 'DCS1'),
                ('rla_mic', tester.Relay, 'RLA10'),
                ('rla_comm', tester.Relay, 'RLA13'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_picMic'] = share.ProgramPIC(
            InitialMicro.pic_hex_mic, folder, '18F4520', self['rla_mic'])
        # Serial connection to the console
        pic_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=19200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = InitialMicro.pic_port
        self['pic'] = console.Console(pic_ser)
        self['rla_comm'].set_on()
        self.add_closer(lambda: self['rla_comm'].set_off())

    def reset(self):
        """Reset instruments."""
        self['pic'].close()
        self['dcs_vcc'].output(0.0, False)
        self['rla_mic'].set_off()


class Sensors(share.Sensors):

    """Micro Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        pic = self.devices['pic']
        sensor = tester.sensor
        self['Vsec5VuP'] = sensor.Vdc(dmm, high=19, low=1, rng=10, res=0.001)
        self['SwRev'] = console.Sensor(
                pic, 'PIC-SwRev', rdgtype=sensor.ReadingString)
        self['MicroTemp'] = console.Sensor(
                pic, 'PIC-MicroTemp', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Micro Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_vsec5VuP', '5V', 'Vsec5VuP', ''),
            ('swrev', 'SwRev', 'SwRev', ''),
            ('microtemp', 'MicroTemp', 'MicroTemp', ''),
            ))
