#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd.
"""Unittests."""

# import unittest
import logging

_LOG_LEVEL = logging.DEBUG
_LOG_FORMAT = "%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s"
_LOG_SETUP = False


def logging_setup():
    """Setup the logging system.

    Messages are sent to the stderr console.

    """
    global _LOG_SETUP
    if not _LOG_SETUP:
        # create console handler and set level
        hdlr = logging.StreamHandler()
        hdlr.setLevel(_LOG_LEVEL)
        # Log record formatter
        fmtr = logging.Formatter(_LOG_FORMAT)
        # Connect it all together
        hdlr.setFormatter(fmtr)
        if not logging.root.hasHandlers():
            logging.root.addHandler(hdlr)
        logging.root.setLevel(logging.DEBUG)
        _LOG_SETUP = True


# Imported here so that logging_setup already exists in the namespace
from . import share
from . import programs
