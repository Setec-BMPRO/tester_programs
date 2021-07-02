#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Advertisment decoder."""

import ctypes
import struct

import attr


@attr.s
class _ASwitchState():

    """A single RVSWT switch state."""

    state = attr.ib(converter=bool)
    count = attr.ib(converter=int)


@attr.s
class _SwitchState():

    """All RVSWT switch states."""

    _states = attr.ib()
    @_states.validator
    def _states_len(self, attribute, value):
        """Validate states."""
        if len(self._states) != 8:
            raise ValueError('8 (state, count) values are required')
    _data = attr.ib(init=False, factory=list)

    def __attrs_post_init__(self):
        """Populate _data with _ASwitchState instances."""
        for state, count in self._states:
            self._data.append(_ASwitchState(state, count))

    def __iter__(self):
        """Return iterator of _data."""
        return iter(self._data)

    def __len__(self):
        """Return len of _data."""
        return len(self._data)


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

    def __init__(self, payload):
        """Create instance.

        @param payload BLE broadcast packet payload
            EG: '1f050112022d624c3a00000300d1139e69'

        """
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
        all_switches = ''.join([str(int(val.state)) for val in self.switches])
        self.switch_code = int(all_switches, 2)     #int value between 0-255
        # switch_code expected values:
        # Button1:128  Button2:64  Button3:32
        # Button4:16   Button5:8   Button6:4


@attr.s
class RVSWT101():

    """Custom logical instrument to read packet properties."""

    bleserver = attr.ib()       # tester.BLE instance
    always_scan = attr.ib(init=False, default=True)
    _read_key = attr.ib(init=False, default=None)
    _packet = attr.ib(init=False, default=None)
    scan_count = attr.ib(init=True, default=0)

    def configure(self, key):
        """Sensor: Configure for next reading.
        
        key must be one of: 'cell_voltage', 'company_id',
                            'equipment_type', 'protocol_ver',
                            'sequence', 'signature', 'switch_code',
                            'switch_type', 'switches'
        """
        self._read_key = key

    def opc(self):
        """Sensor: OPC."""
        self.bleserver.opc()

    def read(self, callerid):
        """Sensor: Read payload data using the last configured key.

        @param callerid Identity of caller
        @return Packet property value

        """
        if self.always_scan:
            self.scan_count +=1
            rssi, ad_data = self.bleserver.read(callerid)
            self._packet = Packet(ad_data)
        return getattr(self._packet, self._read_key)

    def reset(self):
        self.bleserver.uut = None
        self.always_scan = False
        self._packet = None
