#!/usr/bin/env python3
# Copyright 2014 SETEC Pty Ltd.
"""Bluetooth RSSI signal strength."""

from typing import Any, Optional

from attrs import define, field, validators

import tester


@define
class RSSI:
    """Logical Instrument to read RSSI of BLE advertisment packets."""

    bleserver: tester.BLE = field(validator=validators.instance_of(tester.BLE))
    _key: Optional[str] = field(
        init=False,
        default="",
        validator=validators.optional(validators.instance_of(str)),
    )
    _data: dict = field(init=False, factory=dict)

    def configure(self, key: str) -> None:
        """Sensor: Configure for next reading."""
        self._key = key

    def opc(self) -> None:
        """Sensor: OPC."""
        self.bleserver.opc()

    def read(self, callerid: Any) -> None:
        """Sensor: Read packet payload data using the last configured key.

        @param callerid Identity of caller
        @return Packet property value

        """
        rssi, _ = self.bleserver.read(callerid)
        self._data["rssi"] = rssi
        return self._data.get(self._key)

    def reset(self) -> None:
        """Reset internal state."""
        self.bleserver.uut = None
        self._data.clear()
