#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Initial Test Program."""

import os
import inspect
import time
import logging

import tester
from share import SimSerial
from isplpc import Programmer, ProgrammingError
from ..console import Console
from . import support
from . import limit

MeasureGroup = tester.measure.group


INI_LIMIT = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM6'}[os.name]
# Software image filename
_ARM_BIN = 'gen8_{}.bin'.format(limit.BIN_VERSION)

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


class Initial(tester.TestSequence):

    """GEN8 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PartDetect', self._step_part_detect, None, True),
            ('Program', self._step_program, None, not fifo),
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
        arm_ser = SimSerial(simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately - don't open until after programming
        arm_ser.port = _ARM_PORT
        self._armdev = Console(arm_ser, verbose=False)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._armdev)
        m = support.Measurements(s, self._limits)
        # Switch on fixture power
        d.dcs_10Vfixture.output(10.0, output=True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        # Switch off fixture power
        global d, m, s
        d.dcs_10Vfixture.output(0.0, output=False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._armdev.close()
        d.acsource.output(voltage=0.0, output=False)
        d.dcl_5V.output(1.0)
        d.dcl_12V.output(5.0)
        d.dcl_24V.output(5.0)
        time.sleep(1)
        d.discharge.pulse()
        # Reset Logical Devices
        d.reset()

    def _arm_puts(self,
                  string_data, preflush=0, postflush=0, priority=False,
                  addprompt=True):
        """Push string data into the buffer, if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r> '
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
        MeasureGroup((m.dmm_5V, m.dmm_3V3, ), timeout=2)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        ser = SimSerial(port=_ARM_PORT, baudrate=115200)
        try:
            pgm = Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=None)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except ProgrammingError:
                s.oMirARM.store(1)
        finally:
            ser.close()
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
        for _ in range(2):      # Push response prompts
            self._arm_puts('')

        self._armdev.open()
        self._armdev['UNLOCK'] = '$DEADBEA7'
        self._armdev['NVWRITE'] = True
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
        self.fifo_push(
            ((s.ACin, 240.0), (s.o5V, (5.05, 5.11, )), (s.o12Vpri, 12.12),
             (s.o12V, 0.12), (s.o12V2, (0.12, 0.12, 12.12, )),
             (s.o24V, (0.24, 23.23, )), (s.PWRFAIL, 0.0), ))
        self.fifo_push(
            ((s.PFC,
              (432.0, 432.0,      # Initial reading
               442.0, 442.0,      # After 1st cal
               440.0, 440.0,      # 2nd reading
               440.0, 440.0,      # Final reading
               )), ))
        self.fifo_push(
            ((s.o12V,
              (12.34, 12.34,     # Initial reading
               12.24, 12.24,     # After 1st cal
               12.14, 12.14,     # 2nd reading
               12.18, 12.18,     # Final reading
               )), ))
        for _ in range(9):      # Push response prompts
            self._arm_puts('')
        for str in (('50Hz ', ) +       # ARM_AcFreq
                    ('240Vrms ', ) +    # ARM_AcVolt
                    ('5050mV ', ) +     # ARM_5V
                    ('12180mV ', ) +    # ARM_12V
                    ('24000mV ', )      # ARM_24V
                    ):
            self._arm_puts(str)
        self._arm_puts(limit.BIN_VERSION[:3])    # ARM SwVer
        self._arm_puts(limit.BIN_VERSION[4:])    # ARM BuildNo

        d.acsource.output(voltage=240.0, output=True)
        MeasureGroup(
            (m.dmm_ACin, m.dmm_5Vset, m.dmm_12Vpri, m.dmm_12Voff,
             m.dmm_12V2off, m.dmm_24Voff, m.dmm_PWRFAIL, ), timeout=5)
        # Hold the 12V2 off
        d.rla_12v2off.set_on()
        # A little load so 12V2 voltage falls when off
        d.dcl_12V.output(0.1, output=True)
        # Switch all outputs ON
        d.rla_pson.set_on()
        MeasureGroup(
            (m.dmm_5Vset, m.dmm_12V2off, m.dmm_24Vpre, ), timeout=5)
        # Switch on the 12V2
        d.rla_12v2off.set_off()
        m.dmm_12V2.measure(timeout=5)
        # Unlock ARM
        self._armdev['UNLOCK'] = '$DEADBEA7'
        # A little load so PFC voltage falls faster
        d.dcl_12V.output(1.0, output=True)
        d.dcl_24V.output(1.0, output=True)
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        result, pfc = m.dmm_PFCpre.stable(limit.PFC_STABLE)
        self._armdev['CAL_PFC'] = pfc
        self._armdev['NVWRITE'] = True
        result, pfc = m.dmm_PFCpost1.stable(limit.PFC_STABLE)
        if not result:      # 1st retry
            self._logger.info('Retry1 PFC calibration')
            self._armdev['CAL_PFC'] = pfc
            self._armdev['NVWRITE'] = True
            result, pfc = m.dmm_PFCpost2.stable(limit.PFC_STABLE)
        if not result:      # 2nd retry
            self._logger.info('Retry2 PFC calibration')
            self._armdev['CAL_PFC'] = pfc
            self._armdev['NVWRITE'] = True
            result, pfc = m.dmm_PFCpost3.stable(limit.PFC_STABLE)
        if not result:      # 3rd retry
            self._logger.info('Retry3 PFC calibration')
            self._armdev['CAL_PFC'] = pfc
            self._armdev['NVWRITE'] = True
            result, pfc = m.dmm_PFCpost4.stable(limit.PFC_STABLE)
        # A final PFC setup check
        m.dmm_PFCpost.stable(limit.PFC_STABLE)
        # no load for 12V calibration
        d.dcl_12V.output(0.0)
        d.dcl_24V.output(0.0)
        # Calibrate the 12V set voltage
        self._logger.info('Start 12V calibration')
        result, v12 = m.dmm_12Vpre.stable(limit.V12_STABLE)
        self._armdev['CAL_12V'] = v12
        self._armdev['NVWRITE'] = True
        # Prevent a limit fail from failing the unit
        m.dmm_12Vset.testlimit[0].position_fail = False
        result, v12 = m.dmm_12Vset.stable(limit.V12_STABLE)
        # Allow a limit fail to fail the unit
        m.dmm_12Vset.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry 12V calibration')
            result, v12 = m.dmm_12Vpre.stable(limit.V12_STABLE)
            self._armdev['CAL_12V'] = v12
            self._armdev['NVWRITE'] = True
            m.dmm_12Vset.stable(limit.V12_STABLE)
        MeasureGroup(
            (m.arm_AcFreq, m.arm_AcVolt,
             m.arm_5V, m.arm_12V, m.arm_24V, m.arm_SwVer, m.arm_SwBld), )

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
        self.fifo_push(((s.o12V, (12.34, 12.25, 12.00)), (s.oVdsfet, 0.05), ))

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
        self.fifo_push(((s.o24V, (24.33, 24.22, 24.11)), (s.oVdsfet, 0.05), ))

        d.dcl_12V.output(4.0)
        _reg_check(
            dmm_out=m.dmm_24V, dcl_out=d.dcl_24V, max_load=5.0, peak_load=6.0, fet=True)
        d.dcl_24V.output(0)
        d.dcl_12V.output(0)


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
    tester.testsequence.path_push('NoLoad')
    dcl_out.output(0.0)
    dcl_out.opc()
    dmm_out.measure()
    tester.testsequence.path_pop()
    tester.testsequence.path_push('MaxLoad')
    dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
    dmm_out.measure()
    if fet:
        m.dmm_Vdsfet.measure(timeout=5)
    tester.testsequence.path_pop()
    tester.testsequence.path_push('PeakLoad')
    dcl_out.output(peak_load)
    dcl_out.opc()
    dmm_out.measure()
    tester.testsequence.path_pop()
