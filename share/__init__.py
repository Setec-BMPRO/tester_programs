#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

from functools import wraps
# Easy access to utility methods and classes
from .bluetooth import *
from .console import *
from .can_tunnel import *
from .programmer import *
from .ticker import *
from .timed_data import *


class AttrDict():

    """Store dictionary data and expose as instance attributes."""

    def __init__(self, classname):
        self.name = classname
        self.attr = {}

    def __getattr__(self, name):
        """Access dictionary entries as instance attributes."""
        if name in self.attr:
            return self.attr[name]
        else:
            raise AttributeError(
                "'{0}' object has no attribute '{1}'".format(self.name, name))

    def save(self, name, value):
        """Save a value into the attribute dictionary.

        @param name Attribute name
        @param value Attribute value

        """
        self.attr[name] = value


def teststep(func):
    """Decorator to add arguments to the test step calls.

    @return Decorated function

    """
    @wraps(func)
    def new_func(self):
        """Decorate the function."""
        return func(self, self.support.devices, self.support.measurements)
    return new_func


def oldteststep(func):
    """Deprecated decorator to add arguments to the test step calls.

    @return Decorated function

    """
    @wraps(func)
    def new_func(self):
        """Decorate the function."""
        return func(self, self.logdev, self.meas)
    return new_func


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
