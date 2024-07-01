#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""Data feeder version of a Tester for Test programs during unittest.

Subscribe to Tester signals.
Feed FIFO data to Test programs.
Record the test result.

"""

import datetime
import logging
import queue
import unittest
from unittest.mock import Mock, patch

import libtester
import tester
from pydispatch import dispatcher

from . import logging_setup


class UnitTester(tester.Tester):
    """Tester with data feeder functionality."""

    # Dictionary keys into data given to ut_load() method
    key_sen = "Sen"
    key_call = "Call"

    def start(self, tester_type, programs):
        """Initalise the data feeder."""
        self.ut_result = []
        self.ut_steps = []
        self.ut_data = None
        self.ut_sensor_storer = None
        dispatcher.connect(  # Subscribe to the TestStep signals
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step,
        )
        dispatcher.connect(  # Subscribe to the TestResult signals
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result,
        )
        super().start(tester_type, programs)

    def stop(self):
        """Release resources."""
        dispatcher.disconnect(
            self._signal_step,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.step,
        )
        dispatcher.disconnect(
            self._signal_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.result,
        )
        super().stop()

    def ut_load(self, data, sensor_storer):
        """Per-Test data load.

        @param data Dictionary of FIFO data
        @param sensor_storer Callable to push FIFO data into sensors
        @param console_puts Callable to push console data

        """
        self.ut_data = data
        self.ut_sensor_storer = sensor_storer
        self.ut_steps.clear()
        self.ut_result.clear()

    def _signal_step(self, **kwargs):
        """Signal receiver for TestStep signals."""
        stepname = kwargs["name"]
        self.ut_steps.append(stepname)
        self._load_sensors(stepname)
        self._load_callables(stepname)

    def _load_sensors(self, stepname):
        """Sensor FIFOs."""
        try:
            dat = self.ut_data[self.key_sen][stepname]
            self.ut_sensor_storer(dat)
        except KeyError:
            pass

    def _load_callables(self, stepname):
        """Callables."""
        try:
            dat, val = self.ut_data[self.key_call][stepname]
            dat(val)
        except KeyError:
            pass

    def _signal_result(self, **kwargs):
        """Signal receiver for TestResult signals."""
        self.ut_result.append(kwargs["result"])


class ProgramTestCase(unittest.TestCase):
    """Product test program wrapper."""

    debug = False
    prog_class = None
    parameter = ""
    _logger_names = ("tester", "share", "programs")
    per_panel = 1

    @classmethod
    def setUpClass(cls):
        """Per-Class setup."""
        cls.start_time = datetime.datetime.now()
        logging_setup()
        logging.getLogger(__name__).info(
            "setUpClass() '%s' [%s]", cls.prog_class, cls.parameter
        )
        # Set lower level logging level
        for name in cls._logger_names:
            log = logging.getLogger(name)
            log.setLevel(logging.DEBUG if cls.debug else logging.INFO)
        # Patch time.sleep to remove delays
        cls.patcher = patch("time.sleep")
        cls.patcher.start()
        # Create the tester instance
        cls.ut_program = tester.TestProgram(
            repr(cls.prog_class), cls.per_panel, cls.parameter
        )
        cls.tester = UnitTester()
        cls.tester.start(
            libtester.Tester("MockATE", "MockATEa"),
            {repr(cls.prog_class): cls.prog_class},
        )
        cls.uuts = list(
            libtester.UUT.from_sernum("A000000000{0}".format(uut))
            for uut in range(1, cls.per_panel + 1)
        )
        cls.fixture = libtester.Fixture.from_barcode("123456-0001")
        # Looking up devices for a fixture
        cls.patchfixt = patch("share.config.Fixture.port", return_value="DummyPort")
        cls.patchfixt.start()

    def setUp(self):
        """Per-Test setup."""
        # Patch queue.get to speed up open() by removing the UI ping delays
        myq = Mock(name="MyQueue")
        myq.get.side_effect = queue.Empty
        with patch("queue.Queue", return_value=myq):
            self.tester.open(self.ut_program, self.fixture, self.uuts)
        self.test_sequence = self.tester.sequence

    def tearDown(self):
        """Per-Test tear down."""
        self.tester.close()

    @classmethod
    def tearDownClass(cls):
        """Per-Class tear down."""
        # Reset lower level logging level
        for name in cls._logger_names:
            log = logging.getLogger(name)
            log.setLevel(logging.INFO)
        cls.patcher.stop()
        cls.tester.stop()
        elapsed = datetime.datetime.now() - cls.start_time
        elapsed = round(float(elapsed.seconds) + float(elapsed.microseconds) / 1000)
        logging.getLogger(__name__).info(
            "tearDownClass() UnitTest Run Time = %sms", elapsed
        )
