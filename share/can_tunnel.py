#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""A Tunneled Console over CAN.

Creates an interface to tunnel data across a CAN bus to a remote device
console.
Our end of the tunnel is a Trek2 PCB, which we talk to using it's console
serial port.
The interface is compatible with that of a SimSerial port.
This driver implements a simplified version of the generic console driver.
Just enough to open and run a tunnel.

The required process to run a tunnel...
    Echo OFF
        '0 ECHO'                            ' -> <CR><LF> '
    CAN Filter
        '"RF,ALL CAN'                       None
    CAN Print Packets
        '"STATUS XN?'                       '0x12345678'
        '0x12345678 "STATUS XN!'            None
    Open CAN Tunnel
        '"TCC,<target>,3,<local>,1 CAN'     None
    Send Data
        '"TCC,<target>,4,<data> CAN'        None
    Receive Data
        None                                'RRC,<target>,4,<count>,<data>,...'
    Close CAN Tunnel
        '"TCC,<target>,3,<local>,0 CAN'     None

"""

import logging
import time
import tester


class OldConsoleCanTunnel():

    """A CAN Tunnel to another Console.

    A SimSerial object is used to do input data buffering of the decoded data
    received over the CAN Tunnel.

    Another SimSerial port is used to communicate with a Serial to CAN
    interface device (A modified Trek2 inside a test fixture).

    This object presents the same interface as a SimSerial object, and is
    used as the 'port' by another Console driver.

    """

    # "CAN Print Packets" mode controlled by STATUS bit 29
    can_on = (1 << 29)
    # Investigation shows that time.sleep() <= 1ms doesn't do anything.
    # Only delays >1ms are implemented.
    inter_char_delay = 2e-3
    # Ignored response strings
    ignore = (' -> ', ' \r\n', '\r\n', '"', )
    # CAN ID numbers
    local_id = 16       # My CAN bus ID
    target_id = 32      # Remote CAN bus ID

    def __init__(self, port, simulation=False, verbose=False):
        """Initialise communications.

        @param port SimSerial port to connect to Serial to CAN interface.
        @param simulation True for simulation mode.
        @param verbose True for verbose logging.

        """
        self.port = port
        self.simulation = simulation
        self.verbose = verbose
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        # Create & open a SimSerial in simulation mode.
        # We can open it any time as there is no actual serial port.
        self._buf_port = tester.SimSerial(simulation=True)
        # Callable SimSerial compatible interface
        self.puts = self._buf_port.puts
        self.inWaiting = self._buf_port.inWaiting
        self.flush = self.port.flush
        self.flushInput = self._buf_port.flushInput
        self.flushOutput = self._buf_port.flushOutput

    def open(self):
        """Open the CAN tunnel."""
        self.local_id = '{0},{1}'.format(
            (self.local_id & 0xFF00) >> 8, (self.local_id & 0xFF))
        self._logger.debug('Open CAN tunnel buffer port')
        self._buf_port.open()
        self._logger.debug('Open CAN tunnel serial port')
        self.port.open()
        self.port.write(b'\r')  # Need this 'sometimes' to wake the unit up...
        time.sleep(0.1)
        # Switch console echo OFF
        self.port.flushInput()
        no_echo_cmd = '0 ECHO'
        reply = self.action(no_echo_cmd)
        if reply is None or reply[:6] != no_echo_cmd:
            self._logger.debug(
                'Echo error: expected %s, got %s',
                repr(no_echo_cmd), repr(reply))
            raise TunnelError
        # Send the Preconditions packet (for Trek2)
        self.action('"TAN,16,105,0,0 CAN')
        # Set filters to see all CAN traffic
        self.action('"RF,ALL CAN')
        # Switch CAN Print Packet mode ON
        try:
            reply = self.action('"STATUS XN?')
            new_status = self.can_on | int(reply, 16)
            self.action('${0:08X} "STATUS XN!'.format(new_status))
        except Exception as exc:
            raise TunnelError('Set CAN print mode failed') from exc
        # Open a console tunnel
        try:
            self.action(
                '"TCC,{0},3,{1},1 CAN'.format(self.target_id, self.local_id))
            reply = self.action(delay=0.2)  # RRC... is expected
        except Exception as exc:
            raise TunnelError('CAN Tunnel Mode failed') from exc
        expected = 'RRC,{0},3,3,{1},1'.format(self.target_id, self.local_id)
        if reply != expected:
            raise TunnelError(
                'Bad CAN tunnel mode reply: {0}'.format(reply))
        self._logger.debug('CAN Tunnel opened')

    def close(self):
        """Close the CAN tunnel."""
        self.action(
            '"TCC,{0},3,{1},0 CAN'.format(self.target_id, self.local_id))
        self._logger.debug('Close CAN tunnel serial port')
        self.port.close()
        self._logger.debug('Close CAN tunnel buffer port')
        self._buf_port.close()
        self._logger.debug('CAN Tunnel closed')

    def action(self, command=None, delay=0.1, get_response=True):
        """Send a command, and read the response.

        @param command Command string.
        @param delay Delay between sending command and reading response.
        @param get_response True if a response should be read back.
        @return Response line.

        """
        if command:
            if self.verbose:
                self._logger.debug('--> {0!r}'.format(command))
            cmd_data = command.encode()
            for a_byte in cmd_data:             # write 1 byte at a time...
                a_byte = bytes([a_byte])
                self.port.write(a_byte)
                time.sleep(self.inter_char_delay)   # ... a gap between each
            self.port.write(b'\r')
        time.sleep(delay)
        if get_response:
            buf = self.port.readline()
            response = None
            if self.verbose:
                self._logger.debug('Rx <--- {0!r}'.format(buf))
            if len(buf) > 0:
                response = buf.decode(errors='ignore')
                for pattern in self.ignore:
                    response = response.replace(pattern, '')
            if self.verbose:
                self._logger.debug('<-- {0!r}'.format(response))
            return response

    def _decode(self, message):
        """Decode a single CAN packet messages.

        @param message String.
        @return Decoded data string.

        """
        data = ''
        if message is None:
            return data
        # Pattern to match a console data packet
        pattern = ['RRC', str(self.target_id), '4']
        pat_len = len(pattern)
        chunks = message.split(',')         # Chop into CSV pieces
        if chunks[:pat_len] == pattern:     # if it's a console data packet
            count = len(chunks) - pat_len   # chunks after the pattern
            if count < 2:   # No data in the packet
                return ''
            byte_count = int(chunks[len(pattern)])
            if byte_count + 1 != count:     # Data count mismatch
                return ''
            for i in range(pat_len + 1, pat_len + 1 + byte_count):
                data += chr(int(chunks[i]))
        if self.verbose:
            self._logger.debug('Decode {0!r} => {1!r}'.format(message, data))
        return data

    def read(self, size=1):
        """Serial: Read the input buffer.

        @return data from the tunnel

        """
        while self.port.inWaiting():
            reply = self.action()       # read any CAN data
            if reply:
                reply_bytes = self._decode(reply)
                if self.verbose:
                    self._logger.debug(
                        'read() reply_bytes {0!r}'.format(reply_bytes))
                self.puts(reply_bytes)  # push any CAN data into buffer port
                time.sleep(0.1)
        data = self._buf_port.read(size)    # now read from the buffer port
        if self.verbose:
            self._logger.debug('read({0}) = {1!r}'.format(size, data))
        return data

    def write(self, data):
        """Serial: Write data bytes to the tunnel.

        The maximum tunnel payload is 8 data bytes, so we must cut the
        data into payload size chunks.

        @param data Byte data to send.

        """
        if self.verbose:
            self._logger.debug('write({0!r})'.format(data))
        while len(data) > 0:
            if len(data) > 8:           # Use 8 bytes max at a time
                byte_data = data[:8]
                data = data[8:]
            else:
                byte_data = data
                data = b''
            byte_data = ','.join(str(c) for c in byte_data)
            command = '"TCC,{0},4,{1} CAN'.format(self.target_id, byte_data)
            reply = self.action(command, delay=0.2)
            if reply:
                reply_bytes = self._decode(reply)
                self.puts(reply_bytes)  # push any CAN data into my buffer port


class TunnelError(Exception):

    """Tunnel Error."""
