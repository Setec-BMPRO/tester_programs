#!/usr/bin/env python3
"""Trek2 ARM processor console driver."""

import share.arm_gen1
import share.sim_serial


# Expose arm_gen1.Sensor as trek2.Sensor
Sensor = share.arm_gen1.Sensor

# Some easier to use short names
ArmConsoleGen1 = share.arm_gen1.ArmConsoleGen1
ParameterBoolean = share.arm_gen1.ParameterBoolean
ParameterFloat = share.arm_gen1.ParameterFloat
ParameterHex = share.arm_gen1.ParameterHex
ParameterCAN = share.arm_gen1.ParameterCAN
ParameterRaw = share.arm_gen1.ParameterRaw

# Test mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF
# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF


class Console(ArmConsoleGen1):

    """Communications to Trek2 console."""

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port, dialect=1)
        self.cmd_data = {
            # Read-Write values
            'BACKLIGHT': ParameterFloat('BACKLIGHT', writeable=True,
                minimum=0, maximum=100, scale=1),
            # Other items
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=(1 << 28)),
            'CAN_ID': ParameterCAN('TQQ,16,0'),
            'SwVer': ParameterRaw('', func=self.version),
            }

    def testmode(self, state):
        """Enable or disable Test Mode."""
        self._logger.debug('Test Mode = %s', state)
        reply = self['STATUS']
        if state:
            value = _TEST_ON | reply
        else:
            value = _TEST_OFF & reply
        self['STATUS'] = value

    def can_mode(self, state):
        """Enable or disable CAN Communications Mode."""
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = _CAN_ON | reply
        else:
            value = _CAN_OFF & reply
        self['STATUS'] = value


class ConsoleCanTunnel(Console):

    """A CAN Tunnel to a Trek2 Console.

    Console tunneling is only available on Trek2 and CN101 (as of 2015-08).

    A serial port is used to communicate with a Serial to CAN interface
    device (A modified Trek2 inside a test fixture).

    A SimSerial object is used to do input data buffering of the decoded
    data received over the CAN Tunnel.

    This object presents the same interface as a SimSerial object, and is
    used as the 'port' by another trek2.Console instance.

    """

    def __init__(self, port, local_id=16, target_id = 32):
        """Initialise communications.

        @param port Serial port to connect to Serial to CAN interface.
        @param local_id My CAN bus ID (16-bit).
        @param target_id Remote CAN bus ID (16-bit).
        @param dialect Command dialect to use (0=SX-750,GEN8, 1=TREK2,BP35)

        """
        self._can_tunnel = False        # CAN tunneling OFF
        self._local_id = '{},{}'.format(
            (local_id & 0xFF00) >> 8, (local_id & 0xFF) )
        self._target_id = target_id
        # Create & open a SimSerial in simulation mode.
        # We can open it any time as there is no actual serial port.
        self._buf_port = share.sim_serial.SimSerial(simulation=True)
        self._buf_port.open()
        self.baudrate = 115200
        self.timeout = 0.1
        self.simulation = False
        super().__init__(port)

    def open(self):
        """Open a CAN tunnel."""
        # Open underlying console & serial port
        super().open()
        # Set filters to see all CAN traffic, Switch CAN test mode ON
        self.can_mode(True)
        # Open a console tunnel
        command = '"TCC,{},3,{},1 CAN'.format(self._target_id, self._local_id)
        self.action(command, expected=1)
        self._can_tunnel = True

    def close(self):
        """Close the CAN tunnel."""
        command = '"TCC,{},3,{},0 CAN'.format(self._target_id, self._local_id)
        self.action(command, expected=1)
        super().close()
        self._can_tunnel = False

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Serial: Put a string into the _buf_port read-back buffer."""
        self._buf_port.puts(string_data, preflush, postflush, priority)

    def read(self, size=1):
        """Serial: Read the input buffer."""
# TODO: Read any data from CAN Tunnel into _buf_port
#       "RRC,<local CAN ID>,4,<NumBytes>,<B0>,<B1>,...<B7>
#           Incoming DATA

#        data = self._buf_port.read(size)

#        data = self._port.read(1024)

        data = self.action()

        self._logger.debug('read(%s) = %s', size, repr(data))
        return data

    def write(self, data):
        """Serial: Write data bytes to the tunnel.

        The maximum tunnel payload is 8 data bytes, so we must cut the
        data into payload size chunks.

        """
        self._logger.debug('write(%s)', repr(data))
        while len(data) > 0:
            if len(data) > 8:           # Use 8 bytes max at a time
                byte_data = data[:8]
                byte_count = 8
                data = data[8:]
            else:
                byte_data = data
                byte_count = len(data)
                data = b''
            byte_data = ','.join(str(c) for c in byte_data)
            command = '"TCC,{},4,{},{} CAN'.format(
                self._target_id, byte_count, byte_data)
            reply = self.action(command, delay=0.2)
            self._logger.debug('write() reply %s', repr(reply))
        # sending a command of        "TCC,32,4,1,83 CAN
        # will result in a reply of   RRC,32,4,1,83
# TODO: Decode the reply, and push bytes back into _buf_port

    def inWaiting(self):
        """Serial: Return the number of bytes in the input buffer."""
        return self._buf_port.inWaiting()

    def flush(self):
        """Serial: Wait until all output data has been sent."""
        self._buf_port.flush()

    def flushInput(self):
        """Serial: Discard waiting input."""
        self._buf_port.flushInput()

    def flushOutput(self):
        """Serial: Discard waiting output."""
        self._buf_port.flushOutput()
