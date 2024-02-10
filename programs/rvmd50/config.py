#!/usr/bin/env python3
# Copyright 2023 SETEC Pty Ltd.
"""RVMD50x Configuration."""

import logging

import attr


def get(parameter, uut):  # pylint: disable=unused-argument
    """Get a configuration.

    @param parameter Test program parameter
    @param uut setec.tester.UUT instance
    @return Values instance

    """
    return Config.get(uut)


@attr.s
class Values:  # pylint: disable=too-few-public-methods

    """Configuration data values."""

    sw_image = attr.ib(validator=attr.validators.instance_of(str))
    lcd_packet_enable = attr.ib(
        validator=attr.validators.instance_of(bool), default=True
    )


class Config:  # pylint: disable=too-few-public-methods

    """Configuration data storage and lookup."""

    _sw_1_6 = "rvmd50_1.6.bin"
    _sw_1_9 = "rvmd_sam_1.9.0-0-gd59e853.bin"
    _sw_1_13 = "rvmd_sam_1.13.0-0-gda5ce5c.bin"
    _rev_data = {
        None: Values(sw_image=_sw_1_13),
        "8": Values(sw_image=_sw_1_13),
        "7": Values(sw_image=_sw_1_9),
        "6": Values(sw_image=_sw_1_9),
        "5": Values(sw_image=_sw_1_6),
        "4": Values(sw_image=_sw_1_6),
        "3": Values(sw_image=_sw_1_6),
        "2": Values(sw_image=_sw_1_6),
        "1": Values(sw_image=_sw_1_6),
    }

    @classmethod
    def get(cls, uut):
        """Get configuration based on UUT.

        @param uut setec.tester.UUT instance
        @return Values instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        # Firmware 1.13 crashes if you send a LCD Test Packet...
        # There are Production Concessions to not use the packet
        if uut.lot.job in (
            "59445-0",  # PC-103 for RVMD50 (2023-10-24)
            "59458-0",  # PC-102 for RVMD50B
            "59459-0",  # PC-110 for RVMD50B
            "59460-0",  # PC-111 for RVMD50B
            "59581-0",  # PC-112 for RVMD50B
            "59677-0",  # PC-113 for RVMD50
            "59678-0",  # PC-114 for RVMD50T
            "59679-0",  # PC-115 for RVMD50B
            "59812-0",  # PC-116 for RVMD50
            "59813-0",  # PC-117 for RVMD50B
            "59902-0",  # PC-120 for RVMD50
            "59903-0",  # PC-121 for RVMD50B
            "60020-0",  # PC-126 for RVMD50
            "60021-0",  # PC-127 for RVMD50B
            "60133-0",  # PC-132 for RVMD50B
            "60192-0",  # PC-147 for RVMD50B
            "60226-0",  # PC-148 for RVMD50B
            "60343-0",  # PC-149 for RVMD50T
            "60344-0",  # PC-150 for RVMD50B
#            "60416-0",  # PC-xxx for RVMD50B
        ):
            values.lcd_packet_enable = False
        return values
