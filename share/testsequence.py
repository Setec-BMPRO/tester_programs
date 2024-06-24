#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

import contextlib
import functools
import time
from typing import Any, Callable, Optional, Sequence, Union

from attrs import define, field, validators
import libtester
import tester

from . import bluetooth
from . import config


class DuplicateNameError(Exception):
    """Duplicate name error."""


def teststep(func: Callable) -> Callable:
    """Decorator to add arguments to the test step calls.

    Requires self.devices and self.measurements

    @return Decorated function

    """

    @functools.wraps(func)
    def new_func(self) -> Callable:
        """Decorate the function."""
        return func(self, self.devices, self.measurements)

    return new_func


@define
class Devices:
    """Devices abstract base class."""

    tester_type = field(validator=validators.instance_of(str))
    physical_devices = field(validator=validators.instance_of(tester.PhysicalDevices))
    fixture: libtester.Fixture = field(
        validator=validators.instance_of(libtester.Fixture)
    )
    parameter = field(validator=validators.optional(validators.instance_of(str)))
    _close_callables = field(init=False, factory=list)
    _store = field(init=False, factory=dict)

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

    def open(self):
        """Create all devices."""

    def run(self):
        """Test run is starting."""

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

    def port(self, name: str) -> str:
        """Find the device name of a serial port."""
        return config.Fixture.port(self.tester_type, self.fixture, name)


@define
class TestLimits:
    """Dictionary of Test Limits."""

    _store = field(init=False, factory=dict)

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


@define
class Sensors:
    """Sensors."""

    devices = field(validator=validators.instance_of(Devices))
    limits = field(validator=validators.instance_of(TestLimits))
    parameter = field()
    _store = field(init=False, factory=dict)

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

    def open(self):
        """Create all sensors."""

    def reset(self):
        """Reset sensors by flushing any stored data."""
        for sensor in self._store.values():
            try:
                for subsensor in iter(sensor):  # It could be a sequence of sensors
                    subsensor.clear()
            except TypeError:  # Not iterable is a single sensor
                sensor.clear()

    def close(self):
        """Close sensors."""
        self._store.clear()


@define
class Measurements:
    """Measurements."""

    sensors = field(validator=validators.instance_of(Sensors))
    limits = field(validator=validators.instance_of(TestLimits))
    parameter = field()
    _store = field(init=False, factory=dict)

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


@define
class TestSequenceMixin:
    """Utility methods for Test Programs."""

    _limit_builtin = (  # Built-in limits available to every test program
        libtester.LimitBoolean("Notify", True, doc="YES response"),
        libtester.LimitInteger("ProgramOk", 0, doc="Exit code 0"),
    )

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

    def port(self, name: str) -> str:
        """Find the device name of a serial port."""
        return self.devices.port(name)

    def ble_rssi_dev(self) -> None:
        """Generic configuration of a BLE MAC & Scanning server."""
        ble_dev = tester.BLE(
            (self.physical_devices["BLE"], self.physical_devices["MAC"])
        )
        rssi_decoder = bluetooth.RSSI(ble_dev)
        rssi_sensor = tester.sensor.Keyed(rssi_decoder, "rssi")
        rssi_sensor.rereadable = True
        # Pre-populate devices and sensors
        self.devices["BLE"] = ble_dev
        self.devices["RSSIDecoder"] = rssi_decoder
        self.sensors["RSSI"] = rssi_sensor


@define
class TestSequence(tester.TestSequenceEngine, TestSequenceMixin):
    """Base class for Test Programs."""

    physical_devices: tester.devphysical.PhysicalDevices = field(
        validator=validators.instance_of(tester.devphysical.PhysicalDevices),
    )
    limits: TestLimits = field(init=False, factory=TestLimits)
    devices: Optional[Devices] = field(
        init=False,
        default=None,
        validator=validators.optional(validators.instance_of(Devices)),
    )
    sensors: Optional[Sensors] = field(
        init=False,
        default=None,
        validator=validators.optional(validators.instance_of(Sensors)),
    )
    measurements: Optional[Measurements] = field(
        init=False,
        default=None,
        validator=validators.optional(validators.instance_of(Measurements)),
    )

    def configure(
        self,
        limits: Sequence[libtester.LimitABC],
        cls_devices: Devices,
        cls_sensors: Sensors,
        cls_measurements: Measurements,
    ) -> None:
        """Configure test program by creating supporting instances.

        @param limits Iterable libtester.Limit*
        @param cls_devices subclass of Devices
        @param cls_sensors subclass of Sensors
        @param cls_measurements subclass of Measurements

        """
        self.limits.load(self._limit_builtin + limits)
        self.devices = cls_devices(
            self.tester_type, self.physical_devices, self.fixture, self.parameter
        )
        self.sensors = cls_sensors(self.devices, self.limits, self.parameter)
        self.measurements = cls_measurements(self.sensors, self.limits, self.parameter)

    def open(self) -> None:
        """Open test program."""
        config.System.tester_type = self.tester_type
        super().open()
        self.devices.open()
        self.sensors.open()
        self.measurements.open()

    def run(self) -> None:
        """Run the test sequence."""
        self.devices.run()
        super().run()

    def safety(self) -> None:
        """Reset everything ready for another test."""
        self.devices.reset()
        self.sensors.reset()
        self.measurements.reset()
        super().safety()

    def close(self) -> None:
        """Close everything."""
        self.measurements.close()
        self.sensors.close()
        self.devices.close()
        super().close()


@define
class MultiMeasurementSummary:
    """Check multiple measurements and calculate overall result."""

    default_timeout: Union[int, float] = field(
        validator=validators.instance_of((int, float)), default=0
    )
    result: tester.MeasurementResult = field(
        init=False, factory=tester.MeasurementResult
    )
    _sensor_positions: set = field(init=False, factory=set)

    def __enter__(self) -> "MultiMeasurementSummary":
        """Context Manager entry handler.

        @return self

        """
        return self

    def __exit__(self, exct_type: Any, exce_value: Any, trace_back: Any) -> None:
        """Context Manager exit handler - Check overall result."""
        with contextlib.suppress(tester.measure.NoResultError):
            result_overall = self.result.result
            lim = libtester.LimitBoolean("AllOk", True, doc="All passed")
            sen = tester.sensor.Mirror()
            mes = tester.Measurement(lim, sen, doc="All checks ok")
            mes.log_data = False
            sen.position = tuple(self._sensor_positions)
            sen.store(result_overall)
            mes.measure()

    def measure(
        self, measurement: tester.Measurement, timeout: int = 0
    ) -> tester.MeasurementResult:
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
