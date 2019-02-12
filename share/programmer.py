#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmer for devices."""

import os
import subprocess
import tester
import isplpc
import serial


class PIC():

    """Microchip PIC programmer using a PicKit3."""

    pic_binary = {          # Executable to use
        'posix': 'pickit3',
        'nt': r'C:\Program Files\Microchip-PK3\PK3CMD.exe',
        }[os.name]
    limitname = 'Program'   # Testlimit name to use

    def __init__(self, hexfile, working_dir, device_type, relay):
        """Create a programmer.

        @param hexfile HEX filename
        @param working_dir Working directory
        @param device_type PIC device type
        @param relay Relay device to connect programmer to target

        """
        self.hexfile = hexfile
        self.working_dir = working_dir
        self.device_type = device_type
        self.relay = relay
        self.measurement = tester.Measurement(
            tester.LimitInteger(
                self.limitname, 0, doc='Programming succeeded'),
            tester.sensor.Mirror()
            )
        self.process = None

    def program(self):
        """Program a device and return when finished."""
        self.program_begin()
        self.program_wait()

    def program_begin(self):
        """Begin device programming."""
        command = [
            self.pic_binary,
            '/P{0}'.format(self.device_type),
            '/F{0}'.format(self.hexfile),
            '/E',
            '/M',
            '/Y'
            ]
        self.relay.set_on()
        self.process = subprocess.Popen(command, cwd=self.working_dir)

    def program_wait(self):
        """Wait for device programming to finish."""
        self.measurement.sensor.store(self.process.wait())
        self.relay.set_off()
        self.measurement()


class ARM():

    """ARM programmer using the isplpc package."""

    limitname = 'Program'   # Testlimit name to use

    def __init__(self, port, filename,
        baudrate=115200,
        erase_only=False, verify=False, crpmode=None,
        boot_relay=None, reset_relay=None):
        """Create a programmer.

        @param port Serial port to use
        @param filename Software image filename
        @param baudrate Serial baudrate
        @param erase_only True: Device should be erased only
        @param verify True: Verify the programmed device
        @param crpmode Code Protection:
                        True: ON, False: OFF, None: per 'bindata'
        @param boot_relay Relay device to assert BOOT to the ARM
        @param reset_relay Relay device to assert RESET to the ARM

        """
        self._port = port
        self._baudrate = baudrate
        self._erase_only = erase_only
        self._verify = verify
        self._crpmode = crpmode
        self._boot_relay = boot_relay
        self._reset_relay = reset_relay
        with open(filename, 'rb') as infile:
            self._bindata = bytearray(infile.read())
        self.measurement = tester.Measurement(
            tester.LimitInteger(
                self.limitname, 0, doc='Programming succeeded'),
            tester.sensor.Mirror()
            )

    def program(self):
        """Program a device.

        If BOOT or RESET relay devices are available, use them to put the chip
        into bootloader mode (Assert BOOT, pulse RESET).

        """
        ser = serial.Serial(port=self._port, baudrate=self._baudrate)
        try:
            if self._boot_relay:
                self._boot_relay.set_on()
            if self._reset_relay:
                self._reset_relay.pulse(0.1)
            pgm = isplpc.Programmer(
                ser,
                self._bindata,
                erase_only=self._erase_only,
                verify=self._verify,
                crpmode=self._crpmode)
            try:
                pgm.program()
                self.measurement.sensor.store(0)
            except isplpc.ProgrammingError:
                self.measurement.sensor.store(1)
        finally:
            ser.close()
            if self._boot_relay:
                self._boot_relay.set_off()
        self.measurement()


class Nordic():

    """Nordic Semiconductors programmer using a NRF52."""

    pic_binary = {          # Executable to use
        'posix': '/opt/nordic/nrfjprog/nrfjprog',
        'nt': r'C:\Program Files\Nordic Semiconductor\nrf5x\bin\nrfjprog.exe',
        }[os.name]
    limitname = 'Program'   # Testlimit name to use

    def __init__(self, hexfile, working_dir):
        """Create a programmer.

        @param hexfile HEX filename
        @param working_dir Working directory

        """
        self.hexfile = hexfile
        self.working_dir = working_dir
        self.measurement = tester.Measurement(
            tester.LimitInteger(
                self.limitname, 0, doc='Programming succeeded'),
            tester.sensor.Mirror()
            )
        self.process = None

    def program(self):
        """Program a device and return when finished."""
        self.program_begin()
        self.program_wait()

    def program_begin(self):
        """Begin device programming."""
        command = [
            self.pic_binary,
            '-f',
                'NRF52',
            '--chiperase',
            '--program',
                '{0}'.format(self.hexfile),
            '--verify',
#            '--log',
            ]
        self.process = subprocess.Popen(command, cwd=self.working_dir)

    def program_wait(self):
        """Wait for device programming to finish."""
        self.measurement.sensor.store(self.process.wait())
        self.measurement()
