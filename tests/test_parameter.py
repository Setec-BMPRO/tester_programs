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
        self.param = share.ParameterBoolean(_CMD, writeable=True)
        self.func = MagicMock(name='ParBool')

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
        for resp in ('x', 'True', 'False', ''):
            self.func.return_value = resp
            with self.assertRaises(ValueError):
                self.param.read(self.func)

    def test_5_wr_cmd(self):
        """Write command."""
        for val, code in ((True, '1'), (False, '0')):
            self.param.write(val, self.func)
            self.func.assert_called_with('{0} "{1} XN!'.format(code, _CMD))

    def test_6_wr_invalid(self):
        """Invalid data values."""
        for val in (1, 'x', '1', ''):
            with self.assertRaises(share.console.ParameterError):
                self.param.write(val, self.func)
