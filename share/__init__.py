#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

from functools import wraps
from abc import ABC, abstractmethod
# Easy access to utility methods and classes
from .bluetooth import *
from .console import *
from .can_tunnel import *
from .programmer import *
from .ticker import *
from .timed_data import *


class AttributeDict(dict):

    """A dictionary that exposes the keys as instance attributes."""

    def __getattr__(self, name):
        """Access dictionary entries as instance attributes.

        @param name Attribute name
        @return Entry value

        """
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(
                "'{0}' object has no attribute '{1}'".format(
                self.__class__.__name__, name)) from exc


class SupportBase(ABC):

    """Supporting data base class."""

    @abstractmethod
    def __init__(self):
        """Create all supporting classes."""
        self.devices = None
        self.limits = None
        self.sensors = None
        self.measurements = None

    def measure_group(self, names, timeout=0):
        """Measure a group of measurements given the measurement names.

        @param names Measurement names
        @param timeout Measurement timeout

        """
        measurements = []
        for name in names:
            measurements.append(self.measurements[name])
        tester.MeasureGroup(measurements, timeout)

    def reset(self):
        """Reset logical devices."""
        self.devices.reset()

    def close(self):
        """Close logical devices."""
        self.devices.close()


def teststep(func):
    """Decorator to add arguments to the test step calls.

    Requires self.support.devices and self.support.measurements

    @return Decorated function

    """
    @wraps(func)
    def new_func(self):
        """Decorate the function."""
        return func(self, self.support.devices, self.support.measurements)
    return new_func


def oldteststep(func):
    """Deprecated decorator to add arguments to the test step calls.

    Requires self.logdev and self.meas

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
