#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test suite definition for Eric6 Unittest plugin."""

import unittest

# This is the overall project top level folder
_TOP_LEVEL_DIR = None
# Discover test files in this relative path
_START_DIR = 'share'

# Test files must match this pattern
_TEST_PATTERN = 'test_*.py'


def suite():
    """Define the test suite by discovering all test files."""
    testsuite = unittest.defaultTestLoader.discover(
        top_level_dir=_TOP_LEVEL_DIR,
        start_dir=_START_DIR,
        pattern=_TEST_PATTERN
        )
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    testsuite = suite()
    runner.run(testsuite)
