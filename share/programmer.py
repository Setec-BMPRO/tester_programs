#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmer for devices."""

import os
import subprocess
import logging
import tester
import isplpc


# Result values to store into the mirror sensor
_SUCCESS = 0
_FAILURE = 1


class ProgramSAM():

    pic_binary = {
        'posix': 'pickit3',
        'nt': r'C:\Program Files\Microchip-PK3\PK3CMD.exe',
        }[os.name]

    """Atmel SAM device programmer using a Atmel-ICE Debugger."""

    def __init__(self,
                 hexfile, working_dir, device_type,
                 relay, limitname='Program'):
        """Create a programmer.

        @param hexfile Full pathname of HEX file
        @param working_dir Working directory
        @param device_type SAM device type (eg: 'SAM B11-MR210CA')
        @param relay Relay device to connect programmer to target
        @param limitname Testlimit name

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.hexfile = hexfile
        self.working_dir = working_dir
        self.device_type = device_type
        self.relay = relay
        limit = tester.LimitInteger(
            limitname, _SUCCESS, doc='Programming succeeded')
        self._sam = tester.Measurement(limit, tester.sensor.Mirror())

    def program(self):
        """Program a device."""
        try:
            command = [
                self.pic_binary,
                '/P{}'.format(self.device_type),
                '/F{}'.format(self.hexfile),
                '/E',
                '/M',
                '/Y'
                ]
            self.relay.set_on()
            subprocess.check_output(command, cwd=self.working_dir)
            self._sam.sensor.store(_SUCCESS)
        except subprocess.CalledProcessError as err:
            self._logger.debug('Error: %s', err.output)
            self._sam.sensor.store(_FAILURE)
        self.relay.set_off()
        self._sam.measure()


class ProgramPIC():

    pic_binary = {
        'posix': 'pickit3',
        'nt': r'C:\Program Files\Microchip-PK3\PK3CMD.exe',
        }[os.name]

    """Microchip PIC programmer using a PicKit3."""

    def __init__(self,
                 hexfile, working_dir, device_type,
                 relay, limitname='Program'):
        """Create a programmer.

        @param hexfile Full pathname of HEX file
        @param working_dir Working directory
        @param device_type PIC device type (eg: '10F320')
        @param relay Relay device to connect programmer to target
        @param limitname Testlimit name

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.hexfile = hexfile
        self.working_dir = working_dir
        self.device_type = device_type
        self.relay = relay
        limit = tester.LimitInteger(
            limitname, _SUCCESS, doc='Programming succeeded')
        self._pic = tester.Measurement(limit, tester.sensor.Mirror())

    def program(self):
        """Program a device."""
        try:
            command = [
                self.pic_binary,
                '/P{}'.format(self.device_type),
                '/F{}'.format(self.hexfile),
                '/E',
                '/M',
                '/Y'
                ]
            self.relay.set_on()
            subprocess.check_output(command, cwd=self.working_dir)
            self._pic.sensor.store(_SUCCESS)
        except subprocess.CalledProcessError as err:
            self._logger.debug('Error: %s', err.output)
            self._pic.sensor.store(_FAILURE)
        self.relay.set_off()
        self._pic.measure()


class ProgramARM():

    """ARM programmer using the isplpc package."""

    def __init__(self, port, filename,
        baudrate=115200, limitname='Program',
        erase_only=False, verify=False, crpmode=None,
        boot_relay=None, reset_relay=None):
        """Create a programmer.

        @param port Serial port to use
        @param filename Software image filename
        @param baudrate Serial baudrate
        @param limitname Testlimit name
        @param erase_only True: Device should be erased only
        @param verify True: Verify the programmed device
        @param crpmode Code Protection:
                        True: ON, False: OFF, None: per 'bindata'
        @param boot_relay Relay device to assert BOOT to the ARM
        @param reset_relay Relay device to assert RESET to the ARM

        """
        self._port = port
        self._baudrate = baudrate
        self._limitname = limitname
        self._erase_only = erase_only
        self._verify = verify
        self._crpmode = crpmode
        self._boot_relay = boot_relay
        self._reset_relay = reset_relay
        with open(filename, 'rb') as infile:
            self._bindata = bytearray(infile.read())
        limit = tester.LimitInteger(
            limitname, _SUCCESS, doc='Programming succeeded')
        self._arm = tester.Measurement(limit, tester.sensor.Mirror())

    def program(self):
        """Program a device.

        If BOOT or RESET relay devices are available, use them to put the chip
        into bootloader mode (Assert BOOT, pulse RESET).

        """
        ser = tester.SimSerial(port=self._port, baudrate=self._baudrate)
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
                self._arm.sensor.store(_SUCCESS)
            except isplpc.ProgrammingError:
                self._arm.sensor.store(_FAILURE)
        finally:
            ser.close()
            if self._boot_relay:
                self._boot_relay.set_off()
        self._arm.measure()
