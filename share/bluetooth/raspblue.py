#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONRPC Client for the Raspberry Pi Bluetooth helper."""

import abc
import jsonrpclib       # Install with: pip install jsonrpclib-pelix


class SerialIO(abc.ABC):

    """Serial compatible interface for RPC attached consoles.

    Simulates a serial console with character echo enabled.
    A RPC attached console cannot do byte by byte IO, only Command-Response
    calls. This class emulates the byte by byte IO functionality.
    Commands are run when a '\r' is received.

    """

    def __init__(self):
        """Create instance."""
        self.write_data = bytearray()           # write data buffer
        self.read_data = bytearray()            # read data buffer

    def flushInput(self):
        """Flush input data"""
        self.read_data.clear()

    def write(self, data):
        """Simulate Serial.write

        @param data Byte data to write

        """
        for abyte in data:
            abyte = bytes([abyte])
            self.read_data.extend(abyte)        # simulate echo
            if abyte == b'\r':
                reply = self.action(self.write_data.decode())
                self.write_data.clear()
                self.read_data.extend(reply.encode())
            else:
                self.write_data.extend(abyte)   # save for command locating

    def read(self, count=1):
        """Simulate Serial.read

        @param count Number of bytes to read
        @return Bytes read

        """
        data = bytes(self.read_data[:count])
        del self.read_data[:count]
        return data

    @abc.abstractmethod
    def action(self, command, timeout=60):
        """Command-Response to an open console.

        @param command Command string to be sent
        @param timeout Timeout in seconds
        @return Response to the command

        """


class RaspberryBluetooth(SerialIO):

    """Connection to a Raspberry Pi with Bluetooth helper running."""

    # Default server URL (Static addressed)
    default_server = 'http://192.168.168.62:8888/'
    # Calibration command end with this string
    cal_command = ' CAL'

    def __init__(self, server=None):
        """Create instance.

        @param server URL of the networked programmer

        """
        super().__init__()
        if server is None:
            server = self.default_server
        self.server = jsonrpclib.ServerProxy(
            server,
            config=jsonrpclib.config.Config(content_type='application/json')
            )

    def echo(self, value):
        """Echo function for diagnostic purposes.

        @param value Input value to be echoed back
        @return The input value

        """
        return self.server.echo(value)

    def scan_blemac(self, blemac, timeout=10):
        """Scan for a device MAC address.

        @param blemac MAC address to locate
        @param timeout Timeout in seconds
        @return True if device was found

        """
        return self.server.scan_blemac(blemac, timeout)

    def scan_sernum(self, sernum, timeout=10):
        """Scan for a device Serial Number.

        @param sernum Serial Number to locate
        @param timeout Timeout in seconds
        @return True if device was found

        """
        return self.server.scan_blemac(sernum, timeout)

    def open(self, device_id, timeout=10, passkey=None):
        """Open a connection to a device console.

        @param device_id Serial Number OR MAC address to connect to
        @param timeout Timeout in seconds
        @param passkey Device passkey string

        """
        self.server.open(device_id, timeout, passkey)

    def action(self, command, timeout=60):
        """Command-Response to an open console.

        @param command Command string to be sent
        @param timeout Timeout in seconds
        @return Response from the command call

        """
#        # BC2 Rev 4: The CAL commands return response-prompt-response-prompt
#        prompts = 2 if command.endswith(self.cal_command) else 1
#        reply = self.server.action(command, prompts, timeout)
#        lines = reply.splitlines()
#        # CAL command: skip command echo line & 1st response (3 lines)
#        # Other commands: skip command echo line
#        firstline = 3 if prompts == 2 else 1
#        reply = '\r\n'.join(lines[firstline:])

        # BC2 Rev 5: The CAL commands return response-response-prompt
        is_cal = command.endswith(self.cal_command)
        prompts = 1
        reply = self.server.action(command, prompts, timeout)
        lines = reply.splitlines()
        # CAL command: skip command echo line & 1st response (2 lines)
        # Other commands: skip command echo line
        firstline = 2 if is_cal else 1
        reply = '\r\n'.join(lines[firstline:])

        return reply

    def close(self):
        """Close an open console."""
        self.server.close()
