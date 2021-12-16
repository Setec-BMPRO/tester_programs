#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Programmer for devices."""

import abc
import pathlib
import os
import subprocess
import time

import isplpc
import serial
import tester
import updi


class _Base(abc.ABC):

    """Programmer base class."""

    pass_result = 'ok'

    def __init__(self):
        """Create a programmer."""
        self._measurement = tester.Measurement(
            tester.LimitRegExp(
                name='Program',
                testlimit=self.pass_result,
                doc='Programming succeeded'),
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
                value = self.pass_result
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


class VerificationError(Exception):

    """Verification error."""


class ARM(_Base):

    """ARM programmer using the isplpc package."""

    def __init__(
            self,
            port,
            file,
            crpmode=None,
            boot_relay=None,
            reset_relay=None,
            bda4_signals=False):
        """Create a programmer.

        @param port Serial port to use
        @param file pathlib.Path instance
        @param crpmode Code Protection:
                        True: ON, False: OFF, None: per 'bindata'
        @param boot_relay Relay device to assert BOOT to the ARM
        @param reset_relay Relay device to assert RESET to the ARM
        @param bda4_signals True: Use BDA4 serial lines for RESET & BOOT

        """
        super().__init__()
        self.port = port
        self.file = file
        self.boot_relay = boot_relay
        self.reset_relay = reset_relay
        self.bda4_signals = bda4_signals
        self.baudrate = 115200
        self.crpmode = crpmode
        self._bindata = None

    def program_begin(self):
        """Program a device.

        If BOOT or RESET relay devices are available, use them to put the chip
        into bootloader mode (Assert BOOT, pulse RESET).
        BDA4 serial signals: RTS = BOOT, DTR = RESET.

        """
        if not self._bindata:
            with self.file.open('rb') as infile:
                self._bindata = bytearray(infile.read())
        ser = serial.Serial(port=self.port, baudrate=self.baudrate)
        # We need to wait just a little before flushing the port
        time.sleep(0.5)
        ser.reset_input_buffer()
        try:
            if self.bda4_signals:
                ser.rts = ser.dtr = True
                ser.dtr = False
            if self.boot_relay:
                self.boot_relay.set_on()
            if self.reset_relay:
                self.reset_relay.pulse(0.1)
            pgm = isplpc.Programmer(
                ser,
                self._bindata,
                erase_only=False,
                verify=False,
                crpmode=self.crpmode)
            try:
                pgm.program()
                self.result = self.pass_result
            except isplpc.ProgrammingError as exc:
                self.result = str(exc)
        finally:
            ser.close()
            if self.bda4_signals:
                ser.rts = False
            if self.boot_relay:
                self.boot_relay.set_off()

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()


class AVR(_Base):

    """AVR programmer using the updi package."""

    def __init__(
            self,
            port,
            file,
            baudrate=115200,
            device='tiny406',
            fuses=None):
        """Create a programmer.

        @param port Serial port name to use
        @param file pathlib.Path instance
        @param baudrate Serial baudrate
        @param device Device type
        @param fuses Device fuse settings
            Dictionary{FuseName: (FuseNumber, FuseValue)}

        """
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._file = file
        self._device = updi.Device(device)
        self._fuses = fuses if fuses else {}

    def program_begin(self):
        """Program a device."""
        try:
            nvm = updi.UpdiNvmProgrammer(
                comport=self._port, baud=self._baudrate, device=self._device)
            try:
                nvm.enter_progmode()
            except updi.UpdiError:
                nvm.unlock_device()
            nvm.get_device_info()
            data, start_address = nvm.load_ihex(str(self._file))
            nvm.chip_erase()
            nvm.write_flash(start_address, data)
            readback = nvm.read_flash(nvm.device.flash_start, len(data))
            for offset in range(len(data)):
                if data[offset] != readback[offset]:
                    raise VerificationError(
                        'Verify error at 0x{0:04X}'.format(offset))
            for fuse_num, fuse_val in self._fuses.values():
                nvm.write_fuse(fuse_num, fuse_val)
            nvm.leave_progmode()
            self.result = self.pass_result
        except updi.UpdiError as exc:
            self.result = str(exc)

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()


class NRF52(_Base):

    """Nordic Semiconductors programmer using a NRF52."""

    bin_nt = pathlib.PureWindowsPath(
        'C:/Program Files/Nordic Semiconductor/nrf5x/bin/nrfjprog.exe')
    bin_posix = pathlib.PurePosixPath('nrfjprog')
    # HACK: Force coded RVSWT101 switch code if != 0
    rvswt101_forced_switch_code = 0

    def __init__(self, file, sernum=None):
        """Create a programmer.

        @param file pathlib.Path instance
        @param sernum nRF52 serial number

        """
        super().__init__()
        self._file = file
        self._sernum = sernum

    def program_begin(self):
        """Begin device programming."""
        binary = {
            'nt': self.bin_nt,
            'posix': self.bin_posix,
            }[os.name]
        command = [
            str(binary),
            '-f', 'NRF52',
            '--chiperase',
            '--program', str(self._file),
            '--verify',
            ]
        if self._sernum:
            command.extend(['--snr', self._sernum])
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        result = process.wait(timeout=60)
        # HACK: Force code an RVSWT101 switch code
        if not result and self.rvswt101_forced_switch_code:
            command = [
                self.binary,
                '--memwr', '0x70000',
                '--val', str(self.rvswt101_forced_switch_code),
                ]
            process = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            result = process.wait(timeout=60)
        self.result = result

    def program_wait(self):
        """Wait for device programming to finish."""
        self.result_check()
