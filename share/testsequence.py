#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

import abc
import contextlib
import functools
import time

import attr
import tester


class DuplicateNameError(Exception):

    """Duplicate name error."""


@attr.s
class TestLimits:

    """Dictionary of Test Limits."""

    _store = attr.ib(init=False, factory=dict)

    def load(self, limitdata):
        """Load Test Limit data.

        @param limitdata iterable(TestLimit)

        """
        self._store.clear()
        for alimit in limitdata:
            self[alimit.name] = alimit

    def __setitem__(self, name, value):
        """Add a Test Limit, rejecting duplicate names.

        @param name Test limit name
        @param value Test limit instance

        """
        if name in self._store:
            raise DuplicateNameError('Limit name "{0}"'.format(name))
        self._store[name] = value

    def __getitem__(self, name):
        """Indexed access by name.

        @param name Test limit name
        @return TestLimit instance

        """
        return self._store[name]


class TestSequence(tester.TestSequence):

    """Base class for Test Programs.

    Manages the common instances

    """

    limit_builtin = (
        tester.LimitRegExp(
            "SerNum", r"^[AS][0-9]{4}[0-9A-Z]{2}[0-9]{4}$", doc="Serial Number"
        ),
        tester.LimitBoolean("Notify", True, doc="YES response"),
        tester.LimitInteger("ProgramOk", 0, doc="Exit code 0"),
    )

    def __init__(self):
        """Create instance variables."""
        super().__init__()
        self.devices = None
        self.limits = TestLimits()
        self.sensors = None
        self.measurements = None
        self.parameter = None

    @abc.abstractmethod
    def open(self, limits, cls_devices, cls_sensors, cls_measurements):
        """Open test program by creating supporting instances.

        @param limits Tuple of test limits
        @param cls_devices Devices class
        @param cls_sensors Sensors class
        @param cls_measurements Measurements class

        """
        super().open()
        self.limits.load(self.limit_builtin + limits)
        self.devices = cls_devices(self.physical_devices)
        self.devices.parameter = self.parameter
        self.sensors = cls_sensors(self.devices, self.limits)
        self.sensors.parameter = self.parameter
        self.measurements = cls_measurements(self.sensors, self.limits)
        self.measurements.parameter = self.parameter
        self.devices.open()
        self.sensors.open()
        self.measurements.open()

    def run(self, uuts):
        """Run the test sequence.

        @param uuts Iterable of Unit Under Test's

        """
        self.devices.run()
        super().run(uuts)

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
        super().close()

    def measure(self, names, timeout=0, delay=0):
        """Measure a group of measurements given the measurement names.

        Don't stop on a failure within the group.

        @param names Tuple of Measurement names
        @param timeout Measurement timeout
        @param delay Time delay after measurements
        @return Measurement result

        """
        with MultiMeasurementSummary(default_timeout=timeout) as checker:
            for name in names:
                checker.measure(self.measurements[name])
        time.sleep(delay)
        return checker.result

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

        @param uuts Tuple of libtester.UUT instances
        @param limit_name TestLimit to validate a serial number
        @param measurement_name Measurement to ask the operator for the number
        @return Serial Number

        Inspect uuts[0] first, and if it is not a serial number, use the
        measurement to get the number from the tester operator.

        """
        try:
            sernum = uuts[0].sernum
        except AttributeError:
            sernum = ""
        limit = self.limits[limit_name]
        measurement = self.measurements[measurement_name]
        if not limit.check(sernum):
            sernum = measurement.measure().value1
        return sernum


@attr.s
class Devices(abc.ABC):

    """Devices abstract base class."""

    physical_devices = attr.ib()
    parameter = attr.ib(init=False, default=None)
    _close_callables = attr.ib(init=False, factory=list)
    _store = attr.ib(init=False, factory=dict)

    def __setitem__(self, name, value):
        """Add a Device, rejecting duplicate names.

        @param name Device name
        @param value Device instance

        """
        if name in self._store:
            raise DuplicateNameError('Device name "{0}"'.format(name))
        self._store[name] = value

    def __getitem__(self, name):
        """Indexed access by name.

        @param name Device name
        @return Device instance

        """
        return self._store[name]

    @abc.abstractmethod
    def open(self):
        """Create all devices."""

    def run(self):
        """Test run is starting."""

    @abc.abstractmethod
    def reset(self):
        """Test run has stopped - Reset instruments."""

    def add_closer(self, target):
        """Add a callable to be called upon close()."""
        self._close_callables.append(target)

    def close(self):
        """Close devices."""
        self._close_callables.reverse()  # Close in LIFO order
        for target in self._close_callables:
            target()
        self._close_callables.clear()
        self._store.clear()


@attr.s
class Sensors(abc.ABC):

    """Sensors."""

    devices = attr.ib()
    limits = attr.ib()
    parameter = attr.ib(init=False, default=None)
    _store = attr.ib(init=False, factory=dict)

    def __setitem__(self, name, value):
        """Add a Sensor, rejecting duplicate names.

        @param name Sensor name
        @param value Sensor instance

        """
        if name in self._store:
            raise DuplicateNameError('Sensor name "{0}"'.format(name))
        self._store[name] = value

    def __getitem__(self, name):
        """Indexed access by name.

        @param name Sensor name
        @return Sensor instance

        """
        return self._store[name]

    @abc.abstractmethod
    def open(self):
        """Create all sensors."""

    def reset(self):
        """Reset sensors by flushing any stored data."""
        for name, sensor in self._store.items():
            try:
                for subsensor in iter(sensor):  # It could be a sequence of sensors
                    subsensor.clear()
            except TypeError:  # Not iterable is a single sensor
                sensor.clear()

    def close(self):
        """Close sensors."""
        self._store.clear()


@attr.s
class Measurements(abc.ABC):

    """Measurements."""

    sensors = attr.ib()
    limits = attr.ib()
    parameter = attr.ib(init=False, default=None)
    _store = attr.ib(init=False, factory=dict)

    def __setitem__(self, name, value):
        """Add a Measurement, rejecting duplicate names.

        @param name Measurement name
        @param value Measurement instance

        """
        if name in self._store:
            raise DuplicateNameError('Measurement name "{0}"'.format(name))
        self._store[name] = value

    def __getitem__(self, name):
        """Indexed access by name.

        @param name Measurement name
        @return Measurement instance

        """
        return self._store[name]

    @abc.abstractmethod
    def open(self):
        """Create all measurements."""

    def reset(self):
        """Reset measurements."""

    def close(self):
        """Close measurements."""
        self._store.clear()

    def create_from_names(self, namedata):
        """Create measurements from name data.

        @param namedata Iterable of Tuple of
                (measurement_name, limit_name, sensor_name, doc)

        """
        for measurement_name, limit_name, sensor_name, doc in namedata:
            self[measurement_name] = tester.Measurement(
                self.limits[limit_name], self.sensors[sensor_name], doc=doc
            )


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


@attr.s
class MultiMeasurementSummary:

    """Check multiple measurements and calculate overall result."""

    default_timeout = attr.ib(
        validator=attr.validators.instance_of((int, float)), default=0
    )
    result = attr.ib(init=False, factory=tester.MeasurementResult)
    _sensor_positions = attr.ib(init=False, factory=set)

    def __enter__(self):
        """Context Manager entry handler.

        @return self

        """
        return self

    def __exit__(self, exct_type, exce_value, trace_back):
        """Context Manager exit handler - Check overall result."""
        with contextlib.suppress(tester.measure.NoResultError):
            result_overall = self.result.result
            lim = tester.LimitBoolean("AllOk", True, doc="All passed")
            sen = tester.sensor.Mirror()
            mes = tester.Measurement(lim, sen, doc="All checks ok")
            mes.log_data = False
            sen.position = tuple(self._sensor_positions)
            sen.store(result_overall)
            mes.measure()

    def measure(self, measurement, timeout=0):
        """Make a single measurement.

        @param measurement Measurement instance
        @param timeout Timeout for measurement
        @return MeasurementResult instance

        """
        tmo = timeout if timeout else self.default_timeout
        for val in measurement.sensor.position:
            self._sensor_positions.add(val)
        with measurement.position_fail_disabled():
            mres = measurement.measure(timeout=tmo)
        with contextlib.suppress(tester.measure.NoResultError):
            for rdg in mres.readings:
                self.result.append(mres.result, rdg)
        return self.result
