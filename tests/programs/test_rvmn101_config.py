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
                'dunno', cfg._arm_image_19, '05A', '05A', 4, ),
            ('A192800',
                'dunno', cfg._arm_image_19, '06A', '06A', 4, ),
            ('A193000',
                cfg._nordic_133, cfg._arm_image_19, '07A', '07A', 4, ),
            ('A195000',
                cfg._nordic_181, cfg._arm_image_19, '08A', '08A', 4, ),
            ('A200100',
                cfg._nordic_XXX, cfg._arm_image_XX, '09A', '09A', 6, ),
            )
        for (
                uut, nordic_image, arm_image,
                product_rev, hardware_rev, banner_lines,
                ) in checks:
            cfg.get('A', UUT(uut))
            self.assertEqual(nordic_image, cfg.nordic_image)
            self.assertEqual(arm_image, cfg.arm_image)
            self.assertEqual(product_rev, cfg.product_rev)
            self.assertEqual(hardware_rev, cfg.hardware_rev)
            self.assertEqual(banner_lines, cfg.banner_lines)

class RVMN101B_Config(unittest.TestCase):

    """RVMN101B Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = rvmn101.config.RVMN101B()
        checks = (
            ('A193000',
                cfg._nordic_088, cfg._arm_image_19, '05B', None, 4, ),
            )
        for (
                uut, nordic_image, arm_image,
                product_rev, hardware_rev, banner_lines,
                ) in checks:
            cfg.get('B', UUT(uut))
            self.assertEqual(nordic_image, cfg.nordic_image)
            self.assertEqual(arm_image, cfg.arm_image)
            self.assertEqual(product_rev, cfg.product_rev)
            self.assertEqual(hardware_rev, cfg.hardware_rev)
            self.assertEqual(banner_lines, cfg.banner_lines)
