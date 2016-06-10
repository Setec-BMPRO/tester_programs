#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Initial Test Program."""

import time
import logging

import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """SX-750 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FixtureLock', self._step_fixture_lock, None, True),
            ('Program', self._step_program_micros, None, not fifo),
            ('Initialise', self._step_initialise_arm, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('5Vsb', self._step_reg_5v, None, True),
            ('12V', self._step_reg_12v, None, True),
            ('24V', self._step_reg_24v, None, True),
            ('PeakPower', self._step_peak_power, None, True),
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
        global d, s, m, t
        d = support.LogicalDevices(self._devices, self._fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global d, s, m, t
        d = s = m = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed.

        Measure Part detection microswitches.
        Check for presence of Snubber resistors.

        """
        self.fifo_push(
            ((s.Lock, 10.1), (s.Part, 10.2), (s.R601, 2001.0),
             (s.R602, 2002.0), (s.R609, 2003.0), (s.R608, 2004.0), ))

        tester.MeasureGroup(
            (m.dmm_Lock, m.dmm_Part, m.dmm_R601, m.dmm_R602, m.dmm_R609,
             m.dmm_R608), 2)

    def _step_program_micros(self):
        """Program the ARM and PIC devices.

         5Vsb is injected to power the ARM and 5Vsb PIC. PriCtl is injected
         to power the PwrSw PIC and digital pots.
         The ARM is programmed.
         The PIC's are programmed and the digital pots are set for maximum OCP.
         Unit is left unpowered.

         """
        self.fifo_push(
            ((s.o5Vsb, 5.75), (s.o5Vsbunsw, (5.0,) * 2), (s.o3V3, 3.21),
            (s.o8V5Ard, 8.5), (s.PriCtl, 12.34),))
        for _ in range(2):      # Push response prompts
            d.ard_puts('OK')

        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Apply and check injected rails
        t.ext_pwron.run()
        d.programmer.program()  # Program the ARM device
        d.ard.open()
        time.sleep(2)        # Wait for Arduino to start
        d.rla_pic1.set_on()
        d.rla_pic1.opc()
        m.dmm_5Vunsw.measure(timeout=2)
        m.pgm_5vsb.measure()
        d.rla_pic1.set_off()
        d.rla_pic2.set_on()
        d.rla_pic2.opc()
        m.pgm_pwrsw.measure()
        d.rla_pic2.set_off()
        m.ocp_max.measure()
        # Switch off rails and discharge the 5Vsb to stop the ARM
        t.ext_pwroff.run()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        5Vsb is injected to power the ARM.
        The ARM is initialised via the serial port.
        Unit is left unpowered.

        """
        self.fifo_push(((s.o5Vsb, 5.75), (s.o5Vsbunsw, 5.01), ))
        for _ in range(2):      # Push response prompts
            d.arm_puts('')

        d.dcs_5Vsb.output(9.0, True)
        tester.MeasureGroup((m.dmm_5Vext, m.dmm_5Vunsw), 2)
        time.sleep(1)           # ARM startup delay
        d.arm.open()
        d.arm['UNLOCK'] = True
        d.arm['NVWRITE'] = True
        # Switch everything off
        d.dcs_5Vsb.output(0, False)
        d.dcl_5Vsb.output(0.1)
        time.sleep(0.5)
        d.dcl_5Vsb.output(0)

    def _step_powerup(self):
        """Power-Up the Unit.

        240Vac is applied.
        ARM data readings are logged.
        PFC voltage is calibrated.
        Unit is left running at 240Vac, no load.

        """
        self.fifo_push(
            ((s.ACin, 240.0), (s.PriCtl, 12.34), (s.o5Vsb, 5.05),
             (s.o12V, (0.12, 12.34)), (s.o24V, (0.24, 24.34)),
             (s.ACFAIL, 5.0), (s.PGOOD, 0.123),
             (s.PFC,
              (432.0, 432.0,     # Initial reading
               433.0, 433.0,     # After 1st cal
               433.0, 433.0,     # 2nd reading
               435.0, 435.0,     # Final value
               )), ))
        d.arm_puts('')
        for str in (('50Hz ', ) +       # ARM_AcFreq
                    ('240Vrms ', ) +    # ARM_AcVolt
                    ('12180mV ', ) +    # ARM_12V
                    ('24000mV ', )      # ARM_24V
                    ):
            d.arm_puts(str)
        d.arm_puts(limit.BIN_VERSION[:3])    # ARM SwVer
        d.arm_puts(limit.BIN_VERSION[4:])    # ARM BuildNo
        for _ in range(4):      # Push response prompts
            d.arm_puts('')

        d.acsource.output(voltage=240.0, output=True)
        # A little load so PFC voltage falls faster
        d.dcl_12V.output(1.0)
        d.dcl_24V.output(1.0)
        tester.MeasureGroup(
            (m.dmm_ACin, m.dmm_PriCtl, m.dmm_5Vsb_set, m.dmm_12Voff,
             m.dmm_24Voff, m.dmm_ACFAIL), 2)
        # Switch all outputs ON
        d.rla_pson.set_on()
        tester.MeasureGroup((m.dmm_12V_set, m.dmm_24V_set, m.dmm_PGOOD), 2)
        # ARM data readings
        d.arm['UNLOCK'] = True
        tester.MeasureGroup(
            (m.arm_AcFreq, m.arm_AcVolt, m.arm_12V, m.arm_24V,
             m.arm_SwVer, m.arm_SwBld), )
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        result, pfc = m.dmm_PFCpre.stable(limit.PFC_STABLE)
        d.arm_calpfc(pfc)
        # Prevent a limit fail from failing the unit
        m.dmm_PFCpost.testlimit[0].position_fail = False
        result, pfc = m.dmm_PFCpost.stable(limit.PFC_STABLE)
        # Allow a limit fail to fail the unit
        m.dmm_PFCpost.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry PFC calibration')
            result, pfc = m.dmm_PFCpre.stable(limit.PFC_STABLE)
            d.arm_calpfc(pfc)
            m.dmm_PFCpost.stable(limit.PFC_STABLE)
        # Leave the loads at zero
        d.dcl_12V.output(0)
        d.dcl_24V.output(0)

    def _step_reg_5v(self):
        """Check regulation of the 5Vsb.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        Unit is left running at no load.

        """
        self.fifo_push(((s.o5Vsb, (5.20, 5.15, 5.14, 5.10, )), ))

        _reg_check(
            dmm_out=m.dmm_5Vsb, dcl_out=d.dcl_5Vsb,
            reg_limit=self._limits['5Vsb_reg'], max_load=2.0, peak_load=2.5)
        d.dcl_5Vsb.output(0)

    def _step_reg_12v(self):
        """Check regulation and OCP of the 12V.

        Min = 0, Max = 32A, Peak = 36A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    34.0 - 38.0A
        Post adjustment range   36.2 - 36.6A
        Adjustment resolution   116mA/step
        Unit is left running at no load.

        """
        self.fifo_push(
            ((s.o12V, (12.34, 12.25, 12.10, 12.00, 12.34, )),
             # OPC SET: Push 32 reads before OCP detected
             # OCP CHECK: Push 37 reads before OCP detected
             (s.o12VinOCP, ((0.123, ) * 32 + (4.444, )) +
                           ((0.123, ) * 37 + (4.444, ))),
             ))
        # Push response prompts
        for _ in range(35):      # Push response prompts
            d.ard_puts('OK')

        _reg_check(
            dmm_out=m.dmm_12V, dcl_out=d.dcl_12V,
            reg_limit=self._limits['12V_reg'], max_load=32.0, peak_load=36.0)
        _ocp_set(
            target=36.6, load=d.dcl_12V, dmm=m.dmm_12V, detect=m.dmm_12V_inOCP,
            enable=m.ocp12_unlock, limit=self._limits['12V_ocp'])
        tester.testsequence.path_push('OCPcheck')
        d.dcl_12V.binary(0.0, 36.6 * 0.9, 2.0)
        m.rampOcp12V.measure()
        d.dcl_12V.output(1.0)
        d.dcl_12V.output(0.0)
        tester.testsequence.path_pop()

    def _step_reg_24v(self):
        """Check regulation and OCP of the 24V.

        Min = 0, Max = 15A, Peak = 18A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    17.0 - 19.0A
        Post adjustment range   18.1 - 18.3A
        Adjustment resolution   58mA/step
        Unit is left running at no load.

        """
        self.fifo_push(
            ((s.o24V, (24.44, 24.33, 24.22, 24.11, 24.24)),
             # OPC SET: Push 32 reads before OCP detected
             # OCP CHECK: Push 18 reads before OCP detected
             (s.o24VinOCP, ((0.123, ) * 32 + (4.444, )) +
                           ((0.123, ) * 18 + (4.444, ))),
             ))
        for _ in range(35):      # Push response prompts
            d.ard_puts('OK')

        _reg_check(
            dmm_out=m.dmm_24V, dcl_out=d.dcl_24V,
            reg_limit=self._limits['24V_reg'], max_load=15.0, peak_load=18.0)
        _ocp_set(
            target=18.3, load=d.dcl_24V, dmm=m.dmm_24V, detect=m.dmm_24V_inOCP,
            enable=m.ocp24_unlock, limit=self._limits['24V_ocp'])
        tester.testsequence.path_push('OCPcheck')
        d.dcl_24V.binary(0.0, 18.3 * 0.9, 2.0)
        m.rampOcp24V.measure()
        d.dcl_24V.output(1.0)
        d.dcl_24V.output(0.0)
        tester.testsequence.path_pop()

    def _step_peak_power(self):
        """Check operation at Peak load.

        5Vsb @ 2.5A, 12V @ 36.0A, 24V @ 18.0A
        Unit is left running at no load.

        """
        self.fifo_push(
            ((s.o5Vsb, 5.15), (s.o12V, 12.22), (s.o24V, 24.44),
             (s.PGOOD, 0.15)))

        d.dcl_5Vsb.binary(start=0.0, end=2.5, step=1.0)
        d.dcl_12V.binary(start=0.0, end=36.0, step=2.0)
        d.dcl_24V.binary(start=0.0, end=18.0, step=2.0)
        tester.MeasureGroup((m.dmm_5Vsb, m.dmm_12V, m.dmm_24V, m.dmm_PGOOD), 2)
        d.dcl_24V.output(0)
        d.dcl_12V.output(0)
        d.dcl_5Vsb.output(0)


def _reg_check(dmm_out, dcl_out, reg_limit, max_load, peak_load):
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
    tester.testsequence.path_push('NoLoad')
    dcl_out.output(0.0)
    dcl_out.opc()
    volt00 = dmm_out.measure().reading1
    tester.testsequence.path_pop()
    tester.testsequence.path_push('MaxLoad')
    dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
    dmm_out.measure()
    tester.testsequence.path_pop()
    tester.testsequence.path_push('LoadReg')
    dcl_out.output(peak_load * 0.95)
    dcl_out.opc()
    volt = dmm_out.measure().reading1
    load_reg = 100.0 * (volt00 - volt) / volt00
    reg_limit.check(load_reg, 1)
    tester.testsequence.path_pop()
    tester.testsequence.path_push('PeakLoad')
    dcl_out.output(peak_load)
    dcl_out.opc()
    dmm_out.measure()
    tester.testsequence.path_pop()

def _ocp_set(target, load, dmm, detect, enable, limit):
    """Set OCP of an output.

    target: Target setpoint in Amp.
    load: Load instrument.
    dmm: Measurement of output voltage.
    detect: Measurement of 'In OCP'.
    enable: Measurement to call to enable digital pot.
    limit: Limit to check OCP pot setting.

    OCP has been set to maximum in the programming step. Apply the desired load
    current, then lower the OCP setting until OCP triggers.
    The unit is left running at no load.

    """
    tester.testsequence.path_push('OCPset')
    load.output(target)
    dmm.measure()
    detect.configure()
    detect.opc()
    enable.measure()
    setting = 0
    for setting in range(63, 0, -1):
        m.ocp_step_dn.measure()
        if detect.measure().result:
            break
    m.ocp_lock.measure()
    load.output(0.0)
    limit.check(setting, 1)
    tester.testsequence.path_pop()
