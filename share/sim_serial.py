#!/usr/bin/env python3
"""Serial Port with simulation ability.

Setting the 'simulate' argument at creation will give a port with queues
to hold simulated Tx & Rx data, for testing purposes.

"""

import serial
import logging
import queue
import threading

# Queue entry to be read when a flush occurs
_FLUSH = b''


class _Simulator():

    """Serial port simulation abilities."""

    def __init__(self, simulation=False, **kwargs):
        """Create internal data storage queue."""
        self.simulation = simulation
        if self.simulation:
            kwargs['port'] = None   # Prevent a real port from being opened
        # Queues to hold data to be read by read()
        self._in_queue_hi = queue.Queue()   # High priority
        self._in_queue_lo = queue.Queue()   # Normal priority
        # Queue to hold data written by write()
        self._out_queue = queue.Queue()
        # Control of read() enable
        self._enable = threading.Event()
        self._enable.set()
        # Initialise the serial.Serial
        super().__init__(**kwargs)

    def puts(self, string_data, preflush=0, postflush=0, priority=False):
        """Put a string into the read-back queue.

        @param string_data Data string, or tuple of data strings.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to use high priority queue.
        Note: _FLUSH is a marker to stop the flush of the data queue.

        """
        if not self.simulation:
            return
        self._logger.debug('puts() %s', repr(string_data))
        if isinstance(string_data, str):
            string_data = (string_data, )
        for a_string in string_data:
            self.put(a_string.encode(), preflush, postflush, priority)

    def putch(self, data, preflush=0, postflush=0, priority=False):
        """Put data character by character into the read-back queue.

        @param data String to be entered character by character.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to use high priority queue.
        Note: _FLUSH is a marker to stop the flush of the data queue.

        """
        if not self.simulation:
            return
        self._logger.debug('putch() %s', repr(data))
        self._put_flush(preflush, priority)
        for c in data:
            self.put(c.encode(), priority=priority)
        self._put_flush(postflush, priority)

    def put(self, data, preflush=0, postflush=0, priority=False):
        """Put data into the read-back queue.

        @param data Bytes of data.
        @param preflush Number of _FLUSH to be entered before the data.
        @param postflush Number of _FLUSH to be entered after the data.
        @param priority True to use high priority queue.
        Note: _FLUSH is a marker to stop the flush of the data queue.

        """
        if not self.simulation:
            return
        self._put_flush(preflush, priority)
        que = self._in_queue_hi if priority else self._in_queue_lo
        que.put(data)
        self._put_flush(postflush, priority)

    def _put_flush(self, flush_count, priority):
        """Add flush stop markers into the queue.

        @param flush_count Number of _FLUSH to be entered.
        @param priority True to use high priority queue.
        Note: _FLUSH is a marker to stop the flush of the data queue.

        """
        que = self._in_queue_hi if priority else self._in_queue_lo
        for _ in range(flush_count):
            que.put(_FLUSH)

    def get(self):
        """Get data from the written-out queue.

        @return Bytes from the queue.

        """
        return b'' if self._out_queue.empty() else self._out_queue.get()

    def enable(self):
        """Enable reading of the read-back queue."""
        self._enable.set()

    def disable(self):
        """Disable reading of the read-back queue."""
        self._enable.clear()


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
        super().__init__(           # Initialise the _Simulator()
            simulation=simulation,
            port=port, baudrate=baudrate, bytesize=bytesize, parity=parity,
            stopbits=stopbits, timeout=timeout, xonxoff=xonxoff,
            rtscts=rtscts, writeTimeout=writeTimeout, dsrdtr=dsrdtr,
            interCharTimeout=interCharTimeout)

    def open(self):
        """Open port."""
        self._logger.debug('Open port')
        if not self.simulation:
            super().open()
        self._isOpen = True

    def close(self):
        """Close port."""
        self._logger.debug('Close port')
        if not self.simulation:
            try:
                super().close()
            except:
                pass
        self._isOpen = False

    def makeDeviceName(self, port):
        return 'simulation'

    def read(self, size=1):
        """A non-blocking read.

        @param size Number of bytes to read.
        @return Bytes read.

        """
        if not self.simulation:
            return super().read(size)
        if self._enable.is_set():
            if not self._in_queue_hi.empty():
                data = self._in_queue_hi.get()
                return data[:size]       # limit to 'size' bytes
            if not self._in_queue_lo.empty():
                data = self._in_queue_lo.get()
                return data[:size]       # limit to 'size' bytes
        return b''

    def readline(self, size=-1):
        """A non-blocking read.

        @return Bytes read.

        """
        if not self.simulation:
            return super().readline(size)
        if self._enable.is_set():
            if not self._in_queue_hi.empty():
                return self._in_queue_hi.get()
            if not self._in_queue_lo.empty():
                return self._in_queue_lo.get()
        return b''

    def write(self, data):
        """Write data bytes to the written-out queue.

        @param data Bytes to write.

        """
        if not self.simulation:
            super().write(data)
        else:
            self._out_queue.put(data)

    def inWaiting(self):
        """Return the number of characters currently in the input buffer."""
        if not self.simulation:
            return super().inWaiting()
        else:
            return int((not self._in_queue_hi.empty()) or
                       (not self._in_queue_lo.empty()))

    def flush(self):
        """Wait until all output data has been sent."""
        if not self.simulation:
            super().flush()

    def flushInput(self):
        """Discard waiting input.

        A queue value of _FLUSH will stop the flush of the queues.

        """
        if not self.simulation:
            super().flushInput()
        else:
            while not self._in_queue_hi.empty():
                data = self._in_queue_hi.get()
                if data == _FLUSH:
                    return
            while not self._in_queue_lo.empty():
                data = self._in_queue_lo.get()
                if data == _FLUSH:
                    return

    def flushOutput(self):
        """Discard waiting output."""
        if not self.simulation:
            super().flushOutput()
        else:
            while not self._out_queue.empty():
                self._out_queue.get()
