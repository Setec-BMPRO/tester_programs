#!/usr/bin/env python3
"""UnitTest for share.console parameters."""

import unittest
from unittest.mock import Mock
import share

_CMD = "x"


class Boolean(unittest.TestCase):

    """Boolean test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.parameter.Boolean(_CMD, writeable=True)
        self.func = Mock(name="Parameter")

    def test_1_rd_cmd(self):
        """Read command."""
        self.func.return_value = "0"
        self.param.read(self.func)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_rd_false(self):
        """Valid responses for False."""
        for resp in ("0", " 0", "0 ", " 0 "):
            self.func.return_value = resp
            value = self.param.read(self.func)
            self.assertEqual(False, value)

    def test_3_rd_true(self):
        """Valid responses for True."""
        for resp in ("1", " 1", "1 ", " 1 ", "2"):
            self.func.return_value = resp
            value = self.param.read(self.func)
            self.assertEqual(True, value)

    def test_4_rd_invalid(self):
        """Invalid response values."""
        for resp in ("x", "True", "False", "yes", ""):
            self.func.return_value = resp
            with self.assertRaises(ValueError):
                self.param.read(self.func)

    def test_5_wr_cmd(self):
        """Write command."""
        for val, code in ((True, "1"), (False, "0")):
            self.param.write(val, self.func)
            self.func.assert_called_with('{0} "{1} XN!'.format(code, _CMD), expected=0)

    def test_6_wr_invalid(self):
        """Invalid data values."""
        for val in (1, "x", "1", ""):
            with self.assertRaises(share.console.parameter.ParameterError):
                self.param.write(val, self.func)


class String(unittest.TestCase):

    """String test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.parameter.String(_CMD, writeable=True)
        self.func = Mock(name="Parameter")

    def test_1_rd_cmd(self):
        """Read command."""
        response = "abc "
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(response, value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = "def"
        self.param.write(value, self.func)
        self.func.assert_called_with('{0} "{1} XN!'.format(value, _CMD), expected=0)


class Float(unittest.TestCase):

    """Float test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.parameter.Float(_CMD, writeable=True)
        self.func = Mock(name="Parameter")

    def test_1_rd_cmd(self):
        """Read command."""
        response = "1.234 "
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(float(response), value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = 2.678
        self.param.write(value, self.func)
        self.func.assert_called_with(
            '{0} "{1} XN!'.format(round(value), _CMD), expected=0
        )


class Hex(unittest.TestCase):

    """Hex test suite."""

    def setUp(self):
        """Per-Test setup."""
        self.param = share.console.parameter.Hex(_CMD, writeable=True)
        self.func = Mock(name="Parameter")

    def test_1_rd_cmd(self):
        """Read command."""
        response = "0x1234 "
        self.func.return_value = response
        value = self.param.read(self.func)
        self.assertEqual(int(response, 16), value)
        self.func.assert_called_with('"{0} XN?'.format(_CMD), expected=1)

    def test_2_wr_cmd(self):
        """Write command."""
        value = 234
        self.param.write(value, self.func)
        self.func.assert_called_with(
            '${0:08X} "{1} XN!'.format(round(value), _CMD), expected=0
        )
