#!/usr/bin/env python3
# Copyright 2024 SETEC Pty Ltd.
"""DCX Configurations."""

import logging

from attrs import define, field, validators

import libtester


def get(parameter, uut):
    """Get a configuration based on the parameter and lot.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    DCX._configure(uut)  # Adjust for the revision
    return DCX


@define
class _Values:
    """Adjustable configuration data values."""

    hw_version = field(validator=validators.instance_of(tuple))
    sw_image = field(validator=validators.instance_of(str))


class DCX:
    """Base configuration."""

    values = None  # This value is set per Product type & revision

    vbat_in = 12.4
    iload = 28.0
    ibatt = 4.0
    outputs = 14
    vout_set = 12.8
    limits = (
        libtester.LimitDelta("Vload", 12.45, 0.45, doc="Load output present"),
        libtester.LimitLow("FixtureLock", 200, doc="Contacts closed"),
        libtester.LimitLow("VloadOff", 0.5, doc="Load output off"),
        libtester.LimitDelta("VbatIn", 12.0, 0.5, doc="Injected Vbatt present"),
        libtester.LimitBetween("Vbat", 12.2, 13.0, doc="Vbatt present"),
        libtester.LimitDelta("Vaux", 13.4, 0.4, doc="Vaux present"),
        libtester.LimitDelta("3V3", 3.30, 0.05, doc="3V3 present"),
        libtester.LimitBetween("ARM-SecT", 8.0, 70.0, doc="Reading ok"),
        libtester.LimitDelta("ARM-Vout", 12.45, 0.45),
        libtester.LimitDelta("ARM-LoadI", 2.1, 0.9, doc="Load current flowing"),
        libtester.LimitDelta("ARM-BattI", ibatt, 1.0, doc="Battery current flowing"),
        libtester.LimitInteger("ARM-RemoteClosed", 1, doc="REMOTE input connected"),
        libtester.LimitDelta(
            "CanPwr", vout_set, delta=3.0, doc="CAN bus power present"
        ),
        libtester.LimitRegExp("CAN_RX", r"^RRQ,32,0", doc="Expected CAN message"),
        libtester.LimitInteger("CAN_BIND", 1 << 28, doc="CAN comms established"),
        libtester.LimitInteger("Vout_OV", 0, doc="Over-voltage not triggered"),
        libtester.LimitRegExp("Reply", "^OK$"),
        libtester.LimitBetween("15Vs", 11.5, 13.0, doc="Control rail present"),
    )

    _rev1_values = _Values(
        hw_version=(1, 9999, "A"),
        sw_image="dcx_1.0.8-0-g1049123.bin",
    )
    _rev_data = {
        None: _rev1_values,
        "1": _rev1_values,
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        _rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", _rev)
        cls.values = cls._rev_data[_rev]
