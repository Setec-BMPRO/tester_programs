#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Share."""

import logging

# Configuration of logger.
_CONSOLE_LOG_LEVEL = logging.DEBUG
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'

_SETUP = False

def logging_setup():
    """Setup the logging system.

    Messages are sent to the stderr console.

    """
    global _SETUP
    if not _SETUP:
        # create console handler and set level
        hdlr = logging.StreamHandler()
        hdlr.setLevel(_CONSOLE_LOG_LEVEL)
        # Log record formatter
        fmtr = logging.Formatter(_LOG_FORMAT)
        # Connect it all together
        hdlr.setFormatter(fmtr)
        if not logging.root.hasHandlers():
            logging.root.addHandler(hdlr)
        logging.root.setLevel(logging.DEBUG)
        _SETUP = True