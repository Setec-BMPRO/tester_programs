#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

from functools import wraps
from abc import ABC, abstractmethod
import time
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

    def reset(self):
        """Reset logical devices and sensors."""
        self.devices.reset()
        try:
            self.sensors.reset()
        except AttributeError:
            pass

    def close(self):
        """Close logical devices."""
        self.devices.close()

    def measure(self, names, timeout=0):
        """Measure a group of measurements given the measurement names.

        @param names Measurement names
        @param timeout Measurement timeout

        """
        measurements = []
        for name in names:
            measurements.append(self.measurements[name])
        tester.MeasureGroup(measurements, timeout)

    def dcload(self, setting, output=True, delay=0):
        """DC Load setter.

        @param setting Iterable of Tuple of (DcLoad name, Current)
        @param output Boolean to control output enable
        @param delay Time delay after all setting are made

        """
        for dcl, current in setting:
            self.devices[dcl].output(current, output)
        time.sleep(delay)

    def dcsource(self, setting, output=True, delay=0):
        """DC Source setter.

        @param setting Iterable of Tuple of (DcSource name, Voltage)
        @param output Boolean to control output enable
        @param delay Time delay after all setting are made

        """
        for dcs, voltage in setting:
            self.devices[dcs].output(voltage, output)
        time.sleep(delay)

    def relay(self, relays, delay=0):
        """Relay setter.

        @param relays Iterable of Tuple of (Relay name, State)
                        (True=on | False=Off)
        @param delay Time delay after all setting are made

        """
        for rla, state in relays:
            rla = self.devices[rla]
            if state:
                rla.set_on()
            else:
                rla.set_off()
        time.sleep(delay)

    def ramp_linear(self, setting, output=True, delay=0):
        """Linear ramping.

        @param setting Iterable of Tuple of (Instrument name, Start, End, Step)
        @param output Boolean to control output enable
        @param delay Time delay after all setting are made

        """
        for instr, start, end, step in setting:
            instr = self.devices[instr]
            instr.output(start, output)
            instr.linear(start, end, step)
        time.sleep(delay)

    def ramp_binary(self, setting, output=True, delay=0):
        """Binary ramping.

        @param setting Iterable of Tuple of (Instrument name, Start, End, Step)
        @param output Boolean to control output enable
        @param delay Time delay after all setting are made

        """
        for instr, start, end, step in setting:
            instr = self.devices[instr]
            instr.output(start, output)
            instr.binary(start, end, step)
        time.sleep(delay)


def teststep(func):
    """Decorator to add arguments to the test step calls.

    Requires self.support.devices and self.support.measurements

    @return Decorated function

    """
    @wraps(func)
    def new_func(self):
        """Decorate the function."""
        return func(
            self, self.support,
            self.support.devices, self.support.measurements)
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
