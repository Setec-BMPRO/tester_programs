#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 BLE Advertisment packet decoder."""

import ctypes
import struct

from attrs import define, field

import tester


class _Switch(ctypes.Structure):  # pylint: disable=too-few-public-methods

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
        ("S0state", ctypes.c_uint, 1),
        ("S0count", ctypes.c_uint, 3),
        ("S1state", ctypes.c_uint, 1),
        ("S1count", ctypes.c_uint, 3),
        ("S2state", ctypes.c_uint, 1),
        ("S2count", ctypes.c_uint, 3),
        ("S3state", ctypes.c_uint, 1),
        ("S3count", ctypes.c_uint, 3),
        ("S4state", ctypes.c_uint, 1),
        ("S4count", ctypes.c_uint, 3),
        ("S5state", ctypes.c_uint, 1),
        ("S5count", ctypes.c_uint, 3),
        ("S6state", ctypes.c_uint, 1),
        ("S6count", ctypes.c_uint, 3),
        ("S7state", ctypes.c_uint, 1),
        ("S7count", ctypes.c_uint, 3),
    ]


@define
class PacketDecoder(tester.sensor.KeyedDataDecoderMixIn):

    """RVSWT101 BLE broadcast packet decoder."""

    def worker(self, fields, data):
        """Decode packet.

        @param fields Dictionary to hold decoded field data
        @param data Tuple(
            rssi RSSI value
            payload BLE broadcast packet payload
                EG: '1f050112022d624c3a00000300d1139e69'
            )

        """
        fields["rssi"], payload = data
        payload_bytes = bytes.fromhex(payload)
        try:
            (
                fields["company_id"],
                fields["equipment_type"],
                fields["protocol_ver"],
                fields["switch_type"],
                fields["sequence"],
                voltage_data,
                switch_data,
                fields["signature"],
            ) = struct.Struct("<H3B2HLL").unpack(payload_bytes)
        except struct.error:
            mes = tester.Measurement(
                tester.LimitBoolean("valid_packet", True, "Non-empty packet"),
                tester.sensor.Mirror(),
            )
            mes.sensor.store(False)
            mes()
        fields["cell_voltage"] = voltage_data * 3.6 / (2 ^ 14 - 1) / 1000
        # Decode the switch data
        sw_fields = _Switch.from_buffer_copy(switch_data.to_bytes(4, "little"))
        # pylint: disable=protected-access
        values = list(getattr(sw_fields, name) for name, _, _ in _Switch._fields_)
        states = []
        for index in range(0, len(values), 2):  # Every 2nd value is a button state
            states.append(values[index])
        # Build a 8 character binary string
        all_switches = "".join([str(int(val)) for val in states])
        # Convert to an integer value between 0-255
        fields["switch_code"] = int(all_switches, 2)


@define
class RVSWT101:

    """Custom logical instrument to read packet properties."""

    bleserver = field()
    always_scan = field(init=False, default=True)
    _key = field(init=False, default=None)
    _decoder = field(init=False, factory=PacketDecoder)

    def configure(self, key):
        """Sensor: Configure for next reading."""
        self._key = key

    def opc(self):
        """Sensor: OPC."""
        self.bleserver.opc()

    def read(self, callerid):
        """Sensor: Read packet payload data using the last configured key.

        @param callerid Identity of caller
        @return Packet property value

        """
        if self.always_scan:
            rssi, ad_data = self.bleserver.read(callerid)
            self._decoder.decode((rssi, ad_data, ))
        return self._decoder.get(self._key)

    def reset(self):
        """Reset internal state."""
        self.bleserver.uut = None
        self.always_scan = True
        self._decoder.clear()
