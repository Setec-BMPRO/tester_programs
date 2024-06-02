#!/usr/bin/env python3
# Copyright 2016 SETEC Pty Ltd
"""UnitTest for timed_data module."""

import threading
import unittest
from unittest.mock import Mock, patch, call

import share


class BackgroundTimer(unittest.TestCase):
    """BackgroundTimer test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.evt = Mock(name="Event")
        self.evt.is_set.return_value = True
        self._event = threading.Event()

    def test_parameters(self):
        """Parameter validation."""
        with self.assertRaises(ValueError):
            share.BackgroundTimer("x")  # Non-numeric interval
        with self.assertRaises(ValueError):
            share.BackgroundTimer(-1)  # Negative interval
        tmr = share.BackgroundTimer(10)
        tmr.start()
        tmr.stop()


class RepeatTimer(unittest.TestCase):
    """RepeatTimer test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.evt = Mock(name="Event")
        self.evt.is_set.side_effect = (False,) * 2 + (True,) * 2
        self._event = threading.Event()

    def test_parameters(self):
        """Parameter validation."""
        with self.assertRaises(ValueError):
            share.RepeatTimer("x", self._event.set)  # Non-numeric interval
        with self.assertRaises(ValueError):
            share.RepeatTimer(-1, self._event.set)  # Negative interval
        tmr = share.RepeatTimer(10, self._event.set)
        tmr.start()
        tmr.stop()

    def test_run(self):
        """Run RepeatTimer."""
        tmr = share.RepeatTimer(0.001, self._event.set)
        tmr._stop = self.evt
        tmr.start()
        self._event.wait(1)  # Will be set after 1st function call
        self.evt.wait.assert_called_once_with(0.001)
        tmr.stop()


class TimedStore(unittest.TestCase):
    """TimedStore test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.template = {1: 1}
        self.tmr = Mock(name="RepeatTimer")
        patcher = patch("share.timed.RepeatTimer", return_value=self.tmr)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_parameters(self):
        """Parameter validation."""
        with self.assertRaises(TypeError):
            share.TimedStore("x", 5.0)  # non-dictionary template
        with self.assertRaises(ValueError):
            share.TimedStore({}, -5)  # negative interval
        store = share.TimedStore({}, 5)  # valid parameters
        store.start()
        store.stop()

    def test_reset(self):
        """Reset of data."""
        store = share.TimedStore(self.template, 0.6)
        store.start()
        self.assertEqual([call.start()], self.tmr.mock_calls)
        self.assertEqual(self.template, store.data)
        store[2] = 2  # add more data
        self.assertNotEqual(self.template, store.data)
        store.reset()
        self.assertEqual(self.template, store.data)
        store._tick_handler()  # should hit zero & reset data to template
        self.assertEqual(self.template, store.data)

    def test_data(self):
        """Reset of data."""
        store = share.TimedStore(self.template, 0.6)
        store.start()
        self.assertEqual(self.template, store.data)
        store[2] = 2  # add more data
        self.assertNotEqual(self.template, store.data)
        self.assertEqual(store[2], 2)
        self.assertEqual(2, len(store))
        store[3] = 3  # add more data
        self.assertEqual(3, len(store))
        del store[3]
        self.assertEqual(2, len(store))
