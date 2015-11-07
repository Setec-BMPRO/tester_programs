#!/usr/bin/env python3
"""GEN8 Initial Test Program."""

import os
import inspect
import time
import logging

import tester
import share.programmer
from share.sim_serial import SimSerial
import share.console
from . import support
from . import limit

MeasureGroup = tester.measure.group


LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'\\.\COM6',
             }[os.name]
# Software image filename
_ARM_HEX = 'gen8_1.4.645.hex'
# Reading to reading difference for PFC voltage stability
_PFC_STABLE = 0.05
# Reading to reading difference for 12V voltage stability
_12V_STABLE = 0.005

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


class Main(tester.TestSequence):

    """GEN8 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PartDetect', self._step_part_detect, None, True),
            ('Program', self._step_program, None, True),
            ('Initialise', self._step_initialise_arm, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('5V', self._step_reg_5v, None, True),
            ('12V', self._step_reg_12v, None, True),
            ('24V', self._step_reg_24v, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Serial connection to the ARM console
        arm_ser = SimSerial(simulation=fifo, baudrate=57600)
        # Set port separately, as we don't want it opened yet
        arm_ser.setPort(_ARM_PORT)
        self._armdev = share.console.ConsoleGen0(arm_ser)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits, self._armdev)
        global m
        m = support.Measurements(s, self._limits)
        # Switch on fixture power
        d.dcs_10Vfixture.output(10.0, output=True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._armdev.close()
        # Switch off fixture power
        global d
        d.dcs_10Vfixture.output(0.0, output=False)
        global m
        m = None
        d = None
        global s
        s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.acsource.output(voltage=0.0, output=False)
        d.dcl_5V.output(1.0)
        d.dcl_12V.output(5.0)
        d.dcl_24V.output(5.0)
        time.sleep(1)
        d.discharge.pulse()
        # Reset Logical Devices
        d.reset()

    def _arm_puts(self,
                  string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the Console buffer if FIFOs are enabled."""
        if self._fifo:
            self._armdev.puts(string_data, preflush, postflush, priority)

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_part_detect(self):
        """Measure Part detection microswitches."""
        self.fifo_push(
            ((s.Lock, 10.0), (s.Part, 10.0), (s.FanShort, 200.0), ))
        MeasureGroup((m.dmm_Lock, m.dmm_Part, m.dmm_FanShort, ), timeout=2)

    def _step_program(self):
        """Program the ARM device.

        5Vsb is injected to power the ARM for programming.
        Unit is left running the new code.

        """
        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Apply and check injected rails
        d.dcs_5V.output(5.15, True)
        self.fifo_push(((s.o5V, 5.05), (s.o3V3, 3.30), ))
        MeasureGroup((m.dmm_5V, m.dmm_3V3, ), timeout=2)
        # Start the ARM programmer
        self._logger.info('Start ARM programmer')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        arm = share.programmer.ProgramARM(
            _ARM_HEX, folder, s.oMirARM, _ARM_PORT, fifo=self._fifo)
        arm.read()
        m.pgmARM.measure()
        # Remove BOOT, reset micro, wait for ARM startup
        d.rla_boot.set_off()
        d.rla_reset.pulse(0.1)
        time.sleep(1)

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        5V is already injected to power the ARM.
        The ARM is initialised via the serial port.

        Unit is left unpowered.

        """
        self._armdev.open()
        self._arm_puts('\r\r\r', preflush=1)
        self._armdev.defaults()
        # Switch everything off
        d.dcs_5V.output(0.0, False)
        d.dcl_5V.output(0.1, True)
        time.sleep(0.5)
        d.dcl_5V.output(0.0)

    def _step_powerup(self):
        """Power-Up the Unit.

        240Vac is applied.
        PFC voltage is calibrated.
        12V is calibrated.
        ARM data readings are logged.
        Unit is left running at 240Vac, no load.

        """
        d.acsource.output(voltage=240.0, output=True)
        self.fifo_push(
            ((s.ACin, 240.0), (s.o5V, 5.05), (s.o12Vpri, 12.12),
             (s.o12V, 0.12), (s.o12V2, 0.12), (s.o24V, 0.24),
             (s.PWRFAIL, 0.0), ))
        MeasureGroup(
            (m.dmm_ACin, m.dmm_5Vset, m.dmm_12Vpri, m.dmm_12Voff,
             m.dmm_12V2off, m.dmm_24Voff, m.dmm_PWRFAIL, ), timeout=5)
        # Hold the 12V2 off
        d.rla_12v2off.set_on()
        # A little load so 12V2 voltage falls when off
        d.dcl_12V.output(0.1, output=True)
        # Switch all outputs ON
        d.rla_pson.set_on()
        self.fifo_push(((s.o5V, 5.11), (s.o12V2, 0.12), (s.o24V, 23.23), ))
        MeasureGroup(
            (m.dmm_5Vset, m.dmm_12V2off, m.dmm_24Vpre, ), timeout=5)
        # Switch on the 12V2
        d.rla_12v2off.set_off()
        self.fifo_push(((s.o12V2, 12.12), ))
        m.dmm_12V2.measure(timeout=5)
        # Unlock ARM
        self._arm_puts('\r\r', preflush=1)
        self._armdev.unlock()
        # A little load so PFC voltage falls faster
        d.dcl_12V.output(1.0, output=True)
        d.dcl_24V.output(1.0, output=True)
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        self.fifo_push(
            ((s.PFC,
              (432.0, 432.0,      # Initial reading
               442.0, 442.0,      # After 1st cal
               440.0, 440.0,      # 2nd reading
               440.0, 440.0,      # Final reading
               )), ))
        result, pfc = m.dmm_PFCpre.stable(_PFC_STABLE)
        self._arm_puts('\r\r', preflush=1)
        self._armdev.cal_pfc(pfc)
        # Prevent a limit fail from failing the unit
        m.dmm_PFCpost1.testlimit[0].position_fail = False
        result, pfc = m.dmm_PFCpost1.stable(_PFC_STABLE)
        # Allow a limit fail to fail the unit
        m.dmm_PFCpost1.testlimit[0].position_fail = True
        if not result:      # 1st retry
            self._logger.info('Retry1 PFC calibration')
            self._arm_puts('\r\r', preflush=1)
            self._armdev.cal_pfc(pfc)
            # Prevent a limit fail from failing the unit
            m.dmm_PFCpost2.testlimit[0].position_fail = False
            result, pfc = m.dmm_PFCpost2.stable(_PFC_STABLE)
            # Allow a limit fail to fail the unit
            m.dmm_PFCpost2.testlimit[0].position_fail = True
        if not result:      # 2nd retry
            self._logger.info('Retry2 PFC calibration')
            self._arm_puts('\r\r', preflush=1)
            self._armdev.cal_pfc(pfc)
            # Prevent a limit fail from failing the unit
            m.dmm_PFCpost3.testlimit[0].position_fail = False
            result, pfc = m.dmm_PFCpost3.stable(_PFC_STABLE)
            # Allow a limit fail to fail the unit
            m.dmm_PFCpost3.testlimit[0].position_fail = True
        if not result:      # 3rd retry
            self._logger.info('Retry3 PFC calibration')
            self._arm_puts('\r\r', preflush=1)
            self._armdev.cal_pfc(pfc)
            # Prevent a limit fail from failing the unit
            m.dmm_PFCpost4.testlimit[0].position_fail = False
            result, pfc = m.dmm_PFCpost4.stable(_PFC_STABLE)
            # Allow a limit fail to fail the unit
            m.dmm_PFCpost4.testlimit[0].position_fail = True
        # A final PFC setup check
        m.dmm_PFCpost.stable(_PFC_STABLE)
        # no load for 12V calibration
        d.dcl_12V.output(0.0)
        d.dcl_24V.output(0.0)
        # Calibrate the 12V set voltage
        self._logger.info('Start 12V calibration')
        self.fifo_push(
            ((s.o12V,
              (12.34, 12.34,     # Initial reading
               12.24, 12.24,     # After 1st cal
               12.14, 12.14,     # 2nd reading
               12.18, 12.18,     # Final reading
               )), ))
        result, v12 = m.dmm_12Vpre.stable(_12V_STABLE)
        self._arm_puts('\r\r', preflush=1)
        self._armdev.cal_12v(v12)
        # Prevent a limit fail from failing the unit
        m.dmm_12Vset.testlimit[0].position_fail = False
        result, v12 = m.dmm_12Vset.stable(_12V_STABLE)
        # Allow a limit fail to fail the unit
        m.dmm_12Vset.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry 12V calibration')
            result, v12 = m.dmm_12Vpre.stable(_12V_STABLE)
            self._arm_puts('\r\r', preflush=1)
            self._armdev.cal_12v(v12)
            m.dmm_12Vset.stable(_12V_STABLE)
        self._arm_puts(     # Console response strings
            '50 %\r'        # ARM_AcDuty
            '50000 ms\r'    # ARM_AcPer
            '50 Hz\r'       # ARM_AcFreq
            '240 Vrms\r'    # ARM_AcVolt
            '50 %\r'        # ARM_PfcTrim
            '50 %\r'        # ARM_12VTrim
            '5050 mV\r'     # ARM_5V
            '12180 mV\r'    # ARM_12V
            '24000mV\r'     # ARM_24V
            '105 Counts\r'  # ARM_5Vadc
            '112 Counts\r'  # ARM_12Vadc
            '124 Counts\r'  # ARM_24Vadc
            '1.4\r645\r')   # ARM_SwVer
        MeasureGroup(
            (m.arm_AcDuty, m.arm_AcPer, m.arm_AcFreq, m.arm_AcVolt,
             m.arm_PfcTrim, m.arm_12VTrim, m.arm_5V, m.arm_12V, m.arm_24V,
             m.arm_5Vadc, m.arm_12Vadc, m.arm_24Vadc, m.arm_SwVer), )

    def _step_reg_5v(self):
        """Check regulation of the 5V.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        self.fifo_push(((s.o5V, (5.15, 5.14, 5.10)), ))
        d.dcl_24V.output(0.1)
        d.dcl_12V.output(4.0)
        _reg_check(
            dmm_out=m.dmm_5V, dcl_out=d.dcl_5V, max_load=2.0, peak_load=2.5)
        d.dcl_5V.output(0)
        d.dcl_24V.output(0)
        d.dcl_12V.output(0)

    def _step_reg_12v(self):
        """Check regulation and OCP of the 12V.

        Min = 4.0, Max = 22A, Peak = 24A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        (We use a parallel 12V / 12V2 load here)

        Unit is left running at no load.

        """
        self.fifo_push(((s.o12V, (12.34, 12.25, 12.00)), ))
        d.dcl_24V.output(0.1)
        _reg_check(
            dmm_out=m.dmm_12V, dcl_out=d.dcl_12V, max_load=22, peak_load=24)
        d.dcl_24V.output(0)
        d.dcl_12V.output(0)

    def _step_reg_24v(self):
        """Check regulation and OCP of the 24V.

        Min = 0.1, Max = 5A, Peak = 6A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        self.fifo_push(((s.o24V, (24.33, 24.22, 24.11)), ))
        d.dcl_12V.output(4.0)
        _reg_check(
            dmm_out=m.dmm_24V, dcl_out=d.dcl_24V, max_load=5.0, peak_load=6.0)
        d.dcl_24V.output(0)
        d.dcl_12V.output(0)


def _reg_check(dmm_out, dcl_out, max_load, peak_load):
    """Check regulation of an output.

    dmm_out: Measurement instance for output voltage.
    dcl_out: DC Load instance.
    max_load: Maximum output load.
    peak_load: Peak output load.

    Unit is left running at peak load.

    """
    dmm_out.configure()
    dmm_out.opc()
    tester.testsequence.path_push('NoLoad')
    dcl_out.output(0.0)
    dcl_out.opc()
    dmm_out.measure()
    tester.testsequence.path_pop()
    tester.testsequence.path_push('MaxLoad')
    dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
    dmm_out.measure()
    tester.testsequence.path_pop()
    tester.testsequence.path_push('PeakLoad')
    dcl_out.output(peak_load)
    dcl_out.opc()
    dmm_out.measure()
    tester.testsequence.path_pop()
