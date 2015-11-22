#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Notify', 1, None, None, None, True),
    ('VoutNL', 0, 14.40 * 0.99, 14.40 * 1.01, None, None),
    ('Vout', 0, 14.40 * 0.95, 14.40 * 1.05, None, None),
    ('InOCP', 0, 12.0, None, None, None),
    ('OCP', 0, 14.0 - 1.0, 14.0 + 1.0, None, None),
    )
