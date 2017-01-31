#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

import functools
import abc
import collections
import logging
import time
import tester
# Easy access to utility methods and classes
from .bluetooth import *
from .console import *
from .can_tunnel import *
from .programmer import *
from .ticker import *
from .timed_data import *

# Data tuple of Test Sequence helper instances
TestSequenceData = collections.namedtuple(
    'TestSequenceData',
    'fifo, per_panel, devices, limits, sensors, measurements, sequence')


class TestSequence(tester.TestSequence):

    """Base class for Test Programs.

    Manages the common instances

    """

    @abc.abstractmethod
    def __init__(self, sequence_data):
        """Create all supporting classes."""
        self.devices = sequence_data.devices
        self.limits = sequence_data.limits
        self.sensors = sequence_data.sensors
        self.measurements = sequence_data.measurements
        super().__init__(
            sequence_data.per_panel,
            sequence_data.sequence,
            sequence_data.fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self.devices.open()
        self.sensors.open()
        self.measurements.open()

    def safety(self):
        """Reset logical devices and sensors."""
        self.devices.reset()
        self.sensors.reset()

    def close(self):
        """Close logical devices."""
        self.devices.close()
        super().close()

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

    def get_serial(self, uuts, limit_name, measurement_name):
        """Find the unit's Serial number.

        @param uuts Tuple of UUT instances
        @param limit_name TestLimit to validate a serial number
        @param measurement_name Measurement to ask the operator for the number
        @return Serial Number

        Inspect uuts[0] first, and if it is not a serial number, use the
        measurement to get the number from the tester operator.

        """
        sernum = str(uuts[0])
        limit = self.limits[limit_name]
        measurement = self.measurements[measurement_name]
        if not limit.check(sernum, position=1, send_signal=False):
            sernum = measurement.measure().reading1
        return sernum


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


class LogicalDevices(abc.ABC, dict):

    """Logical Devices abstract base class."""

    def __init__(self, physical_devices, fifo=False):
        """Create instance.

        @param physical_devices Physical instruments
        @param fifo True if FIFOs are active

        """
        super().__init__()
        self.physical_devices = physical_devices
        self.fifo = fifo

    @abc.abstractmethod
    def open(self):
        """Create all Logical Instruments."""

    @abc.abstractmethod
    def reset(self):
        """Reset instruments."""

    def close(self):
        """Close logical devices."""


class Sensors(abc.ABC, dict):

    """Sensors."""

    def __init__(self, devices, limits=None):
        """Create Sensors instance.

        @param devices Logical instruments
        @param limits Test limits

        """
        super().__init__()
        self.devices = devices
        self.limits = limits

    @abc.abstractmethod
    def open(self):
        """Create all sensors."""

    def reset(self):
        """Reset sensors by flushing any stored data."""
        for sensor in self:
            self[sensor].flush()


class Measurements(abc.ABC, dict):

    """Measurements."""

    def __init__(self, sense, limits):
        """Create Measurements instance.

        @param sense Sensors
        @param limits Test limits

        """
        super().__init__()
        self.sense = sense
        self.limits = limits

    @abc.abstractmethod
    def open(self):
        """Create all Measurements."""


def deprecated(func):
    """Decorator to mark functions as deprecated.

    It will result in a warning when the function is used.

    @return Decorated function

    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.warning(
            'Call to deprecated function "{0}" in "{1}" at line {2}.'.format(
                func.__name__,
                func.__code__.co_filename,
                func.__code__.co_firstlineno + 1)
        )
        return func(*args, **kwargs)
    return new_func


def teststep(func):
    """Decorator to add arguments to the test step calls.

    Requires self.devices and self.measurements

    @return Decorated function

    """
    @functools.wraps(func)
    def new_func(self):
        """Decorate the function."""
        return func(self, self.devices, self.measurements)
    return new_func


def oldteststep(func):
    """Deprecated decorator to add arguments to the test step calls.

    Requires self.logdev and self.meas

    @return Decorated function

    """
    @functools.wraps(func)
    def new_func(self):
        """Decorate the function."""
        return func(self, self.logdev, self.meas)
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
