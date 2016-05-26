#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmer for PIC devices.

Programming runs in the background on another thread.
When you are ready to read the result, call ProgramXXX.read()

"""

import sys
import os
import subprocess
import threading
import queue
import logging
import testlimit
import sensor
import isplpc
from tester.measure import Measurement
from share import SimSerial


# Result values to store into the mirror sensor
_SUCCESS = 0
_FAILURE = 1

# Programmer binaries.
_PIC_BINARY = {'posix': 'pickit3',
               'nt': r'C:\Program Files\Microchip-PK3\PK3CMD.exe',
               }[os.name]


class _Programmer():

    """Programmer base class.

    Handles the programmer thread and result return.

    """

    def __init__(self, command, working_dir, sensor, fifo=False):
        """Create the programmer worker and start it running.

        command: List of command arguments.
        working_dir: Working directory.
        sensor: Mirror sensor to store result (0=success, 1=failed)
        fifo: True if FIFO's are being used

        """
        self._sensor = sensor
        self._fifo = fifo
        # Use a queue to return result from the worker thread
        self._result_q = queue.Queue()
        if fifo:
            self._result_q.put((False, None))   # Dummy PASS result
        else:
            self._work = threading.Thread(
                target=self._worker, args=(command, working_dir))
            self._work.start()

    def read(self):
        """Read programming result & store into the mirror sensor."""
        # Wait for programming completion
        if not self._fifo:
            self._work.join()
        error, msg = self._result_q.get()
        if error:
            val = _FAILURE
            self._logger.warning(msg)
        else:
            val = _SUCCESS
            self._logger.debug(msg)
        self._sensor.store(val)

    def _worker(self, command, working_dir):
        """Thread worker to program a device in another process.

        command: List of command arguments.
        working_dir: Working directory.

        """
        try:
            console = subprocess.check_output(command, cwd=working_dir)
            self._result_q.put((False, console))
        except subprocess.CalledProcessError:
            self._result_q.put((True, sys.exc_info()[1]))


class ProgramPIC(_Programmer):

    """Microchip PIC programmer using a PicKit3."""

    def __init__(self, hexfile, working_dir, device_type, sensor, fifo=False):
        """Create the programmer worker and start it running.

        hexfile: Full pathname of HEX file
        working_dir: Working directory.
        device_type: PIC device type (eg: '10F320')
        sensor: Mirror sensor to store result (0=success, 1=failed)
        fifo: True if FIFO's are being used

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created')
        command = [_PIC_BINARY,
                   '/P{}'.format(device_type),
                   '/F{}'.format(hexfile),
                   '/E',
                   '/M',
                   '/Y']
        super().__init__(command, working_dir, sensor, fifo)


class ProgramARM():

    """ARM programmer using the isplpc package."""

    def __init__(self, port, filename,
        baudrate=115200, limitname='Program',
        erase_only=False, verify=False, crpmode=None):
        """Create a programmer.

        @param port Serial port to use
        @param filename Software image filename
        @param baudrate Serial baudrate
        @param limitname Testlimit name
        @param erase_only True: Device should be erased only.
        @param verify True: Verify the programmed device.
        @param crpmode Code Protection:
                        True: ON, False: OFF, None: per 'bindata'.

        """
        self._port = port
        self._baudrate = baudrate
        self._limitname = limitname
        self._erase_only = erase_only
        self._verify = verify
        self._crpmode = crpmode
        with open(filename, 'rb') as infile:
            self._bindata = bytearray(infile.read())
        self._arm = Measurement(
            testlimit.lim_hilo_int(limitname, _SUCCESS), sensor.Mirror())

    def program(self):
        """Program a device."""
        ser = SimSerial(port=self._port, baudrate=self._baudrate)
        try:
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
        self._arm.measure()
