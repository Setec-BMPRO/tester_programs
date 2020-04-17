#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""Lot Number processing.

Implement a Lot Number to product Revision Number lookup facility.

"""

import re


class Revision():

    """Lot Number to Revision Number mappings."""

    def __init__(self, data):
        """Create instance.

        @param data Tuple of (
            Tuple of (
                tester_storage.LotRange instance,
                Revision Number
                )
            )

        """
        self.data = data

    def find(self, lot):
        """Find the Revision Number of a Lot Number."""
        for lot_range, revision in self.data:
            if lot in lot_range:
                return revision
        raise LotError('Lot is not in Lot Range data')


class Range():

    """A range of Lot Numbers."""

    lot_re = re.compile('^[AS][0-9]{4}[0-9A-Z]{2}$', re.IGNORECASE)

    def __init__(self, start, end=None):
        """Create instance.

        @param start Start of Lot Number range
        @param end End of Lot Number range, or None for a single Lot range

        """
        if not self.lot_re.match(start):
            raise LotError('Invalid start Lot "{0}"'.format(start))
        if not end:     # Expand a single Lot into a range
            end = start
        if not self.lot_re.match(end):
            raise LotError('Invalid end Lot "{0}"'.format(end))
        if end < start:
            raise LotError('End Lot "{0}" before start Lot "{1}"'.format(
                    end, start))
        self.start = start
        self.end = end

    def __contains__(self, lot):
        """Support for the 'in' operator."""
        try:
            if not self.lot_re.match(lot):
                raise LotError('Invalid Lot "{0}"'.format(lot))
            return self.start <= lot and self.end >= lot
        except TypeError:
            return False


class LotError(Exception):

    """Lot not found Error."""
