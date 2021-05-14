#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""UnitTest for RVMN101 Config module."""

import unittest

import setec

from programs import rvmn101


class RVMN101A_Config(unittest.TestCase):

    """RVMN101A Config test suite."""

    def test_rev(self):
        """Rev of units."""
        cfg = rvmn101.config.RVMN101A()
        checks = (
            ('A192800',
                cfg._nordic_2_5_3, cfg._arm_image_1_13, '06H', '06A', 5, ),
            ('A193000',
                cfg._nordic_2_5_3, cfg._arm_image_1_13, '07D', '07A', 5, ),
            ('A195000',
                cfg._nordic_2_5_3, cfg._arm_image_1_13, '08D', '08A', 5, ),
            ('A200100',
                cfg._nordic_2_5_3, cfg._arm_image_1_13, '09D', '08A', 5, ),
            )
        for (
                lotnum, nordic_image, arm_image,
                product_rev, hardware_rev, banner_lines,
                ) in checks:
            cfg.get('101A', setec.UUT.from_sernum(lotnum + '0001'))
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
                cfg._nordic_2_4_2, cfg._arm_image_3_0, '05G', '6A', 5, ),
            )
        for (
                lotnum, nordic_image, arm_image,
                product_rev, hardware_rev, banner_lines,
                ) in checks:
            cfg.get('101B', setec.UUT.from_sernum(lotnum + '0001'))
            self.assertEqual(nordic_image, cfg.nordic_image)
            self.assertEqual(arm_image, cfg.arm_image)
            self.assertEqual(product_rev, cfg.product_rev)
            self.assertEqual(hardware_rev, cfg.hardware_rev)
            self.assertEqual(banner_lines, cfg.banner_lines)
