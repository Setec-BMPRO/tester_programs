#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""Test suite definition for Eric Unittest plugin."""

import unittest


def suite():
    """Define the test suite for Eric unittest tool.

    @return unittest.testsuite

    """
    return unittest.defaultTestLoader.discover(
        start_dir='.', pattern='test_*.py')


def _main():
    """Run the testsuite."""
    runner = unittest.TextTestRunner()
    testsuite = suite()
    runner.run(testsuite)


if __name__ == '__main__':
    _main()
