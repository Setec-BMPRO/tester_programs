#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

import functools
import abc
import time
import tester


class TestSequence(tester.TestSequence):

    """Base class for Test Programs.

    Manages the common instances

    """

    devices = None
    limits = None
    sensors = None
    measurements = None
    limit_builtin = (
        tester.LimitRegExp(
            'SerNum',
            r'^[AS][0-9]{4}[0-9A-Z]{2}[0-9]{4}$',
            doc='Valid serial number format'),
        tester.LimitBoolean(
            'Notify',
            True,
            doc='YES response'),
        )

    @abc.abstractmethod
    def open(self, limits, cls_devices, cls_sensors, cls_measurements):
        """Open test program by creating supporting instances.

        @param limits Tuple of test limits
        @param cls_devices Devices class
        @param cls_sensors Sensors class
        @param cls_measurements Measurements class

        """
        super().open()
        self.limits = tester.limitdict(self.limit_builtin + limits)
        self.devices = cls_devices(self.physical_devices, self.fifo)
        self.devices.parameter = self.parameter
        self.sensors = cls_sensors(self.devices, self.limits)
        self.sensors.parameter = self.parameter
        self.measurements = cls_measurements(self.sensors, self.limits)
        self.measurements.parameter = self.parameter
        self.devices.open()
        self.sensors.open()
        self.measurements.open()

    def safety(self):
        """Reset logical devices and sensors."""
        self.devices.reset()
        self.sensors.reset()
        self.measurements.reset()

    def close(self):
        """Close logical devices."""
        self.measurements.close()
        self.sensors.close()
        self.devices.close()
        self.measurements = None
        self.sensors = None
        self.limits = None
        self.devices = None
        super().close()

    def measure(self, names, timeout=0, delay=0):
        """Measure a group of measurements given the measurement names.

        @param names Measurement names
        @param timeout Measurement timeout
        @param delay Time delay after measurements
        @return Measurement result

        """
        measurements = []
        for name in names:
            measurements.append(self.measurements[name])
        result = tester.MeasureGroup(measurements, timeout)
        time.sleep(delay)
        return result

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


class Devices(abc.ABC, dict):

    """Devices abstract base class."""

    physical_devices = None
    fifo = None
    parameter = None
    _close_callables = None         # Callbacks when close() is called

    def __init__(self, physical_devices, fifo):
        """Create instance.

        @param physical_devices Physical instruments
        @param fifo True if FIFOs are active

        """
        super().__init__()
        self.physical_devices = physical_devices
        self.fifo = fifo

    @abc.abstractmethod
    def open(self):
        """Create all Instruments."""

    @abc.abstractmethod
    def reset(self):
        """Reset instruments."""

    def add_closer(self, callable):
        """Add a callable to be called upon close()."""
        if self._close_callables is None:
            self._close_callables = []
        self._close_callables.append(callable)

    def close(self):
        """Close logical devices."""
        if self._close_callables is not None:
            for a_call in self._close_callables:
                a_call()
        self._close_callables = None
        self.clear()


class Sensors(abc.ABC, dict):

    """Sensors."""

    devices = None
    limits = None
    parameter = None

    def __init__(self, devices, limits):
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
            try:
                self[sensor].flush()
            except AttributeError:  # if it's a List of Sensors
                for subsensor in self[sensor]:
                    subsensor.flush()

    def close(self):
        """Close sensors."""
        self.clear()


class Measurements(abc.ABC, dict):

    """Measurements."""

    sensors = None
    limits = None
    parameter = None

    def __init__(self, sensors, limits):
        """Create measurement instance.

        @param sensors Sensors
        @param limits Test limits

        """
        super().__init__()
        self.sensors = sensors
        self.limits = limits

    @abc.abstractmethod
    def open(self):
        """Create all measurements."""

    def reset(self):
        """Reset measurements."""

    def close(self):
        """Close measurements."""
        self.clear()

    def create_from_names(self, namedata):
        """Create measurements from name data.

        @param namedata Iterable of Tuple of
                (measurement_name, limit_name, sensor_name, doc)

        """
        for measurement_name, limit_name, sensor_name, doc in namedata:
            self[measurement_name] = tester.Measurement(
                self.limits[limit_name], self.sensors[sensor_name], doc=doc)


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
