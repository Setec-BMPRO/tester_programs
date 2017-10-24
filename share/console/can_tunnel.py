#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""A Tunneled Console over CAN.

An interface to tunnel console data across a CAN bus to a remote device.
The interface is compatible with that of a SimSerial port, and is
used as the 'port' by another Console driver.

"""

import logging
import tester


class ConsoleCanTunnel():

    """A CAN Tunnel to another Console.

    A SimSerial object is used to do input data buffering of the decoded
    data received from the CAN Tunnel.

    """

    # True for verbose logging
    verbose = False

    def __init__(self, interface, target):
        """Initialise communications.

        @param interface SerialToCan interface.
        @param target CAN target device ID.

        """
        self._target = target
        self._can_port = interface
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        # The buffer for tunneled console data.
        self._buf_port = tester.SimSerial()
        # Serial compatible interface callables
        self.inWaiting = self._buf_port.inWaiting
        self.flushInput = self._buf_port.flushInput
        self.flushOutput = self._buf_port.flushOutput
        self.flush = self.flushOutput

    def open(self):
        """Open the CAN tunnel."""
        self._can_port.open_tunnel(self._target)
        self._logger.debug('CAN Tunnel opened')

    def close(self):
        """Close the CAN tunnel."""
        self._can_port.close_tunnel()
        self._logger.debug('CAN Tunnel closed')

    def read(self, size=1):
        """Serial: Read the input buffer.

        @return data from the tunnel

        """
        while self._can_port.ready_tunnel:  # Read all waiting data
            self._buf_port.put(self._can_port.read_tunnel())
        while self.inWaiting() < size:      # Wait for required data size
            self._buf_port.put(self._can_port.read_tunnel())
        data = self._buf_port.read(size)
        if self.verbose:
            self._logger.debug('read({0}) = {1!r}'.format(size, data))
        return data

    def write(self, data):
        """Serial: Write data bytes to the tunnel.

        @param data Byte data to send.

        """
        if self.verbose:
            self._logger.debug('write({0!r})'.format(data))
        self._can_port.write_tunnel(data)
