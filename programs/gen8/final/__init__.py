#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Final Test Program."""

import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA


class Final(tester.TestSequence):

    """GEN8 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.teststep = None

    def open(self, sequence=None):
        """Prepare for testing."""
        self._logger.info('Open')
        self.logdev = support.LogicalDevices(self._devices)
        self.sensors = support.Sensors(self.logdev)
        self.meas = support.Measurements(self.sensors, self._limits)
        self.teststep = SubTests(self.logdev, self.meas)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self.teststep.pwr_up),
            tester.TestStep('PowerOn', self.teststep.pwr_on),
            tester.TestStep('FullLoad', self.teststep.full_load),
            tester.TestStep('115V', self.teststep.full_load_115),
            tester.TestStep('Poweroff', self.teststep.pwr_off),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.logdev.reset()


class SubTests():

    """SubTest Steps."""

    def __init__(self, dev, mes):
        """Create SubTest Step instances."""
        # PowerUp: Apply 240Vac, set min load, measure.
        self.pwr_up = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_5V, 0.0), (dev.dcl_24V, 0.1), (dev.dcl_12V, 3.5),
                 (dev.dcl_12V2, 0.5)), output=True),
            tester.AcSubStep(
                acs=dev.acsource, voltage=240.0, output=True, delay=1.0),
            tester.MeasureSubStep(
                (mes.dmm_5V, mes.dmm_24Voff, mes.dmm_12Voff, ), timeout=5),
            tester.RelaySubStep(((dev.rla_12V2off, True), )),
            tester.MeasureSubStep((mes.dmm_12V2off, ), timeout=5),
            ))
        # PowerOn: Turn on, measure at min loadev.
        self.pwr_on = tester.SubStep((
            tester.RelaySubStep(((dev.rla_pson, True), )),
            tester.MeasureSubStep(
                (mes.dmm_24Von, mes.dmm_12Von, mes.dmm_12V2off,
                 mes.dmm_PwrFailOff, ), timeout=5),
            tester.RelaySubStep(((dev.rla_12V2off, False), )),
            tester.MeasureSubStep(
                (mes.dmm_12V2on, mes.dmm_Iecon, ), timeout=5),
            tester.MeasureSubStep((mes.ui_YesNoMains, )),
            ))
        # Full Load: Apply full load, measure.
        # 115Vac Full Load: 115Vac, measure.
        mss = tester.MeasureSubStep(
            (mes.dmm_5V, mes.dmm_24Von, mes.dmm_12Von, mes.dmm_12V2on,),
            timeout=5)
        self.full_load = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_5V, 2.5), (dev.dcl_24V, 5.0),
                 (dev.dcl_12V, 15.0), (dev.dcl_12V2, 7.0)), delay=0.5),
            mss,
            ))
        self.full_load_115 = tester.SubStep((
            tester.AcSubStep(acs=dev.acsource, voltage=115.0, delay=0.5),
            mss,
            ))
        # PowerOff: Set min load, switch off, measure.
        self.pwr_off = tester.SubStep((
            tester.LoadSubStep(
                ((dev.dcl_5V, 0.5), (dev.dcl_24V, 0.5), (dev.dcl_12V, 4.0))),
            tester.MeasureSubStep(
                (mes.ui_NotifyPwrOff, mes.dmm_Iecoff, mes.dmm_24Voff,)),
            ))
