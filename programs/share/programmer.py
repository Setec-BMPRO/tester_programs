#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmer for ARM & PIC devices.

Programming runs in the background on another thread.
When you are ready to read the result, call ProgramXXX.read()

"""

import sys
import os
import subprocess
import threading
import queue
import logging


# Result values to store into the mirror sensor
_SUCCESS = 0
_FAILURE = 1

# Programmer binaries.
_ARM_BINARY = {'posix': 'lpc21isp',
               'nt': r'C:\Program Files\ARM\lpc21isp.exe',
               }[os.name]
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


class ProgramARM(_Programmer):

    """ARM programmer using a serial port."""

    def __init__(self, hexfile, working_dir, sensor,
                 port, baud=115200, khz=12000,
                 wipe=False, fifo=False):
        """Create the programmer worker and start it running.

        hexfile: Full pathname of HEX file
        working_dir: Working directory.
        sensor: Mirror sensor to store result (0=success, 1=failed)
        port: Serial port
        baud: Baud rate
        khz: Processor clock
        wipe: Force erase of a protected device
        fifo: True if FIFO's are being used

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created')
        command = [_ARM_BINARY]
        if wipe:
            command += ['-wipe']
        command += [hexfile, port, str(baud), str(khz)]
        super().__init__(command, working_dir, sensor, fifo)


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