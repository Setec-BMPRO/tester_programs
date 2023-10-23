#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 SETEC Pty Ltd.
"""RVMD50x Configuration."""

import logging

import attr


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @param uut setec.tester.UUT instance
    @return configuration class

    """
    Config._configure(uut)  # Adjust for the revision
    return Config


@attr.s
class Values:

    """Adjustable configuration data values."""

    sw_image = attr.ib(validator=attr.validators.instance_of(str))


class Config:

    """Base configuration for RVMN101 and RVMN5x."""

    values = None  # Values instance
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
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.tester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.values = cls._rev_data[rev]
