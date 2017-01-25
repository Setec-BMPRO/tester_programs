#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Initial Test Program."""

import time
import logging
import tester
from share import oldteststep
from . import support
from . import limit

INI_LIMIT = limit.DATA


class Initial(tester.TestSequence):

    """GEN8 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.devices = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensor = None
        self.meas = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self.logdev = support.LogicalDevices(self.devices, self.fifo)
        self.sensor = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensor, self.limits)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PartDetect', self._step_part_detect),
            tester.TestStep('Program', self._step_program),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('5V', self._step_reg_5v),
            tester.TestStep('12V', self._step_reg_12v),
            tester.TestStep('24V', self._step_reg_24v),
            )
        super().open(sequence)
        # Switch on fixture power
        self.logdev.dcs_fixture.output(10.0, output=True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        # Switch off fixture power
        self.logdev.dcs_fixture.output(0.0, output=False)
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.logdev.reset()

    @oldteststep
    def _step_part_detect(self, dev, mes):
        """Measure Part detection microswitches."""
        tester.MeasureGroup(
            (mes.dmm_lock, mes.dmm_part, mes.dmm_fanshort, ), timeout=2)

    @oldteststep
    def _step_program(self, dev, mes):
        """Program the ARM device.

        5Vsb is injected to power the ARM for programming.
        Unit is left running the new code.

        """
        dev.dcs_5v.output(5.15, True)
        tester.MeasureGroup((mes.dmm_5v, mes.dmm_3v3, ), timeout=2)
        if self.fifo:
            self._logger.info(
                '**** Programming skipped due to active FIFOs ****')
        else:
            dev.programmer.program()
        # Reset micro, wait for ARM startup
        dev.rla_reset.pulse(0.1)
        time.sleep(1)

    @oldteststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        5V is already injected to power the ARM.
        The ARM is initialised via the serial port.

        Unit is left unpowered.

        """
        dev.arm.open()
        dev.arm['UNLOCK'] = True
        dev.arm['NVWRITE'] = True
        dev.dcs_5v.output(0.0, False)
        dev.loads(i5=0.1)
        time.sleep(0.5)
        dev.loads(i5=0)

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        PFC voltage is calibrated.
        12V is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (mes.dmm_acin, mes.dmm_5vset, mes.dmm_12vpri, mes.dmm_12voff,
             mes.dmm_12v2off, mes.dmm_24voff, mes.dmm_pwrfail, ), timeout=5)
        # Hold the 12V2 off
        dev.rla_12v2off.set_on()
        # A little load so 12V2 voltage falls when off
        dev.loads(i12=0.1)
        # Switch all outputs ON
        dev.rla_pson.set_on()
        tester.MeasureGroup(
            (mes.dmm_5vset, mes.dmm_12v2off, mes.dmm_24vpre, ), timeout=5)
        # Switch on the 12V2
        dev.rla_12v2off.set_off()
        mes.dmm_12v2.measure(timeout=5)
        # Unlock ARM
        dev.arm['UNLOCK'] = True
        # A little load so PFC voltage falls faster
        dev.loads(i12=1.0, i24=1.0)
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        result, _, pfc = mes.dmm_pfcpre.stable(limit.PFC_STABLE)
        dev.arm_calpfc(pfc)
        result, _, pfc = mes.dmm_pfcpost1.stable(limit.PFC_STABLE)
        if not result:      # 1st retry
            self._logger.info('Retry1 PFC calibration')
            dev.arm_calpfc(pfc)
            result, _, pfc = mes.dmm_pfcpost2.stable(limit.PFC_STABLE)
        if not result:      # 2nd retry
            self._logger.info('Retry2 PFC calibration')
            dev.arm_calpfc(pfc)
            result, _, pfc = mes.dmm_pfcpost3.stable(limit.PFC_STABLE)
        if not result:      # 3rd retry
            self._logger.info('Retry3 PFC calibration')
            dev.arm_calpfc(pfc)
            result, _, pfc = mes.dmm_pfcpost4.stable(limit.PFC_STABLE)
        # A final PFC setup check
        mes.dmm_pfcpost.stable(limit.PFC_STABLE)
        # no load for 12V calibration
        dev.loads(i12=0, i24=0)
        # Calibrate the 12V set voltage
        self._logger.info('Start 12V calibration')
        result, _, v12 = mes.dmm_12vpre.stable(limit.V12_STABLE)
        dev.arm_cal12v(v12)
        # Prevent a limit fail from failing the unit
        mes.dmm_12vset.testlimit[0].position_fail = False
        result, _, v12 = mes.dmm_12vset.stable(limit.V12_STABLE)
        # Allow a limit fail to fail the unit
        mes.dmm_12vset.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry 12V calibration')
            result, _, v12 = mes.dmm_12vpre.stable(limit.V12_STABLE)
            dev.arm_cal12v(v12)
            mes.dmm_12vset.stable(limit.V12_STABLE)
        tester.MeasureGroup(
            (mes.arm_acfreq, mes.arm_acvolt,
             mes.arm_5v, mes.arm_12v, mes.arm_24v, mes.arm_swver, mes.arm_swbld), )

    @oldteststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5V.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        dev.loads(i12=4.0, i24=0.1)
        self.reg_check(
            dmm_out=mes.dmm_5v, dcl_out=dev.dcl_5v, max_load=2.0, peak_load=2.5)
        dev.loads(i5=0, i12=0, i24=0)

    @oldteststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 4.0, Max = 22A, Peak = 24A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        (We use a parallel 12V / 12V2 load here)

        Unit is left running at no load.

        """
        dev.loads(i24=0.1)
        self.reg_check(
            dmm_out=mes.dmm_12v, dcl_out=dev.dcl_12v, max_load=22, peak_load=24)
        dev.loads(i12=0, i24=0)

    @oldteststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0.1, Max = 5A, Peak = 6A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        dev.loads(i12=4.0)
        self.reg_check(
            dmm_out=mes.dmm_24v, dcl_out=dev.dcl_24v, max_load=5.0, peak_load=6.0,
            fet=True)
        dev.loads(i12=0, i24=0)

    def reg_check(self, dmm_out, dcl_out, max_load, peak_load, fet=False):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        max_load: Maximum output load.
        peak_load: Peak output load.

        Unit is left running at peak load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName('NoLoad'):
            dcl_out.output(0.0)
            dcl_out.opc()
            dmm_out.measure()
        with tester.PathName('MaxLoad'):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
            if fet:
                self.meas.dmm_vdsfet.measure(timeout=5)
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()
