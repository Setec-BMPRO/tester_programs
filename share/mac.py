#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""IEEE 802 EUI-48 MAC Address.

See https://en.wikipedia.org/wiki/MAC_address

"""

import re

from attrs import define, field, validators


@define
class MAC:
    """Device MAC address."""

    regex = r"^([0-9A-Fa-f]{2}[:\-]?){5}[0-9A-Fa-f]{2}$"
    _mac_re = re.compile(regex)

    mac = field(validator=validators.instance_of(bytes))

    @mac.validator
    def _mac_validator(self, _, value):
        """MAC Address must be 48-bits (6 bytes)."""
        if len(value) != 6:
            raise ValueError("A MAC must be 48 bits long")

    @classmethod
    def loads(cls, mac_str):
        """Class factory to create a MAC from a string.

        @return MAC instance

        """
        if not cls._mac_re.match(mac_str):
            raise ValueError("MAC does not match {0!r}".format(cls.regex))
        return cls(bytes.fromhex(mac_str.replace(":", "").replace("-", "")))

    def dumps(self, separator="-", lowercase=False):
        """Dump the MAC as a string.

        @param separator String to separate the bytes.
        @param lowercase Convert to lowercase.
        @return MAC as a string.

        """
        data = []
        for abyte in self.mac:
            data.append("{0:02X}".format(abyte))
        data_str = separator.join(data)
        if lowercase:
            data_str = data_str.lower()
        return data_str

    @property
    def oui(self):
        """Organisationally Unique Identifier.

        @return 3 OUI bytes

        """
        return self.mac[:3]

    @property
    def nic(self):
        """Network Interface Controller Specific.

        @return 3 NIC bytes

        """
        return self.mac[3:]

    @property
    def universal(self):
        """Universal (0) / Locally Administered (1) address.

        @return True if universal

        """
        return not bool(self.mac[0] & 0x02)

    @property
    def unicast(self):
        """Unicast (0) or Multicast (1) addressing.

        @return True if unicast

        """
        return not bool(self.mac[0] & 0x01)
