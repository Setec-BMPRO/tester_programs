#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

import functools
import logging
# Easy access to utility methods and classes
from .testsequence import *     # pylint:disable=W0401
from .bluetooth import *        # pylint:disable=W0401
from .console import *          # pylint:disable=W0401
from .programmer import *       # pylint:disable=W0401
from .ticker import *           # pylint:disable=W0401
from .timed_data import *       # pylint:disable=W0401
from .timer import *            # pylint:disable=W0401
from .fixture import *          # pylint:disable=W0401


def deprecated(func):
    """Decorator to mark functions as deprecated.

    It will result in a warning when the function is used.

    @return Decorated function

    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        """Decorate the function."""
        logger = logging.getLogger(__name__)
        logger.warning(
            'Call to deprecated function %s',
            '"{0}" in "{1}" at line {2}.'.format(
                func.__name__,
                func.__code__.co_filename,
                func.__code__.co_firstlineno + 1)
        )
        return func(*args, **kwargs)
    return new_func


@deprecated
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
