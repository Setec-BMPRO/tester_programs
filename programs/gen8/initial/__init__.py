#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Initial Test Program."""

import time
import logging
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """GEN8 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
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
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices, self.fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        # Switch on fixture power
        d.dcs_fixture.output(10.0, output=True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global d, s, m
        # Switch off fixture power
        d.dcs_fixture.output(0.0, output=False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_part_detect(self):
        """Measure Part detection microswitches."""
        self.fifo_push(
            ((s.lock, 10.0), (s.part, 10.0), (s.fanshort, 200.0), ))

        tester.MeasureGroup(
            (m.dmm_lock, m.dmm_part, m.dmm_fanshort, ), timeout=2)

    def _step_program(self):
        """Program the ARM device.

        5Vsb is injected to power the ARM for programming.
        Unit is left running the new code.

        """
        self.fifo_push(((s.o5v, 5.10), (s.o3v3, 3.30), ))

        # Apply and check injected rails
        d.dcs_5v.output(5.15, True)
        tester.MeasureGroup((m.dmm_5v, m.dmm_3v3, ), timeout=2)
        if self.fifo:
            self._logger.info(
                '**** Programming skipped due to active FIFOs ****')
        else:
            d.programmer.program()
        # Reset micro, wait for ARM startup
        d.rla_reset.pulse(0.1)
        time.sleep(1)

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        5V is already injected to power the ARM.
        The ARM is initialised via the serial port.

        Unit is left unpowered.

        """
        for _ in range(2):      # Push response prompts
            d.arm_puts('')

        d.arm.open()
        d.arm['UNLOCK'] = True
        d.arm['NVWRITE'] = True
        # Switch everything off
        d.dcs_5v.output(0.0, False)
        d.loads(i5=0.1)
        time.sleep(0.5)
        d.loads(i5=0)

    def _step_powerup(self):
        """Power-Up the Unit.

        240Vac is applied.
        PFC voltage is calibrated.
        12V is calibrated.
        Unit is left running at 240Vac, no load.

        """
        self.fifo_push(
            ((s.acin, 240.0), (s.o5v, (5.05, 5.11, )), (s.o12vpri, 12.12),
             (s.o12v, 0.12), (s.o12v2, (0.12, 0.12, 12.12, )),
             (s.o24v, (0.24, 23.23, )), (s.pwrfail, 0.0), ))
        self.fifo_push(
            ((s.pfc,
              (432.0, 432.0,      # Initial reading
               442.0, 442.0,      # After 1st cal
               440.0, 440.0,      # 2nd reading
               440.0, 440.0,      # Final reading
               )), ))
        self.fifo_push(
            ((s.o12v,
              (12.34, 12.34,     # Initial reading
               12.24, 12.24,     # After 1st cal
               12.14, 12.14,     # 2nd reading
               12.18, 12.18,     # Final reading
               )), ))
        for _ in range(9):      # Push response prompts
            d.arm_puts('')
        for str in (('50Hz ', ) +       # ARM_AcFreq
                    ('240Vrms ', ) +    # ARM_AcVolt
                    ('5050mV ', ) +     # ARM_5V
                    ('12180mV ', ) +    # ARM_12V
                    ('24000mV ', )      # ARM_24V
                    ):
            d.arm_puts(str)
        d.arm_puts(limit.BIN_VERSION[:3])    # ARM SwVer
        d.arm_puts(limit.BIN_VERSION[4:])    # ARM BuildNo

        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (m.dmm_acin, m.dmm_5vset, m.dmm_12vpri, m.dmm_12voff,
             m.dmm_12v2off, m.dmm_24voff, m.dmm_pwrfail, ), timeout=5)
        # Hold the 12V2 off
        d.rla_12v2off.set_on()
        # A little load so 12V2 voltage falls when off
        d.loads(i12=0.1)
        # Switch all outputs ON
        d.rla_pson.set_on()
        tester.MeasureGroup(
            (m.dmm_5vset, m.dmm_12v2off, m.dmm_24vpre, ), timeout=5)
        # Switch on the 12V2
        d.rla_12v2off.set_off()
        m.dmm_12v2.measure(timeout=5)
        # Unlock ARM
        d.arm['UNLOCK'] = True
        # A little load so PFC voltage falls faster
        d.loads(i12=1.0, i24=1.0)
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        result, pfc = m.dmm_pfcpre.stable(limit.PFC_STABLE)
        d.arm_calpfc(pfc)
        result, pfc = m.dmm_pfcpost1.stable(limit.PFC_STABLE)
        if not result:      # 1st retry
            self._logger.info('Retry1 PFC calibration')
            d.arm_calpfc(pfc)
            result, pfc = m.dmm_pfcpost2.stable(limit.PFC_STABLE)
        if not result:      # 2nd retry
            self._logger.info('Retry2 PFC calibration')
            d.arm_calpfc(pfc)
            result, pfc = m.dmm_pfcpost3.stable(limit.PFC_STABLE)
        if not result:      # 3rd retry
            self._logger.info('Retry3 PFC calibration')
            d.arm_calpfc(pfc)
            result, pfc = m.dmm_pfcpost4.stable(limit.PFC_STABLE)
        # A final PFC setup check
        m.dmm_pfcpost.stable(limit.PFC_STABLE)
        # no load for 12V calibration
        d.loads(i12=0, i24=0)
        # Calibrate the 12V set voltage
        self._logger.info('Start 12V calibration')
        result, v12 = m.dmm_12vpre.stable(limit.V12_STABLE)
        d.arm_cal12v(v12)
        # Prevent a limit fail from failing the unit
        m.dmm_12vset.testlimit[0].position_fail = False
        result, v12 = m.dmm_12vset.stable(limit.V12_STABLE)
        # Allow a limit fail to fail the unit
        m.dmm_12vset.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry 12V calibration')
            result, v12 = m.dmm_12vpre.stable(limit.V12_STABLE)
            d.arm_cal12v(v12)
            m.dmm_12vset.stable(limit.V12_STABLE)
        tester.MeasureGroup(
            (m.arm_acfreq, m.arm_acvolt,
             m.arm_5v, m.arm_12v, m.arm_24v, m.arm_swver, m.arm_swbld), )

    def _step_reg_5v(self):
        """Check regulation of the 5V.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        self.fifo_push(((s.o5v, (5.15, 5.14, 5.10)), ))

        d.loads(i12=4.0, i24=0.1)
        _reg_check(
            dmm_out=m.dmm_5v, dcl_out=d.dcl_5v, max_load=2.0, peak_load=2.5)
        d.loads(i5=0, i12=0, i24=0)

    def _step_reg_12v(self):
        """Check regulation and OCP of the 12V.

        Min = 4.0, Max = 22A, Peak = 24A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        (We use a parallel 12V / 12V2 load here)

        Unit is left running at no load.

        """
        self.fifo_push(((s.o12v, (12.34, 12.25, 12.00)), (s.vdsfet, 0.05), ))

        d.loads(i24=0.1)
        _reg_check(
            dmm_out=m.dmm_12v, dcl_out=d.dcl_12v, max_load=22, peak_load=24)
        d.loads(i12=0, i24=0)

    def _step_reg_24v(self):
        """Check regulation and OCP of the 24V.

        Min = 0.1, Max = 5A, Peak = 6A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        self.fifo_push(((s.o24v, (24.33, 24.22, 24.11)), (s.vdsfet, 0.05), ))

        d.loads(i12=4.0)
        _reg_check(
            dmm_out=m.dmm_24v, dcl_out=d.dcl_24v, max_load=5.0, peak_load=6.0,
            fet=True)
        d.loads(i12=0, i24=0)


def _reg_check(dmm_out, dcl_out, max_load, peak_load, fet=False):
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
            m.dmm_vdsfet.measure(timeout=5)
    with tester.PathName('PeakLoad'):
        dcl_out.output(peak_load)
        dcl_out.opc()
        dmm_out.measure()
