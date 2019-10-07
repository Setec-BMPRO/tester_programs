#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 - 2019 SETEC Pty Ltd
"""Programmer for devices."""

import abc
import os
import subprocess
import time

import isplpc
import serial
import tester
import updi


class _Base(abc.ABC):

    """Programmer base class."""

    limitname = 'Program'   # Testlimit name to use
    pass_value = 'ok'
    doc = 'Programming succeeded'

    def __init__(self):
        """Create a programmer."""
        self._measurement = tester.Measurement(
            tester.LimitRegExp(self.limitname, self.pass_value, self.doc),
            tester.sensor.MirrorReadingString()
            )
        self._result = None

    @property
    def result(self):
        """Programming result value.

        @return Result value

        """
        return self._result

    @result.setter
    def result(self, value):
        """Set programming result.

        @param value Result

        """
        if not isinstance(value, str):  # A subprocess exit code
            if value:
                value = 'Error {0}'.format(value)
            else:
                value = self.pass_value
        self._result = value
        self._measurement.sensor.store(self._result)

    def result_check(self):
        """Check the programming result."""
        self._measurement()

    @property
    def position(self):
        """Position property of the internal mirror sensor.

        @return Position information

        """
        return self._measurement.sensor.position

    @position.setter
    def position(self, value):
        """Set internal mirror sensor position property.

        @param value Position value or Tuple(values)

        """
        self._measurement.sensor.position = value

    def program(self):
        """Program a device and return when finished."""
        self.program_begin()
        self.program_wait()

    @abc.abstractmethod
    def program_begin(self):
        """Begin device programming."""

    @abc.abstractmethod
    def program_wait(self):
        """Wait for device programming to finish."""


class ARM(_Base):

    """ARM programmer using the isplpc package."""

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
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._erase_only = erase_only
        self._verify = verify
        self._crpmode = crpmode
        self._boot_relay = boot_relay
        self._reset_relay = reset_relay
        with open(filename, 'rb') as infile:
            self._bindata = bytearray(infile.read())

    def program_begin(self):
        """Program a device.

        If BOOT or RESET relay devices are available, use them to put the chip
        into bootloader mode (Assert BOOT, pulse RESET).

        """
        ser = serial.Serial(port=self._port, baudrate=self._baudrate)
        # We need to wait just a little before flushing the port
        time.sleep(0.01)
        ser.flushInput()
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
                self.result = self.pass_value
            except isplpc.ProgrammingError as exc:
                self.result = str(exc)
        finally:
            ser.close()
            if self._boot_relay:
                self._boot_relay.set_off()

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()


class AVR(_Base):

    """AVR programmer using the updi package."""

    def __init__(self, port, filename,
            baudrate=115200, device='tiny406',
            fuses=None):
        """Create a programmer.

        @param port Serial port name to use
        @param filename Software HEX filename
        @param baudrate Serial baudrate
        @param device Device type
        @param fuses Device fuse settings
            Dictionary{FuseName: (FuseNumber, FuseValue)}

        """
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._filename = filename
        self._device = updi.Device(device)
        self._fuses = fuses if fuses else {}

    def program_begin(self):
        """Program a device."""
        try:
            nvm = updi.UpdiNvmProgrammer(
                comport=self._port, baud=self._baudrate, device=self._device)
            try:
                nvm.enter_progmode()
            except:
                nvm.unlock_device()
            nvm.get_device_info()
            data, start_address = nvm.load_ihex(self._filename)
            nvm.chip_erase()
            nvm.write_flash(start_address, data)
            readback = nvm.read_flash(nvm.device.flash_start, len(data))
            for offset in range(len(data)):
                if data[offset] != readback[offset]:
                    raise Exception(
                        'Verify error at 0x{0:04X}'.format(offset))
            for fuse_name in self._fuses:
                fuse_num, fuse_val = self._fuses[fuse_name]
                nvm.write_fuse(fuse_num, fuse_val)
            nvm.leave_progmode()
            self.result = self.pass_value
        except Exception as exc:
            self.result = str(exc)

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()


class Nordic(_Base):

    """Nordic Semiconductors programmer using a NRF52."""

    binary = {      # Executable to use
        'posix': '/opt/nordic/nrfjprog/nrfjprog',
        'nt': r'C:\Program Files\Nordic Semiconductor\nrf5x\bin\nrfjprog.exe',
        }[os.name]
    # HACK: Force coded RVSWT101 switch code if != 0
    rvswt101_forced_switch_code = 0

    def __init__(self, hexfile, working_dir):
        """Create a programmer.

        @param hexfile HEX filename
        @param working_dir Working directory

        """
        super().__init__()
        self.hexfile = hexfile
        self.working_dir = working_dir
        self.process = None

    def program_begin(self):
        """Begin device programming."""
        command = [
            self.binary,
            '-f', 'NRF52',
            '--chiperase',
            '--program', '{0}'.format(self.hexfile),
            '--verify',
            ]
        self.process = subprocess.Popen(command, cwd=self.working_dir)
        result = self.process.wait()
        # HACK: Force code an RVSWT101 switch code
        if not result and self.rvswt101_forced_switch_code:
            command = [
                self.binary,
                '--memwr', '0x70000',
                '--val', '{0}'.format(self.rvswt101_forced_switch_code),
                ]
            self.process = subprocess.Popen(command, cwd=self.working_dir)
            result = self.process.wait()
        self.result = result

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()


class PIC(_Base):

    """Microchip PIC programmer using a PicKit3."""

    binary = {      # Executable to use
        'posix': 'pickit3',
        'nt': r'C:\Program Files\Microchip-PK3\PK3CMD.exe',
        }[os.name]

    def __init__(self, hexfile, working_dir, device_type, relay):
        """Create a programmer.

        @param hexfile HEX filename
        @param working_dir Working directory
        @param device_type PIC device type
        @param relay Relay device to connect programmer to target

        """
        super().__init__()
        self.hexfile = hexfile
        self.working_dir = working_dir
        self.device_type = device_type
        self.relay = relay
        self.process = None

    def program_begin(self):
        """Begin device programming."""
        command = [
            self.binary,
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
        self.result = self.process.wait()
        self.relay.set_off()
        self.result_check()
