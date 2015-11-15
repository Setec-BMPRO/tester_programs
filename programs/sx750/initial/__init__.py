#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Initial Test Program."""

import os
import inspect
import time
import logging
import threading

import tester
from ...share.programmer import ProgramPIC
from ...share.sim_serial import SimSerial
from ...share.isplpc import Programmer, ProgrammingError
from ...share.console import ConsoleGen0
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Software image filenames
_ARM_BIN = 'sx750_arm_3.1.2118.bin'
_PIC_HEX = 'sx750_pic_2.hex'
# Reading to reading difference for PFC voltage stability
_PFC_STABLE = 0.05

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


class Main(tester.TestSequence):

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
            ('AC', self._step_acstart, None, True),
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
        self._armdev = ConsoleGen0(arm_ser)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._armdev)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._armdev.close()
        d.acsource.output(voltage=0.0, output=False)
        d.dcl_5Vsb.output(1.0)
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

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed.

        Measure Part detection microswitches.
        Check for presence of Snubber resistors.

        """
        self.fifo_push(
            ((s.Lock, 10.0), (s.Part, 10.0), (s.R601, 2000.0),
             (s.R602, 2000.0), (s.R609, 2000.0), (s.R608, 2000.0), ))
        MeasureGroup(
            (m.dmm_Lock, m.dmm_Part, m.dmm_R601, m.dmm_R602, m.dmm_R609,
             m.dmm_R608), 2)

    def _step_program_micros(self):
        """Program the ARM and PIC devices.

        5Vsb is injected to power the ARM for programming.
        PriCtl is injected to power the PIC for programming.
        Both devices are programmed at the same time using 2 new threads.
        While waiting, we set OCP digital pots to maximum.

        Unit is left unpowered.

        """
        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Apply and check injected rails
        d.dcs_5Vsb.output(5.15, True)
        d.dcs_PriCtl.output(12.0, True)
        self.fifo_push(((s.PriCtl, 12.34), (s.o5Vsb, 5.05), (s.o3V3, 3.21), ))
        MeasureGroup((m.dmm_PriCtl, m.dmm_5Vsb, m.dmm_3V3), 2)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # Start the PIC programmer (takes about 6 sec)
        self._logger.info('Start PIC programmer')
        d.rla_pic.set_on()
        pic = ProgramPIC(_PIC_HEX, folder, '10F320', s.oMirPIC)
        # While programming, we also set OCP adjust to maximum.
        # (takes about 6 sec)
        self._logger.info('Reset digital pots')
        pot_worker = threading.Thread(
            target=self._pot_worker, name='PotReset')
        pot_worker.start()
        self._logger.info('Program ARM')
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        try:
            ser = SimSerial(port=_ARM_PORT, baudrate=115200)
            pgm = Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=None)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except ProgrammingError:
                s.oMirARM.store(1)
        finally:
            ser.close()
        # Wait for programming completion & read results
        pot_worker.join()
        pic.read()
        d.rla_pic.set_off()
        # 'Measure' the mirror sensors to check and log data
        MeasureGroup((m.pgmARM, m.pgmPIC))
        # Reset BOOT to ARM
        d.rla_boot.set_off()
        # Discharge the 5Vsb to stop the ARM
        d.dcs_5Vsb.output(0, False)
        d.dcl_5Vsb.output(0.1)
        time.sleep(0.5)
        d.dcl_5Vsb.output(0)
        d.dcs_PriCtl.output(0, False)

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        5Vsb is injected to power the ARM.
        The ARM is initialised via the serial port.

        Unit is left unpowered.

        """
        d.dcs_5Vsb.output(5.15, True)
        time.sleep(1)           # ARM startup delay
        self._armdev.open()
        self._arm_puts('\r\r\r', preflush=1)
        self._armdev.defaults()
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
        d.acsource.output(voltage=240.0, output=True)
        # A little load so PFC voltage falls faster
        d.dcl_12V.output(1.0)
        d.dcl_24V.output(1.0)
        self.fifo_push(((s.ACin, 240.0), (s.PriCtl, 12.34), (s.o5Vsb, 5.05),
                        (s.o12V, 0.12), (s.o24V, 0.24), (s.ACFAIL, 5.0), ))
        MeasureGroup((m.dmm_ACin, m.dmm_PriCtl, m.dmm_5Vsb_set,
                      m.dmm_12Voff, m.dmm_24Voff, m.dmm_ACFAIL),
                     2)
        # Switch all outputs ON
        d.rla_pson.set_on()
        self.fifo_push(((s.o12V, 12.34), (s.o24V, 24.34), (s.PGOOD, 0.123), ))
        MeasureGroup((m.dmm_12V_set, m.dmm_24V_set, m.dmm_PGOOD), 2)
        # ARM data readings
        self._arm_puts('\r\r', preflush=1)
        self._armdev.unlock()
        self._arm_puts(     # Console response strings
            '50 %\r'        # ARM_AcDuty
            '50000 ms\r'    # ARM_AcPer
            '50 Hz\r'       # ARM_AcFreq
            '240 Vrms\r'    # ARM_AcVolt
            '50 %\r'        # ARM_PfcTrim
            '12180 mV\r'    # ARM_12V
            '24000 mV\r'    # ARM_24V
            '3.1\r2118\r')  # ARM_SwVer
        MeasureGroup(
            (m.arm_AcDuty, m.arm_AcPer, m.arm_AcFreq, m.arm_AcVolt,
             m.arm_PfcTrim, m.arm_12V, m.arm_24V, m.arm_SwVer), )
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        self.fifo_push(
            ((s.PFC,
              (432.0, 432.0,     # Initial reading
               433.0, 433.0,     # After 1st cal
               433.0, 433.0,     # 2nd reading
               435.0, 435.0,     # Final value
               )), ))
        result, pfc = m.dmm_PFCpre.stable(_PFC_STABLE)
        self._arm_puts('\r\r', preflush=1)
        self._armdev.cal_pfc(pfc)
        # Prevent a limit fail from failing the unit
        m.dmm_PFCpost.testlimit[0].position_fail = False
        result, pfc = m.dmm_PFCpost.stable(_PFC_STABLE)
        # Allow a limit fail to fail the unit
        m.dmm_PFCpost.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry PFC calibration')
            result, pfc = m.dmm_PFCpre.stable(_PFC_STABLE)
            self._arm_puts('\r\r', preflush=1)
            self._armdev.cal_pfc(pfc)
            m.dmm_PFCpost.stable(_PFC_STABLE)
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
        self.fifo_push(((s.o5Vsb, (5.20, 5.15, 5.14, 5.10)), ))
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
        self.fifo_push(((s.o12V, (12.34, 12.25, 12.10, 12.00)), ))
        _reg_check(
            dmm_out=m.dmm_12V, dcl_out=d.dcl_12V,
            reg_limit=self._limits['12V_reg'], max_load=32.0, peak_load=36.0)
        self.fifo_push(
            ((s.o12V, 12.34, ),
             # OPC SET: Push 32 reads before OCP detected
             (s.o12VinOCP, ((0.123, ) * 32 + (4.444, ))),
             # OCP CHECK: Push 37 reads before OCP detected
             (s.o12VinOCP, ((0.123, ) * 37 + (4.444, ))),
             ))
        _ocp_set(
            target=36.6, load=d.dcl_12V, dmm=m.dmm_12V, detect=m.dmm_12V_inOCP,
            enable=d.ocp_pot.enable_12v, limit=self._limits['12V_ocp'])
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
        self.fifo_push(((s.o24V, (24.44, 24.33, 24.22, 24.11)), ))
        _reg_check(
            dmm_out=m.dmm_24V, dcl_out=d.dcl_24V,
            reg_limit=self._limits['24V_reg'], max_load=15.0, peak_load=18.0)
        self.fifo_push(
            ((s.o24V, 24.24),
             # OPC SET: Push 32 reads before OCP detected
             (s.o24VinOCP, ((0.123, ) * 32 + (4.444, ))),
             # OCP CHECK: Push 18 reads before OCP detected
             (s.o24VinOCP, ((0.123, ) * 18 + (4.444, ))),
             ))
        _ocp_set(
            target=18.3, load=d.dcl_24V, dmm=m.dmm_24V, detect=m.dmm_24V_inOCP,
            enable=d.ocp_pot.enable_24v, limit=self._limits['24V_ocp'])
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
        d.dcl_5Vsb.binary(0.0, 2.5, 1.0)
        d.dcl_12V.binary(0.0, 36.0, 2.0)
        d.dcl_24V.binary(0.0, 18.0, 2.0)
        self.fifo_push(
            ((s.o5Vsb, 5.15), (s.o12V, 12.22), (s.o24V, 24.44),
             (s.PGOOD, 0.15)))
        MeasureGroup((m.dmm_5Vsb, m.dmm_12V, m.dmm_24V, m.dmm_PGOOD), 2)
        d.dcl_24V.output(0)
        d.dcl_12V.output(0)
        d.dcl_5Vsb.output(0)

    def _step_acstart(self):
        """Measure AC Start / Stop voltages."""
        # A little load so PFC voltage falls faster
        d.dcl_5Vsb.output(0.05)
        d.dcl_12V.output(1.0)
        d.dcl_24V.output(1.0)
        # Switch off the unit
        d.acsource.output(75.0)
        self.fifo_push(((s.ACFAIL, 0.123), (s.o5Vsb, 0.055),
                        (s.ACFAIL, (0.123, ) * 25 + (4.99, ))))
        m.dmm_ACOK.measure(2)
        # 5Vsb should have switched off
        m.dmm_5Voff.measure(1.0)
        m.rampAcStart.measure()
        d.acsource.output(95.0)
        if not self._fifo:
            time.sleep(1)
        self.fifo_push(((s.ACFAIL, (5.01, ) * 30 + (0.123, )), ))
        m.rampAcStop.measure()

    def _pot_worker(self):
        """Thread worker to set the digital pots to maximum."""
        d.ocp_pot.set_maximum()


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
    volt00 = dmm_out.read()[0]
    dmm_out.testlimit[0].check(volt00, 1)
    tester.testsequence.path_pop()
    tester.testsequence.path_push('MaxLoad')
    dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
    volt = dmm_out.read()[0]
    dmm_out.testlimit[0].check(volt, 1)
    tester.testsequence.path_pop()
    tester.testsequence.path_push('LoadReg')
    dcl_out.output(peak_load * 0.95)
    dcl_out.opc()
    volt = dmm_out.read()[0]
    dmm_out.testlimit[0].check(volt, 1)
    load_reg = 100.0 * (volt00 - volt) / volt00
    reg_limit.check(load_reg, 1)
    tester.testsequence.path_pop()
    tester.testsequence.path_push('PeakLoad')
    dcl_out.output(peak_load)
    dcl_out.opc()
    volt = dmm_out.read()[0]
    dmm_out.testlimit[0].check(volt, 1)
    tester.testsequence.path_pop()


def _ocp_set(target, load, dmm, detect, enable, limit):
    """Set OCP of an output.

    target: Target setpoint in Amp.
    load: Load instrument.
    dmm: Measurement of output voltage.
    detect: Measurement of 'In OCP'.
    enable: Method to call to enable digital pot.
    limit: Limit to check OCP pot setting.

    Adjust OCP by setting the desired current, then lowering the digital pot
    setting until OCP triggers.
    Unit is left running at no load.

    """
    tester.testsequence.path_push('OCP')
    load.output(target)
    volt = dmm.read()[0]
    dmm.testlimit[0].check(volt, 1)
    detect.configure()
    detect.opc()
    enable()
    setting = 0
    for setting in range(63, 0, -1):
        d.ocp_pot.step()
        if detect.testlimit[0] == detect.read()[0]:
            break
    d.ocp_pot.disable()
    load.output(0.0)
    limit.check(setting, 1)
    tester.testsequence.path_pop()
