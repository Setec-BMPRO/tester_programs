#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd.
"""Tester program loader.

Reads a INI format configuration file (main.py.ini) like this:

[DEFAULT]
# Type of Tester.
TesterType = ATE4
# Program to run
Program = TRSBTS Final
# Program parameter
Parameter = SR2
# Number of units per panel
PerPanel = 1
# Unit Revision
Revision = 3
# Unit Serial Number
Sernum = A2208150001

"""

import configparser
import logging
import pathlib
import sys
import time
import traceback

from attrs import define, field, validators
import libtester
import setec
import tester
from pydispatch import dispatcher

import programs
import share


@define
class Config:
    """Configuration value loading and storage."""

    configfile = field(validator=validators.instance_of(pathlib.Path))

    @configfile.validator
    def _check_configfile(self, _, value):
        if not value.is_file():
            raise ValueError("Config file not found")

    cli_args = field(default=[], validator=validators.instance_of(list))  # unused
    _config = field(init=False, factory=configparser.ConfigParser)
    # Configuration values
    tester_type = field(init=False)
    fixture = field(init=False)
    test_program = field(init=False)
    per_panel = field(init=False)
    parameter = field(init=False)
    uut = field(init=False)
    revision = field(init=False)

    def read(self):
        """Read the config file."""
        self._config.read(self.configfile)
        section = self._config["DEFAULT"]
        self.tester_type = section.get("TesterType", "ATE3")
        fixture = section.get("Fixture")
        self.fixture = libtester.Fixture.from_barcode(fixture)
        self.test_program = section.get("Program", "Dummy")
        self.per_panel = section.getint("PerPanel", 1)
        self.parameter = section.get("Parameter", "")
        self.revision = section.get("Revision", "")
        sernum = section.get("Sernum", "A0000000001")
        self.uut = libtester.UUT.from_sernum(sernum)
        self.uut.lot.item = libtester.Item(
            number="000000", description="DummyItem", revision=self.revision
        )


@define
class Worker:
    """Test program runner worker."""

    config = field(validator=validators.instance_of(Config))
    tst = field(init=False, factory=tester.Tester)
    pgm = field(init=False)

    @pgm.default
    def _pgm_default(self):
        return tester.TestProgram(
            self.config.test_program,
            per_panel=self.config.per_panel,
            parameter=self.config.parameter,
        )

    _logger = field(init=False)

    @_logger.default
    def _logger_default(self):
        return logging.getLogger(".".join((__name__, self.__class__.__name__)))

    def _test_result(self, result):
        """Receive Test Result signals here."""
        self._logger.info('Test Result: "%s"', result.letter)
        for rdg in result.readings:
            self._logger.info(
                ' "%s", %s, %s',
                rdg.name,
                rdg.reading,
                "Pass" if rdg.is_pass else "Fail",
            )

    def open(self):
        """Open the Worker."""
        share.config.System.tester_type = self.config.tester_type
        dispatcher.connect(
            self._test_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.Status.result,
        )

    def close(self):
        """Close the Worker."""
        dispatcher.disconnect(
            self._test_result,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.Status.result,
        )

    def run(self):
        """Run the Test Program."""
        self._logger.info('Running "%s" Tester', self.config.tester_type)
        try:
            self.tst.start(self.config.tester_type, programs.PROGRAMS)
            self._logger.info('Open Program "%s"', self.config.test_program)
            uuts = [self.config.uut] * self.config.per_panel
            self.tst.open(self.pgm, self.config.fixture, uuts)
            self._logger.info("Running Test")
            self.tst.test(uuts)
        except Exception:
            self._logger.error("Test Run Exception:\n%s", traceback.format_exc())
            raise
        finally:
            self._logger.info("Open Test Fixture Now...")
            time.sleep(2)  # Allow user to open the test fixture
            self._logger.info("Close program and stop tester")
            self.tst.close()
            self.tst.stop()
            self.tst.join()


@define
class Main:
    """Application main class."""

    myname = field(init=False, default="Test Program Runner")
    _logger = field(init=False)

    @_logger.default
    def _logger_default(self):
        logsys = setec.LoggingSystem(name=self.myname)
        logsys.console(level=logging.DEBUG)
        for name, level in (  # Suppress lower level logging
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
        return logging.getLogger(".".join((__name__, self.__class__.__name__)))

    def run(self, cli_args):
        """Run the Tester.

        @param cli_args Command Line Arguments

        """
        exit_code = 1
        worker = None
        try:
            self._logger.info("Starting")
            config = Config(pathlib.Path(__file__ + ".ini"), cli_args)
            config.read()
            worker = Worker(config)
            worker.open()
            worker.run()
            exit_code = 0
        except SystemExit as exc:  # From self._parse_args()
            self._logger.debug("%s", repr(exc))
            exit_code = exc.code
        except KeyboardInterrupt:
            self._logger.debug("KeyboardInterrupt")
        except Exception:  # pylint: disable=broad-except
            self._logger.error("Exception:\n%s", traceback.format_exc())
        if worker:
            worker.close()
        self._logger.info("Exit code %s", exit_code)
        return exit_code


if __name__ == "__main__":
    sys.exit(Main().run(sys.argv))
