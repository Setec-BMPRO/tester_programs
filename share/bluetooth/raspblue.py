#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""JSONRPC Client for the Raspberry Pi Bluetooth helper."""

import abc
import jsonrpclib  # Install with: pip install jsonrpclib-pelix


class SerialIO(abc.ABC):
    """Serial compatible interface for RPC attached consoles.

    Simulates a serial console with character echo enabled.
    A RPC attached console cannot do byte by byte IO, only Command-Response
    calls. This class emulates the byte by byte IO functionality.
    Commands are run when a '\r' is received.

    """

    def __init__(self):
        """Create instance."""
        self.write_data = bytearray()  # write data buffer
        self.read_data = bytearray()  # read data buffer

    def reset_input_buffer(self):
        """Flush input data"""
        self.read_data.clear()

    def write(self, data):
        """Simulate Serial.write

        @param data Byte data to write

        """
        for abyte in data:
            abyte = bytes([abyte])
            self.read_data.extend(abyte)  # simulate echo
            if abyte == b"\r":
                reply = self.action(self.write_data.decode())
                self.write_data.clear()
                self.read_data.extend(reply.encode())
            else:
                self.write_data.extend(abyte)  # save for command locating

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

    # Calibration command end with this string
    cal_command = " CAL"

    def __init__(self, server):
        """Create instance.

        @param server URL of the server

        """
        super().__init__()
        self.server = jsonrpclib.ServerProxy(server)

    def echo(self, value):
        """Echo function for diagnostic purposes.

        @param value Input value to be echoed back
        @return The input value

        """
        return self.server.echo(value)

    def scan_advert_blemac(self, blemac, timeout=10):
        """Scan advertisement packets for a device MAC address.

        @param blemac Bluetooth MAC address to locate
        @param timeout Timeout in seconds
        @return Scan result dictionary {'ad_data': ad_data, 'rssi': rssi}
            or None is not found

        """
        return self.server.scan_advert_blemac(blemac, timeout)

    def scan_advert_sernum(self, sernum, timeout=10):
        """Scan advertisment packets for a device Serial Number.

        @param sernum Serial Number to locate
        @param timeout Timeout in seconds
        @return Scan result dictionary {'ad_data': ad_data, 'rssi': rssi}
            or None is not found

        """
        return self.server.scan_advert_sernum(sernum, timeout)

    def scan_beacon_sernum(self, sernum, timeout=20):
        """Scan beacon-mode packets for a device Serial Number.

        @param sernum Serial Number to locate
        @param timeout Timeout in seconds
        @return True if device was found

        """
        return self.server.scan_beacon_sernum(sernum, timeout)

    def open(self, device_id, timeout=20, passkey=None):
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
        # BC2 Rev 5: The CAL commands return response-response-prompt
        is_cal = command.endswith(self.cal_command)
        prompts = 1
        reply = self.server.action(command, prompts, timeout)
        lines = reply.splitlines()
        # CAL command: skip command echo line & 1st response (2 lines)
        # Other commands: skip command echo line
        firstline = 2 if is_cal else 1
        reply = "\r\n".join(lines[firstline:])
        return reply

    def close(self):
        """Close an open console."""
        self.server.close()
