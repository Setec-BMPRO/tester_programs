#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test suite definition for Eric6 Unittest plugin."""

import unittest


def suite():
    """Define the test suite by discovering all test files."""
    testsuite = unittest.defaultTestLoader.discover(
        start_dir='.', pattern='test_*.py')
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    testsuite = suite()
    runner.run(testsuite)
