#!/usr/bin/env python3
"""Mock Serial Port for testing serial communication modules."""

import time
import queue
import threading


class MockSerial():

    """Simulated serial port for testing."""

    def __init__(self, port=None, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1, timeout=None, xonxoff=False, rtscts=False,
                 writeTimeout=None, dsrdtr=False, interCharTimeout=None):
        """Create internal data storage queue."""
        # Queue to hold data to be read by read()
        self.in_queue = queue.Queue()
        # Queue to hold data written by write()
        self.out_queue = queue.Queue()
        # Control of read() enable
        self._enable = threading.Event()
        self._enable.set()
        self.baudrate = baudrate
        self.timeout = timeout

    def putch(self, data, preflush=0, postflush=0):
        """Put data character by character into the read-back queue.

        @param data String to be entered character by character.
        @param preflush Number of b'' to be entered before the data.
        @param postflush Number of b'' to be entered after the data.
        Note: b'' is a marker to stop the flush of the data queue.

        """
        self._put_flush(preflush)
        for c in data:
            self.put(c.encode())
        self._put_flush(postflush)

    def put(self, data, preflush=0, postflush=0):
        """Put data into the read-back queue.

        @param data Bytes of data.
        @param preflush Number of b'' to be entered before the data.
        @param postflush Number of b'' to be entered after the data.
        Note: b'' is a marker to stop the flush of the data queue.

        """
        self._put_flush(preflush)
        self.in_queue.put(data)
        self._put_flush(postflush)

    def _put_flush(self, flush_count):
        """Add flush stop markers into the queue.

        @param flush_count Number of b'' to be entered.
        Note: b'' is a marker to stop the flush of the data queue.

        """
        for _ in range(flush_count):
            self.put(b'')

    def get(self):
        """Get data from the written-out queue.

        @return Bytes from the queue.

        """
        return b'' if self.out_queue.empty() else self.out_queue.get()

    def flush(self):
        """Flush both input and output queues."""
        self.flushInput()
        self.flushOutput()

    def flushInput(self):
        """Flush input queue.

        A value of b'' will stop the flush of the queue.

        """
        while not self.in_queue.empty():
            data = self.in_queue.get()
            if len(data) == 0:      # This is a b''
                break

    def flushOutput(self):
        """Flush output queue."""
        while not self.out_queue.empty():
            self.out_queue.get()

    def enable(self):
        """Enable reading of the read-back queue."""
        self._enable.set()

    def disable(self):
        """Disable reading of the read-back queue."""
        self._enable.clear()

    def read(self, size=1):
        """A non-blocking read.

        @param size Number of bytes to read.
        @return Bytes read.

        """
# FIXME: Honour the size argument
        if self._enable.is_set() and not self.in_queue.empty():
            data = self.in_queue.get()
        else:
# FIXME: Should we use the timeout from the call to __init__() ?
            time.sleep(0.1)
            data = b''
        return data

    def write(self, data):
        """Write data bytes to the written-out queue.

        @param data Bytes to write.

        """
        self.out_queue.put(data)
