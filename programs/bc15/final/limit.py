#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Program Limits."""

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    ('Notify', 1, None, None, None, True),
    ('VoutNL', 0, 13.85 * 0.99, 13.85 * 1.01, None, None),
    ('Vout', 0, 13.85 * 0.95, 13.85 * 1.05, None, None),
    ('InOCP', 0, 12.0, None, None, None),
    ('OCP', 0, 14.0 - 2.0, 14.0 + 2.0, None, None),
    )
