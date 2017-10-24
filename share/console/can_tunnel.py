#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""A Tunneled Console over CAN.

An interface to tunnel console data across a CAN bus to a remote device.
The interface is compatible with that of a SimSerial port, and is
used as the 'port' by another Console driver.

"""

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
        # Simple callables
        self.close = self._can_port.close_tunnel
        self.write = self._can_port.write_tunnel
        # The buffer for tunneled console data.
        self._buf_port = tester.SimSerial()
        # Serial compatible interface callables
        self.inWaiting = self._buf_port.inWaiting
        self.flushInput = self._buf_port.flushInput
        self.flushOutput = self._buf_port.flushOutput
        self.flush = self.flushOutput
        # A Measurement to generate MeasurementFailedError
        self.measurement = tester.Measurement(
            tester.LimitBoolean(
                'CANtunnel', True, doc='Tunnel operation succeeded'),
            tester.sensor.Mirror()
            )

    def open(self):
        """Open the CAN tunnel."""
        try:    # Change any SystemError into a MeasurementFailedError
            self._can_port.open_tunnel(self._target)
        except tester.SerialToCanError:
            self.measurement.sensor.store(False)
            self.measurement()

    def read(self, size=1):
        """Serial: Read the input buffer.

        @return data from the tunnel

        """
        # Read all waiting data from the CAN tunnel into my buffer
        while self._can_port.ready_tunnel:
            self._buf_port.put(self._can_port.read_tunnel())
        # Wait for required data in my buffer
        while self.inWaiting() < size:
            self._buf_port.put(self._can_port.read_tunnel())
        return self._buf_port.read(size)
