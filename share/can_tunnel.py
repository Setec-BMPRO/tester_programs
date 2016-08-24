#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        '0 ECHO'                    ' -> \r\n> '
    CAN Filter
        '"RF,ALL CAN'               None
    CAN Print Packets
        '"STATUS XN?'               '0x12345678'
        '0x12345678 "STATUS XN!'    None
    Open CAN Tunnel
        '"TCC,{},3,{},1 CAN'        None
    Send Data
        '"TCC,{},4,{} CAN'          None
    Receive Data
        None                        'RRC,{},4,{count},{data},...'
    Close CAN Tunnel
        '"TCC,{},3,{},0 CAN'        None

"""

import logging
import time

import tester

# "CAN Print Packets" mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF
# Investigation shows that time.sleep() <= 1ms doesn't do anything.
# Only delays >1ms are implemented.
_INTER_CHAR_DELAY = 0.002


class TunnelError(Exception):

    """Tunnel Error."""


class ConsoleCanTunnel():

    """A CAN Tunnel to another Console.

    A SimSerial object is used to do input data buffering of the decoded data
    received over the CAN Tunnel.

    Another SimSerial port is used to communicate with a Serial to CAN
    interface device (A modified Trek2 inside a test fixture).

    This object presents the same interface as a SimSerial object, and is
    used as the 'port' by another Console driver.

    """

    def __init__(self,
                 port, local_id=16, target_id=32,
                 simulation=False, verbose=False):
        """Initialise communications.

        @param port SimSerial port to connect to Serial to CAN interface.
        @param local_id My CAN bus ID.
        @param target_id Remote CAN bus ID.

        """
        self.port = port
        self._local_id = '{},{}'.format(
            (local_id & 0xFF00) >> 8, (local_id & 0xFF) )
        self._target_id = target_id
        self.simulation = simulation
        self.verbose = verbose
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        # Create & open a SimSerial in simulation mode.
        # We can open it any time as there is no actual serial port.
        self._buf_port = tester.SimSerial(simulation=True)

    def open(self):
        """Open the CAN tunnel."""
        self._logger.info('Open CAN tunnel buffer port')
        self._buf_port.open()
        self._logger.info('Open CAN tunnel serial port')
        self.port.open()
        # Switch console echo OFF
        self.port.flushInput()
        no_echo_cmd = '0 ECHO'
        reply = self.action(no_echo_cmd)
        if reply is None or reply[:6] != no_echo_cmd:
            raise TunnelError
        # Set filters to see all CAN traffic
        self.action('"RF,ALL CAN')
        # Switch CAN Print Packet mode ON
        try:
            reply = self.action('"STATUS XN?')
            new_status = _CAN_ON | int(reply, 16)
            self.action('${:08X} "STATUS XN!'.format(new_status))
        except Exception as exc:
            raise TunnelError('Set CAN print mode failed') from exc
        # Open a console tunnel
        try:
            self.action(
                '"TCC,{},3,{},1 CAN'.format(self._target_id, self._local_id))
            reply = self.action(delay=0.2)  # RRC... is expected
        except Exception as exc:
            raise TunnelError('CAN Tunnel Mode failed') from exc
        expected = 'RRC,{},3,3,{},1'.format(self._target_id, self._local_id)
        if reply != expected:
            raise TunnelError(
                'Bad CAN tunnel mode reply: {}'.format(reply))
        self._logger.debug('CAN Tunnel opened')

    def close(self):
        """Close the CAN tunnel."""
        self.action(
            '"TCC,{},3,{},0 CAN'.format(self._target_id, self._local_id))
        self._logger.info('Close CAN tunnel serial port')
        self.port.close()
        self._logger.info('Close CAN tunnel buffer port')
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
                self._logger.debug('--> %s', repr(command))
            cmd_data = command.encode()
            for a_byte in cmd_data:             # write 1 byte at a time...
                a_byte = bytes([a_byte])
                self.port.write(a_byte)
                time.sleep(_INTER_CHAR_DELAY)   # ...with a gap between each
            self.port.write(b'\r')
        if delay:
            time.sleep(delay)
        if get_response:
            buf = self.port.readline()
            response = None
            if self.verbose:
                self._logger.debug('Rx <--- %s', repr(buf))
            if len(buf) > 0:
                response = buf.decode(errors='ignore')
                response = response.replace(' -> ', '')
                response = response.replace(' \r\n', '')
                response = response.replace('\r\n', '')
                response = response.replace('"', '')
            if self.verbose:
                self._logger.debug('<-- %s', repr(response))
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
        pattern = ['RRC', str(self._target_id), '4']
        pat_len = len(pattern)
        chunks = message.split(',')     # Chop into CSV pieces
        if chunks[:pat_len] == pattern: # if it's a console data packet
            count = len(chunks) - pat_len   # chunks after the pattern
            if count < 2:   # No data in the packet
                return ''
            byte_count = int(chunks[len(pattern)])
            if byte_count + 1 != count: # Data count mismatch in the packet
                return ''
            for i in range(pat_len + 1, pat_len + 1 + byte_count):
                data += chr(int(chunks[i]))
        if self.verbose:
            self._logger.debug('Decode %s => %s', repr(message), repr(data))
        return data

####    START of SimSerial compatible interface      ####

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Serial: Put a string into the _buf_port read-back buffer."""
        self._buf_port.puts(string_data, preflush, postflush, priority)

    def read(self, size=1):
        """Serial: Read the input buffer."""
        while self.port.inWaiting():
            reply = self.action()       # read any CAN data
            if reply:
                reply_bytes = self._decode(reply)
                if self.verbose:
                    self._logger.debug(
                        'read() reply_bytes %s', repr(reply_bytes))
                self.puts(reply_bytes)  # push any CAN data into buffer port
                time.sleep(0.1)
        data = self._buf_port.read(size)    # now read from the buffer port
        if self.verbose:
            self._logger.debug('read(%s) = %s', size, repr(data))
        return data

    def write(self, data):
        """Serial: Write data bytes to the tunnel.

        The maximum tunnel payload is 8 data bytes, so we must cut the
        data into payload size chunks.

        @param data Byte data to send.

        """
        if self.verbose:
            self._logger.debug('write(%s)', repr(data))
        while len(data) > 0:
            if len(data) > 8:           # Use 8 bytes max at a time
                byte_data = data[:8]
                data = data[8:]
            else:
                byte_data = data
                data = b''
            byte_data = ','.join(str(c) for c in byte_data)
            command = '"TCC,{},4,{} CAN'.format(self._target_id, byte_data)
            reply = self.action(command, delay=0.2)
            if reply:
                reply_bytes = self._decode(reply)
                self.puts(reply_bytes)  # push any CAN data into my buffer port

    def inWaiting(self):
        """Serial: Return the number of bytes in the input buffer."""
        return self._buf_port.inWaiting()

    def flush(self):
        """Serial: Wait until all output data has been sent."""
        self.port.flush()

    def flushInput(self):
        """Serial: Discard waiting input."""
        self._buf_port.flushInput()

    def flushOutput(self):
        """Serial: Discard waiting output."""
        self._buf_port.flushOutput()

####    END of SimSerial compatible interface      ####
