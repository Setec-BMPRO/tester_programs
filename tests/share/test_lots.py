#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd.
"""UnitTest for Lots classes."""

import unittest
import share


class Range(unittest.TestCase):

    """Range test suite."""

    def test_create(self):
        """Create Range."""
        lot = 'A123456'
        myrange = share.lots.Range(lot)
        self.assertEqual(lot, myrange.start)
        self.assertEqual(lot, myrange.end)
        with self.assertRaises(share.lots.LotError):
            share.lots.Range('X123456')
        with self.assertRaises(share.lots.LotError):
            share.lots.Range('A000002', 'A000001')

    def test_in(self):
        """Range in operator."""
        start = 'A000100'
        end = 'A000200'
        myrange = share.lots.Range(start, end)
        self.assertFalse('A000099' in myrange)
        self.assertTrue('A000100' in myrange)
        self.assertTrue('A000200' in myrange)
        self.assertFalse('A000201' in myrange)
        self.assertFalse(1.234 in myrange)


class Revision(unittest.TestCase):

    """Revision test suite."""

    rev = (
        (share.lots.Range('A000100', 'A000199'), 1),
        (share.lots.Range('A000200', 'A000299'), 2),
        )

    def test_create(self):
        """Create Revision."""
        share.lots.Revision(self.rev)

    def test_find(self):
        """Revision find."""
        myrev = share.lots.Revision(self.rev)
        self.assertEqual(1, myrev.find('A000150'))
        self.assertEqual(2, myrev.find('A000250'))
        with self.assertRaises(share.lots.LotError):
            myrev.find('X123456')
