#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd.
"""UnitTest for J35 Config module."""

import unittest

import setec

from programs import j35


class J35A_Config(unittest.TestCase):

    """J35-A Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = j35.config.J35A()
        checks = (
            ('A170000', (1, 1, 'B'), cfg.sw_13, False, ),
            ('A172000', (2, 1, 'B'), cfg.sw_13, False, ),
            ('A180000', (8, 1, 'C'), cfg.sw_15, True, ),
            ('A181500', (9, 1, 'B'), cfg.sw_15, True, ),
            ('A999999', (11, 1, 'A'), cfg.sw_15, True, ),
            )
        for lotnum, hw_version, sw_version, canbus in checks:
            uut = setec.UUT.from_sernum(lotnum + '0001')
            cfg.select('A', uut)
            self.assertEqual(hw_version, cfg.hw_version)
            self.assertEqual(sw_version, cfg.sw_version)
            self.assertEqual(canbus, cfg.canbus)


class J35B_Config(unittest.TestCase):

    """J35-B Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = j35.config.J35B()
        checks = (
            ('A164808', (1, 2, 'B'), cfg.sw_13, False, ),
            ('A172000', (2, 2, 'D'), cfg.sw_13, False, ),
            ('A180000', (8, 2, 'C'), cfg.sw_15, True, ),
            ('A181500', (9, 2, 'B'), cfg.sw_15, True, ),
            ('A999999', (11, 2, 'A'), cfg.sw_15, True, ),
            )
        for lotnum, hw_version, sw_version, canbus in checks:
            uut = setec.UUT.from_sernum(lotnum + '0001')
            cfg.select('B', uut)
            self.assertEqual(hw_version, cfg.hw_version)
            self.assertEqual(sw_version, cfg.sw_version)
            self.assertEqual(canbus, cfg.canbus)


class J35C_Config(unittest.TestCase):

    """J35-C Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = j35.config.J35D()
        checks = (
            ('A164000', (4, 3, 'B'), cfg.sw_15, ),
            ('A170000', (6, 3, 'E'), cfg.sw_15, ),
            ('A172000', (7, 3, 'C'), cfg.sw_15, ),
            ('A180000', (8, 3, 'C'), cfg.sw_15, ),
            ('A181500', (9, 3, 'B'), cfg.sw_15, ),
            ('A999999', (11, 3, 'A'), cfg.sw_15, ),
            )
        for lotnum, hw_version, sw_version in checks:
            uut = setec.UUT.from_sernum(lotnum + '0001')
            cfg.select('C', uut)
            self.assertEqual(hw_version, cfg.hw_version)
            self.assertEqual(sw_version, cfg.sw_version)

    def test_scrap_rev(self):
        """Rev of scrap units."""
        cfg = j35.config.J35D()
        checks = (
            ('A154411', (1, 3, 'A'), cfg.sw_15, ),
            ('A160306', (2, 3, 'A'), cfg.sw_15, ),
            ('A161211', (3, 3, 'A'), cfg.sw_15, ),
            )
        for lotnum, hw_version, sw_version in checks:
            uut = setec.UUT.from_sernum(lotnum + '0001')
            with self.assertRaises(KeyError):
                cfg.select('C', uut)


class J35D_Config(unittest.TestCase):

    """J35-D Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = j35.config.J35D()
        checks = (
            ('A181500', (9, 4, 'B'), cfg.sw_15, ),
            ('A999999', (11, 4, 'A'), cfg.sw_15, ),
            )
        for lotnum, hw_version, sw_version in checks:
            uut = setec.UUT.from_sernum(lotnum + '0001')
            cfg.select('D', uut)
            self.assertEqual(hw_version, cfg.hw_version)
            self.assertEqual(sw_version, cfg.sw_version)
