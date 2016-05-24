#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serial Port with simulation ability.

Data buffers are available to hold simulated input and output data.
The buffers are arrays of signed short values, where 0-255 is a data byte,
and -1 is a 'stop flush' marker.

The input data buffer is always available, and is read before the real port,
if it holds any data.
In 'simulation' mode, the port device is not accessed at all.

"""

import serial
import threading
import logging
from array import array

# Array data type (signed short)
_ARRAY_TYPE = 'h'
# Data buffer entry to mark a 'stop flush' point
_FLUSH = -1


class _Simulator():

    """Serial port simulation abilities."""

    def __init__(self):
        """Create internal data storage queue."""
        # Data buffer for data to be read by read()
        self._in_buf = array(_ARRAY_TYPE)
        # Data buffer for data written by write()
        self._out_buf = array(_ARRAY_TYPE)
        # Thread-safe locking control of the data buffer
        self._lock = threading.Lock()

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Put a string into the read-back buffer.

        @param string_data Data string, or tuple of data strings.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to put in front of the buffer.
        Note: _FLUSH is a marker to stop the flush of the data buffer.

        """
        self._logger.debug('puts() %s', repr(string_data))
        self._lock.acquire()
        try:
            newdata = array(_ARRAY_TYPE)
            for _ in range(preflush):
                newdata.append(_FLUSH)
            for dat in string_data.encode():
                newdata.append(dat)
            for _ in range(postflush):
                newdata.append(_FLUSH)
            if priority:    # LIFO - put into start of buffer
                newdata.extend(self._in_buf)
                self._in_buf = newdata
            else:           # FIFO - add onto end of buffer
                self._in_buf.extend(newdata)
        finally:
            self._lock.release()

    def _in_buf_len(self):
        """Calculate number of data bytes waiting in the input buffer."""
        self._lock.acquire()
        try:
            buf_len = len(self._in_buf) - self._in_buf.count(_FLUSH)
        finally:
            self._lock.release()
        return buf_len

    def get(self):
        """Get data from the written-out buffer.

        @return Bytes from the output capture buffer.

        """
        self._lock.acquire()
        try:
            data = bytearray()
            while len(self._out_buf) > 0:
                data.extend([self._out_buf.pop(0)])
        finally:
            self._lock.release()
        return data


class SimSerial(_Simulator, serial.Serial):

    """Serial port with simulation abilities."""

    def __init__(self,
        simulation=False,  # Extra argument for a simulated port
        port=None,         # These defaults match serial.Serial()
        baudrate=9600, bytesize=8, parity='N', stopbits=1,
        timeout=None, xonxoff=False, rtscts=False, writeTimeout=None,
        dsrdtr=False, interCharTimeout=None
        ):
        """Create base class instances."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created. Simulation = %s', simulation)
        self.simulation = simulation
        if simulation:
            port = None     # Prevent a real port from being opened
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        _Simulator.__init__(self)
        serial.Serial.__init__(self,
            port=port, baudrate=baudrate, bytesize=bytesize, parity=parity,
            stopbits=stopbits, timeout=timeout, xonxoff=xonxoff,
            rtscts=rtscts, writeTimeout=writeTimeout, dsrdtr=dsrdtr,
            interCharTimeout=interCharTimeout)

    def open(self):
        """Open port."""
        self._logger.debug('Open port')
        if not self.simulation:
            super().open()

    def close(self):
        """Close port."""
        self._logger.debug('Close port')
        if not self.simulation:
            try:
                super().close()
            except:
                pass

#    def setPort(self, port):
#        """Assign serial port."""
#        if hasattr(super(), 'setPort'): # Is this PySerial 2
#            print('YES it has setPort()')
#            super().setPort(self, port)
#        if hasattr(super(), 'port'):    # Is this PySerial 3+
#            print('YES it has port')
#            print('...port is', super().port)
#            print('super().port is', type(super().port))
#            print('super().__dict__ is', super().__dict__)
#            print('super().__attr__ is', super().__attr__)
#            super().port = port

    def makeDeviceName(self, port):
        return 'simulation'

    def read(self, size=1):
        """A non-blocking read.

        Read the buffer, then the device.
        @param size Number of bytes to read.
        @return Bytes read.

        """
        data = bytearray()
        bufsize = self._in_buf_len()
        while size > 0 and bufsize > 0:
            dat = self._in_buf.pop(0)
            if dat == _FLUSH:
                return data
            else:
                data.extend([dat])
                size -= 1
                bufsize -= 1
        if size > 0 and not self.simulation:
            data.extend(super().read(size))
        return bytes(data)

    def write(self, data):
        """Write data bytes to the written-out queue.

        @param data Bytes to write.

        """
        if not self.simulation:
            super().write(data)
        else:
            self._out_buf.extend(data)

    def inWaiting(self):
        """Return the number of characters currently in the input buffer."""
        in_count = self._in_buf_len()
        if not self.simulation:
            in_count += super().inWaiting()
        return in_count

    def flush(self):
        """Wait until all output data has been sent."""
        if not self.simulation:
            super().flush()

    def flushInput(self):
        """Discard waiting input.

        A buffer value of _FLUSH will stop the flush.

        """
        if len(self._in_buf) > 0:
            try:
                marker = self._in_buf.index(_FLUSH)
                for _ in range(marker + 1):
                    self._in_buf.pop(0)
                return
            except ValueError:      # No flush markers in the buffer
                self._in_buf = array(_ARRAY_TYPE)   # Empty the buffer
        if not self.simulation:
            super().flushInput()

    def flushOutput(self):
        """Discard waiting output."""
        if not self.simulation:
            super().flushOutput()
