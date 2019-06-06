#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Advertisment decoder."""

import ctypes
import struct
import threading

import tester


class _SwitchState(list):

    """All RVSWT switch states."""

    def __init__(self, states):
        super().__init__()
        if len(states) != 8:
            raise ValueError('8 (state, count) values are required')
        for state, count in states:
            self.append(_ASwitchState(state, count))


class _ASwitchState():

    """A single RVSWT switch state."""

    def __init__(self, state, count):
        self.state = True if state else False
        self.count = count


class _SwitchField(ctypes.Structure):

    """RVSWT switch field definition.

        Switch 0 bits 3-0, Switch 1 bits 7-4
            The 4-bit switch data format.
            Bit 0 is the switch state 0:open, 1:closed
            Bits 3-1 is a rolling count incremented every new button press
        Switch 2 bits 3-0, Switch 3 bits 7-4
        Switch 4 bits 3-0, Switch 5 bits 7-4
        Switch 6 bits 3-0, Switch 7 bits 7-4

    """

    _fields_ = [
        ('S0state', ctypes.c_uint, 1),
        ('S0count', ctypes.c_uint, 3),
        ('S1state', ctypes.c_uint, 1),
        ('S1count', ctypes.c_uint, 3),
        ('S2state', ctypes.c_uint, 1),
        ('S2count', ctypes.c_uint, 3),
        ('S3state', ctypes.c_uint, 1),
        ('S3count', ctypes.c_uint, 3),
        ('S4state', ctypes.c_uint, 1),
        ('S4count', ctypes.c_uint, 3),
        ('S5state', ctypes.c_uint, 1),
        ('S5count', ctypes.c_uint, 3),
        ('S6state', ctypes.c_uint, 1),
        ('S6count', ctypes.c_uint, 3),
        ('S7state', ctypes.c_uint, 1),
        ('S7count', ctypes.c_uint, 3),
        ]


class _SwitchRaw(ctypes.Union):

    """Union of the RVSWT switch type with unsigned integer."""

    _fields_ = [
        ('uint', ctypes.c_uint),
        ('switch', _SwitchField),
        ]


class Packet():

    """A RVSWT101 BLE broadcast packet."""

    def __init__(self, packet):
        """Create instance.

        @param packet BLE broadcast packet
            EG: [[255, 'Manufacturer', '1f050112022d624c3a00000300d1139e69']]

        """
        payload = packet[0][2]
        payload_bytes = bytearray.fromhex(payload)
        (   self.company_id,
            self.equipment_type,
            self.protocol_ver,
            self.switch_type,
            self.sequence,
            voltage_data,
            switch_data,
            self.signature,
            ) = struct.Struct('<H3B2HLL').unpack(payload_bytes)
        self.cell_voltage = voltage_data * 3.6 / (2^14 - 1) / 1000
        switch_raw = _SwitchRaw()
        switch_raw.uint = switch_data
        zss = switch_raw.switch
        self.switches = _SwitchState((
            (zss.S0state, zss.S0count), (zss.S1state, zss.S1count),
            (zss.S2state, zss.S2count), (zss.S3state, zss.S3count),
            (zss.S4state, zss.S4count), (zss.S5state, zss.S5count),
            (zss.S6state, zss.S6count), (zss.S7state, zss.S7count),
            ))


class RVSWT101():

    """An RVSWT101 'instrument' to read values from."""

    def __init__(self):
        """Create instance."""
        self.lock = threading.Lock()
        self._packet = None

    @property
    def packet(self):
        """Property getter."""
        with self.lock:
            return self._packet

    @packet.setter
    def packet(self, value):
        """Property setter."""
        with self.lock:
            self._packet = value

    def configure(self, key):
        """Configure measurement.

        @param key Parameter key string

        """
        self.key = key

    def opc(self):
        """Dummy OPC."""
        return None

    def read(self, callerid):
        """Read value from my data packet.

        @param callerid Calling sensor instance
        @return Tuple(value)

        """
        return getattr(self.packet, self.key)


class Sensor(tester.sensor.Sensor):

    """RVSWT101 packet data exposed as a Sensor."""

    def __init__(self,
            rvswt, key,
            rdgtype=tester.sensor.Reading, position=1,
            scale=1.0):
        """Create a sensor."""
        super().__init__(rvswt, position)
        self.rvswt = rvswt
        self.key = key
        self._rdgtype = rdgtype
        self.scale = scale

    def configure(self):
        """Configure measurement."""
        self.rvswt.configure(self.key)

    def read(self):
        """Take a reading.

        @return Reading

        """
        value = super().read()
        if self._rdgtype is tester.sensor.Reading:
            value = float(value) * self.scale
        rdg = self._rdgtype(value, position=self.position)
        return (rdg, )

    def __str__(self):
        """Sensor as a string.

        @return String representation of Sensor.

        """
        return 'RVSWT101: {0.doc}'.format(self)

    @property
    def doc(self):
        """Get a documentation entry, if present.

        @return Formatted doc string, or empty string

        """
        result = '({0})'.format(self.units) if self.units else ''
        result += ' {0!r}'.format(self.key)
        if self._doc:
            result += ' {0}'.format(self._doc)
        return result.strip()

    @doc.setter
    def doc(self, value):
        """Set doc property."""
        self._doc = value
