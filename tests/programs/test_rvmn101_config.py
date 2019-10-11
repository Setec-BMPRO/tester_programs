#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""UnitTest for RVMN101 Config module."""

import collections
import unittest

from programs import rvmn101


# Simple simulation of tester_storage.UUT class
UUT = collections.namedtuple('UUT', 'lot')


class RVMN101A_Config(unittest.TestCase):

    """RVMN101A Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = rvmn101.config.RVMN101A()
        checks = (
            ('A192000',
                'dunno', cfg._arm_image, '05A', '05A', ),
            ('A192800',
                'dunno', cfg._arm_image, '06A', '06A', ),
            ('A193000',
                cfg._nordic_133, cfg._arm_image, '07A', '07A', ),
            ('A195000',
                cfg._nordic_181, cfg._arm_image, '08A', '08A', ),
            )
        for (
                uut, nordic_image, arm_image,
                product_rev, hardware_rev,
                ) in checks:
            cfg.get('A', UUT(uut))
            self.assertEqual(nordic_image, cfg.nordic_image)
            self.assertEqual(arm_image, cfg.arm_image)
            self.assertEqual(product_rev, cfg.product_rev)
            self.assertEqual(hardware_rev, cfg.hardware_rev)


class RVMN101B_Config(unittest.TestCase):

    """RVMN101B Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = rvmn101.config.RVMN101B()
        checks = (
            ('A193000',
                cfg._nordic_088, cfg._arm_image, '05B', None, ),
            )
        for (
                uut, nordic_image, arm_image,
                product_rev, hardware_rev,
                ) in checks:
            cfg.get('B', UUT(uut))
            self.assertEqual(nordic_image, cfg.nordic_image)
            self.assertEqual(arm_image, cfg.arm_image)
            self.assertEqual(product_rev, cfg.product_rev)
            self.assertEqual(hardware_rev, cfg.hardware_rev)
