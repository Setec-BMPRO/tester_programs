#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""SX-750 Initial Test Program."""

import time
import logging
import tester
from share import oldteststep
from . import support
from . import limit

INI_LIMIT = limit.DATA


class Initial(tester.TestSequence):

    """SX-750 Initial Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        sequence = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('Program', self._step_program_micros),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('5Vsb', self._step_reg_5v),
            tester.TestStep('12V', self._step_reg_12v),
            tester.TestStep('24V', self._step_reg_24v),
            tester.TestStep('PeakPower', self._step_peak_power),
            )
        super().__init__(per_panel, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.devices = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensor = None
        self.meas = None
        self.subt = None

    def open(self, sequence=None):
        """Prepare for testing."""
        self._logger.info('Open')
        super().open()
        self.logdev = support.LogicalDevices(self.devices, self.fifo)
        self.sensor = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensor, self.limits)
        self.subt = support.SubTests(self.logdev, self.meas)
        self.logdev.dcs_Vcom.output(9.0, output=True)
        self.logdev.dcs_Arduino.output(12.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self.logdev.dcs_Arduino.output(0.0, output=False)
        self.logdev.dcs_Vcom.output(0.0, output=False)
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.logdev.reset()

    @oldteststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed.

        Measure Part detection microswitches.
        Check for presence of Snubber resistors.

        """
        tester.MeasureGroup(
            (mes.dmm_Lock, mes.dmm_Part, mes.dmm_R601, mes.dmm_R602,
             mes.dmm_R609, mes.dmm_R608),
            timeout=2)

    @oldteststep
    def _step_program_micros(self, dev, mes):
        """Program the ARM and PIC devices.

        5Vsb is injected to power the ARM and 5Vsb PIC. PriCtl is injected
        to power the PwrSw PIC and digital pots.
        The ARM is programmed.
        The PIC's are programmed and the digital pots are set for maximum OCP.
        Unit is left unpowered.

        """
        # Set BOOT active before power-on so the ARM boot-loader runs
        dev.rla_boot.set_on()
        # Apply and check injected rails
        self.subt.ext_pwron.run()
        if self.fifo:
            self._logger.info(
                '**** Programming skipped due to active FIFOs ****')
        else:
            dev.programmer.program()  # Program the ARM device
        dev.ard.open()
        time.sleep(2)        # Wait for Arduino to start
        dev.rla_pic1.set_on()
        dev.rla_pic1.opc()
        mes.dmm_5Vunsw.measure(timeout=2)
        mes.pgm_5vsb.measure()
        dev.rla_pic1.set_off()
        dev.rla_pic2.set_on()
        dev.rla_pic2.opc()
        mes.pgm_pwrsw.measure()
        dev.rla_pic2.set_off()
        mes.ocp_max.measure()
        # Switch off rails and discharge the 5Vsb to stop the ARM
        self.subt.ext_pwroff.run()

    @oldteststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        5Vsb is injected to power the ARM.
        The ARM is initialised via the serial port.
        Unit is left unpowered.

        """
        dev.arm.open()
        dev.dcs_5Vsb.output(9.0, True)
        tester.MeasureGroup((mes.dmm_5Vext, mes.dmm_5Vunsw), 2)
        time.sleep(1)           # ARM startup delay
        dev.arm['UNLOCK'] = True
        dev.arm['NVWRITE'] = True
        # Switch everything off
        dev.dcs_5Vsb.output(0, False)
        dev.dcl_5Vsb.output(0.1)
        time.sleep(0.5)
        dev.dcl_5Vsb.output(0)

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        ARM data readings are logged.
        PFC voltage is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev.acsource.output(voltage=240.0, output=True)
        # A little load so PFC voltage falls faster
        dev.dcl_12V.output(1.0)
        dev.dcl_24V.output(1.0)
        tester.MeasureGroup(
            (mes.dmm_ACin, mes.dmm_PriCtl, mes.dmm_5Vsb_set, mes.dmm_12Voff,
             mes.dmm_24Voff, mes.dmm_ACFAIL), 2)
        # Switch all outputs ON
        dev.rla_pson.set_on()
        tester.MeasureGroup(
            (mes.dmm_12V_set, mes.dmm_24V_set, mes.dmm_PGOOD), 2)
        # ARM data readings
        dev.arm['UNLOCK'] = True
        tester.MeasureGroup(
            (mes.arm_AcFreq, mes.arm_AcVolt, mes.arm_12V, mes.arm_24V,
             mes.arm_SwVer, mes.arm_SwBld), )
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        result, _, pfc = mes.dmm_PFCpre.stable(limit.PFC_STABLE)
        dev.arm_calpfc(pfc)
        # Prevent a limit fail from failing the unit
        mes.dmm_PFCpost.testlimit[0].position_fail = False
        result, _, pfc = mes.dmm_PFCpost.stable(limit.PFC_STABLE)
        # Allow a limit fail to fail the unit
        mes.dmm_PFCpost.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry PFC calibration')
            result, _, pfc = mes.dmm_PFCpre.stable(limit.PFC_STABLE)
            dev.arm_calpfc(pfc)
            mes.dmm_PFCpost.stable(limit.PFC_STABLE)
        # Leave the loads at zero
        dev.dcl_12V.output(0)
        dev.dcl_24V.output(0)

    @oldteststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5Vsb.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes.dmm_5Vsb, dcl_out=dev.dcl_5Vsb,
            reg_limit=self.limits['5Vsb_reg'], max_load=2.0, peak_load=2.5)
        dev.dcl_5Vsb.output(0)

    @oldteststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 0, Max = 32A, Peak = 36A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    34.0 - 38.0A
        Post adjustment range   36.2 - 36.6A
        Adjustment resolution   116mA/step
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes.dmm_12V, dcl_out=dev.dcl_12V,
            reg_limit=self.limits['12V_reg'], max_load=32.0, peak_load=36.0)
        self.ocp_set(
            target=36.6, load=dev.dcl_12V,
            dmm=mes.dmm_12V, detect=mes.dmm_12V_inOCP,
            enable=mes.ocp12_unlock, olimit=self.limits['12V_ocp'])
        with tester.PathName('OCPcheck'):
            dev.dcl_12V.binary(0.0, 36.6 * 0.9, 2.0)
            mes.rampOcp12V.measure()
            dev.dcl_12V.output(1.0)
            dev.dcl_12V.output(0.0)

    @oldteststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0, Max = 15A, Peak = 18A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    17.0 - 19.0A
        Post adjustment range   18.1 - 18.3A
        Adjustment resolution   58mA/step
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes.dmm_24V, dcl_out=dev.dcl_24V,
            reg_limit=self.limits['24V_reg'], max_load=15.0, peak_load=18.0)
        self.ocp_set(
            target=18.3, load=dev.dcl_24V,
            dmm=mes.dmm_24V, detect=mes.dmm_24V_inOCP,
            enable=mes.ocp24_unlock, olimit=self.limits['24V_ocp'])
        with tester.PathName('OCPcheck'):
            dev.dcl_24V.binary(0.0, 18.3 * 0.9, 2.0)
            mes.rampOcp24V.measure()
            dev.dcl_24V.output(1.0)
            dev.dcl_24V.output(0.0)

    @oldteststep
    def _step_peak_power(self, dev, mes):
        """Check operation at Peak load.

        5Vsb @ 2.5A, 12V @ 36.0A, 24V @ 18.0A
        Unit is left running at no load.

        """
        dev.dcl_5Vsb.binary(start=0.0, end=2.5, step=1.0)
        dev.dcl_12V.binary(start=0.0, end=36.0, step=2.0)
        dev.dcl_24V.binary(start=0.0, end=18.0, step=2.0)
        tester.MeasureGroup(
            (mes.dmm_5Vsb, mes.dmm_12V, mes.dmm_24V, mes.dmm_PGOOD), 2)
        dev.dcl_24V.output(0)
        dev.dcl_12V.output(0)
        dev.dcl_5Vsb.output(0)

    def ocp_set(self, target, load, dmm, detect, enable, olimit):
        """Set OCP of an output.

        target: Target setpoint in Amp.
        load: Load instrument.
        dmm: Measurement of output voltage.
        detect: Measurement of 'In OCP'.
        enable: Measurement to call to enable digital pot.
        olimit: Limit to check OCP pot setting.

        OCP has been set to maximum in the programming step.
        Apply the desired load current, then lower the OCP setting until
        OCP triggers. The unit is left running at no load.

        """
        with tester.PathName('OCPset'):
            load.output(target)
            dmm.measure()
            detect.configure()
            detect.opc()
            enable.measure()
            setting = 0
            for setting in range(63, 0, -1):
                self.meas.ocp_step_dn.measure()
                if detect.measure().result:
                    break
            self.meas.ocp_lock.measure()
            load.output(0.0)
            olimit.check(setting, 1)

    @staticmethod
    def reg_check(dmm_out, dcl_out, reg_limit, max_load, peak_load):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        reg_limit: TestLimit for Load Regulation.
        max_load: Maximum output load.
        peak_load: Peak output load.
        Unit is left running at peak load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName('NoLoad'):
            dcl_out.output(0.0)
            dcl_out.opc()
            volt00 = dmm_out.measure().reading1
        with tester.PathName('MaxLoad'):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
        with tester.PathName('LoadReg'):
            dcl_out.output(peak_load * 0.95)
            dcl_out.opc()
            volt = dmm_out.measure().reading1
            load_reg = 100.0 * (volt00 - volt) / volt00
            reg_limit.check(load_reg, 1)
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()
