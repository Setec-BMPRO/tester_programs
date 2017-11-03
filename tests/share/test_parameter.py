#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for share.console parameters."""

import unittest
from unittest.mock import MagicMock
import share

_CMD = 'x'


class ParameterBoolean(unittest.TestCase):

    """ParameterBoolean test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.ParameterBoolean(_CMD, writeable=True)
        self.func = MagicMock(name='Parameter')

    def test_1_rd_cmd(self):
        """Read command."""
        self.func.return_value = '0'
        self.param.read(self.func)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_rd_false(self):
        """Valid responses for False."""
        for resp in ('0', ' 0', '0 ', ' 0 '):
            self.func.return_value = resp
            value = self.param.read(self.func)
            self.assertEqual(False, value)

    def test_3_rd_true(self):
        """Valid responses for True."""
        for resp in ('1', ' 1', '1 ', ' 1 ', '2'):
            self.func.return_value = resp
            value = self.param.read(self.func)
            self.assertEqual(True, value)

    def test_4_rd_invalid(self):
        """Invalid response values."""
        for resp in ('x', 'True', 'False', 'yes', ''):
            self.func.return_value = resp
            with self.assertRaises(ValueError):
                self.param.read(self.func)

    def test_5_wr_cmd(self):
        """Write command."""
        for val, code in ((True, '1'), (False, '0')):
            self.param.write(val, self.func)
            self.func.assert_called_with(
                '{0} "{1} XN!'.format(code, _CMD),
                expected=0)

    def test_6_wr_invalid(self):
        """Invalid data values."""
        for val in (1, 'x', '1', ''):
            with self.assertRaises(share.console.ParameterError):
                self.param.write(val, self.func)


class ParameterString(unittest.TestCase):

    """ParameterString test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.ParameterString(_CMD, writeable=True)
        self.func = MagicMock(name='Parameter')

    def test_1_rd_cmd(self):
        """Read command."""
        response = 'abc '
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(response, value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = 'def'
        self.param.write(value, self.func)
        self.func.assert_called_with(
            '{0} "{1} XN!'.format(value, _CMD),
            expected=0)


class ParameterFloat(unittest.TestCase):

    """ParameterFloat test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.ParameterFloat(_CMD, writeable=True)
        self.func = MagicMock(name='Parameter')

    def test_1_rd_cmd(self):
        """Read command."""
        response = '1.234 '
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(float(response), value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = 2.678
        self.param.write(value, self.func)
        self.func.assert_called_with(
            '{0} "{1} XN!'.format(round(value), _CMD),
            expected=0)


class ParameterHex(unittest.TestCase):

    """ParameterHex test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.ParameterHex(_CMD, writeable=True)
        self.func = MagicMock(name='Parameter')

    def test_1_rd_cmd(self):
        """Read command."""
        response = '0x1234 '
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(int(response, 16), value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = 234
        self.param.write(value, self.func)
        self.func.assert_called_with(
            '${0:08X} "{1} XN!'.format(round(value), _CMD),
            expected=0)


class ParameterHex0x(unittest.TestCase):

    """ParameterHex0x test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.ParameterHex0x(_CMD, writeable=True)
        self.func = MagicMock(name='Parameter')

    def test_1_rd_cmd(self):
        """Read command."""
        response = '0x1234 '
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(int(response, 16), value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = 234
        self.param.write(value, self.func)
        self.func.assert_called_with(
            '0x{0:08X} "{1} XN!'.format(round(value), _CMD),
            expected=0)


class ParameterCAN(unittest.TestCase):

    """ParameterCAN test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.ParameterCAN(_CMD, writeable=True)
        self.func = MagicMock(name='Parameter')

    def test_1_rd_cmd(self):
        """Read command."""
        response = 'abc '
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(response, value)
        self.func.assert_called_with('"{0} CAN'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        with self.assertRaises(share.console.ParameterError):
            self.param.write('x', self.func)


class ParameterRaw(unittest.TestCase):

    """ParameterRaw test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.func = MagicMock(name='Parameter')
        self.param = share.console.ParameterRaw(_CMD, writeable=True, func=self.func)

    def test_1_rd_cmd(self):
        """Read command."""
        response = 'abc '
        self.func.return_value = response
        value = self.param.read(None)
        self.assertEqual(response, value)
        self.func.assert_called_with()

    def test_2_wr_cmd(self):
        """Write command."""
        with self.assertRaises(share.console.ParameterError):
            self.param.write('x', self.func)
