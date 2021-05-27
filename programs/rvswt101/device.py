#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Advertisment decoder."""

import ctypes, collections
import struct

import share, tester


class _SwitchState(collections.abc.Iterable):

    """All RVSWT switch states."""

    def __init__(self, states):
        self._data = []
        if len(states) != 8:
            raise ValueError('8 (state, count) values are required')
        for state, count in states:
            self._data.append(_ASwitchState(state, count))

    def __iter__(self):
        return iter(self._data)


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
        all_switches = ''.join([str(int(v.state)) for v in self.switches])
        self.switch_code = int(all_switches, 2)     #int value between 0-255
        # switch_code expected values:
        # Button1:128  Button2:64  Button3:32
        # Button4:16   Button5:8   Button6:4



class RVSWT101():
    
    def __init__(self, server):
        """Create instance.

        @param server URL of the server

        """
        self._pi_bt = share.bluetooth.RaspberryBluetooth(server)
        self._read_key = None
        self.mac = None
        self.read_scan = False
        self.ble_adtype_manufacturer = '255'
        # BLE Packet decoder
        self._decoder = tester.CANPacketDevice()
        
    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._read_key = key

    def opc(self):
        """Sensor: Dummy OPC.

        @return None

        """
        return None

    def read(self,):
        """Sensor: Read bluetooth payload data using the last defined key.

        @param callerid Identity of caller
        @return Value

        """
        if not self._decoder.packet or self.read_scan:
            #reply = self._pi_bt.scan_advert_blemac(self.mac, timeout=20)
            reply = {'ad_data': {'255': '1f050112022d624c3a00000300d1139e69'}, 'rssi': -50}
            
            packet = reply['ad_data'][self.ble_adtype_manufacturer]
            self._decoder.packet = Packet(packet)

        self._decoder.configure(self._read_key)
        return self._decoder.read(None)
        
    def reset(self):
        self.read_scan = False
        self._decoder.packet = None
    
