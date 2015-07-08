#!/usr/bin/env python3
"""Fake serial port."""

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

    def put(self, data):
        """Put data into the read-back queue."""
        self.in_queue.put(data)

    def putch(self, data, blanks=0):
        """Put data character by character into the read-back queue."""
        for _ in range(blanks):
            self.put(b'')
        for c in data:
            self.put(c.encode())

    def get(self):
        """Get data from the written-out queue.

        @return bytes

        """
        if not self.out_queue.empty():
            data = self.out_queue.get()
        else:
            data = b''
        return data

    def flush(self):
        """Flush both input and output queues."""
        self.flushInput()
        self.flushOutput()

    def flushInput(self):
        """Flush input queue."""
        while not self.in_queue.empty():
            data = self.in_queue.get()
            if len(data) == 0:
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

        @return bytes

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
        """Write data bytes to the written-out queue."""
        self.out_queue.put(data)
