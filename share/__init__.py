#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared modules for Tester programs."""

# Easy access to utility methods and classes
from .bluetooth import *
from .console import *
from .can_tunnel import *
from .programmer import *
from .ticker import *
from .timed_data import *


def get_sernum(uuts, lim, measurement):
    """Find the unit's Serial number.

    @param uuts Tuple of UUT instances
    @param lim TestLimit to validate a serial number
    @param measurement UI measurement to ask the operator for the number
    @return Serial Number

    Inspect uuts[0] first, and if it is not a serial number, use the
    measurement to get the number from the tester operator.

    """
    sernum = str(uuts[0])
    if not lim.check(sernum, position=1, send_signal=False):
        sernum = measurement.measure().reading1
    return sernum
