#!/usr/bin/env python3
# Copyright 2023 SETEC Pty Ltd.
"""RVMD50x Configuration."""

import logging

import attr


def get(parameter, uut):  # pylint: disable=unused-argument
    """Get a configuration.

    @param parameter Test program parameter
    @param uut libtester.UUT instance
    @return Values instance

    """
    return Config.get(uut)


@attr.s
class Values:  # pylint: disable=too-few-public-methods

    """Configuration data values."""

    sw_image = attr.ib(validator=attr.validators.instance_of(str))


class Config:  # pylint: disable=too-few-public-methods

    """Configuration data storage and lookup."""

    _sw_1_6 = "rvmd50_1.6.bin"
    _sw_1_9 = "rvmd_sam_1.9.0-0-gd59e853.bin"
    _sw_1_14 = "rvmd_sam_1.14.0-0-g2235c2a.bin"
    _rev_data = {
        None: Values(sw_image=_sw_1_14),
        "9": Values(sw_image=_sw_1_14),
        "8": Values(sw_image=_sw_1_14),  # MA-409
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

        @param uut libtester.UUT instance
        @return Values instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        return cls._rev_data[rev]
