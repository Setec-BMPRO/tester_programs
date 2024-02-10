#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd.
"""Tester program loader."""

import configparser
import logging
import time
import traceback

import setec
import tester
from pydispatch import dispatcher

import programs
import share


def _main():
    """Run the Tester."""
    logger = logging.getLogger(__name__)
    logger.info("Starting")
    # Suppress lower level logging
    for name, level in (
        ("gpib", logging.INFO),
        ("isplpc", logging.INFO),
        ("tester.devphysical", logging.INFO),
        ("tester.sensor.ui.Base", logging.INFO),
        ("pylink.jlink", logging.WARN),
        ("share.console.protocol.RttPort", logging.INFO),
        # updi logging when running MB3 Initial
        ("nvm", logging.WARN),
        ("app", logging.WARN),
        ("link", logging.WARN),
        ("phy", logging.WARN),
    ):
        log = logging.getLogger(name)
        log.setLevel(level)
    # Read settings from the configuration file
    config_file = __file__ + ".ini"
    logger.debug("Configuration file: %s", config_file)
    config = configparser.ConfigParser()
    config.read(config_file)
    tester_type = config["DEFAULT"].get("TesterType")
    if not tester_type:
        tester_type = "ATE3"
    test_program = config["DEFAULT"].get("Program")
    if not test_program:
        test_program = "Dummy"
    per_panel = config["DEFAULT"].get("PerPanel")
    if not per_panel:
        per_panel = 1
    per_panel = int(per_panel)
    parameter = config["DEFAULT"].get("Parameter")
    sernum = config["DEFAULT"].get("Sernum")
    if not sernum:
        sernum = "A0000000001"
    uut = setec.tester.UUT.from_sernum(sernum)
    revision = config["DEFAULT"].get("Revision")
    if not revision:
        revision = ""
    uut.lot.item = setec.tester.Item(
        number="000000", description="DummyItem", revision=revision
    )
    # Receive Test Result signals here
    def test_result(result):
        logger.info('Test Result: "%s"', result.code)
        for rdg in result.readings:
            logger.info(
                ' "%s", %s, %s',
                rdg.name,
                rdg.reading,
                "Pass" if rdg.is_pass else "Fail",
            )

    dispatcher.connect(
        test_result,
        sender=tester.signals.Thread.tester,
        signal=tester.signals.Status.result,
    )
    # Make and run the TESTER
    logger.info('Creating "%s" Tester', tester_type)
    tst = tester.Tester()
    tst.start(tester_type, programs.PROGRAMS)
    share.config.System.tester_type = tester_type
    logger.info('Create Program "%s"', test_program)
    # Make a TEST PROGRAM descriptor
    pgm = tester.TestProgram(test_program, per_panel=per_panel, parameter=parameter)
    logger.info('Open Program "%s"', test_program)
    tst.open(pgm, uut)
    logger.info("Running Test")
    try:
        tst.test((uut,) * per_panel)
    except Exception:
        exc_str = traceback.format_exc()
        logger.error("Test Run Exception:\n%s", exc_str)
    finally:
        logger.info("Close Program")
        time.sleep(2)
        tst.close()
    logger.info("Stop Tester")
    tst.stop()
    tst.join()
    logger.info("Finished")


def _logging_setup():
    """
    Setup the logging system.

    Messages are sent to the stderr console.

    """
    # create console handler and set level
    hdlr = logging.StreamHandler()
    hdlr.setLevel(logging.DEBUG)
    # Log record formatter
    fmtr = logging.Formatter(
        "%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s"
    )
    # Connect it all together
    hdlr.setFormatter(fmtr)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.DEBUG)


if __name__ == "__main__":
    _logging_setup()
    _main()
