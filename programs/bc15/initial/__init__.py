#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Initial Test Program."""

import logging
import time

import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """BC15 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PartDetect', self._step_part_detect, None, True),
            ('ProgramARM', self._step_program_arm, None, not fifo),
            ('Initialise', self._step_initialise_arm, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('Output', self._step_output, None, True),
            ('Loaded', self._step_loaded, None, True),
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
        d = support.LogicalDevices(self._devices, self._fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        # Apply power to fixture Comms circuit.
        d.dcs_vcom.output(12.0, True)
        time.sleep(2)       # Allow OS to detect USB serial port

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        # Remove power from fixture circuit.
        d.dcs_vcom.output(0, False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _bc15_putstartup(self, put_defaults):
        """Push startup banner strings into fake serial port."""
        d.bc15_puts(
            'BC15\r\n'                          # BEGIN Startup messages
            'Build date:       06/11/2015\r\n'
            'Build time:       15:31:40\r\n'
            'SystemCoreClock:  48000000\r\n'
            'Software version: 1.2.3.456\r\n'
            'nonvol: reading crc invalid at sector 14 offset 0\r\n'
            'nonvol: reading nonvol2 OK at sector 15 offset 2304\r\n'
            'Hardware version: 0.0.[00]\r\n'
            'Serial number:    A9999999999\r\n'
            'Please type help command.'         # END Startup messages
            )
        if put_defaults:
            for str in (
                ('OK', ) * 3 +
                ('{}'.format(limit.BIN_VERSION), )
                ):
                d.bc15_puts(str)

    def _step_part_detect(self):
        """Measure fixture lock and part detection microswitches."""
        self.fifo_push(((s.olock, 0.0), (s.ofanshort, 3300.0), ))

        tester.MeasureGroup((m.dmm_lock, m.dmm_fanshort, ), timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        3V3 is injected to power the ARM for programming.

        """
        d.dcs_3v3.output(9.0, True)
        self.fifo_push(((s.o3V3, 3.3), ))
        m.dmm_3V3.measure(timeout=5)
        time.sleep(2)
        d.rla_boot.set_on()
        time.sleep(1)
        d.rla_reset.pulse(0.1)
        d.programmer.program()
        d.rla_boot.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected voltage.
        Write Non-Volatile memory defaults.
        Switch off the injected voltage.

        """
        self._bc15_putstartup(True)

        d.dcs_3v3.output(9.0, True)
        d.rla_reset.pulse(0.1)
        time.sleep(0.5)
        d.bc15.open()
        d.bc15.action(None, delay=1.5, expected=10)  # Flush banner
        d.bc15['UNLOCK'] = True
        d.bc15['NVDEFAULT'] = True
        d.bc15['NVWRITE'] = True
        m.arm_SwVer.measure()
        d.bc15.close()
        d.dcs_3v3.output(0.0, False)

    def _step_powerup(self):
        """Power up the Unit.

        Power up with 240Vac.
        Go into Power Supply mode.

        """
        self.fifo_push(
            ((s.oACin, 240.0), (s.oVbus, 330.0), (s.o12Vs, 12.0),
             (s.o3V3, 3.3), (s.o15Vs, 15.0), (s.oVout, 0.2), ))
        self._bc15_putstartup(False)
        for str in (('', ) * 10):
            d.bc15_puts(str)

        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (m.dmm_acin, m.dmm_vbus, m.dmm_12Vs, m.dmm_3V3,
             m.dmm_15Vs, m.dmm_voutoff, ), timeout=5)
        d.bc15.open()
        d.bc15.action(None, delay=1.5, expected=10)  # Flush banner
        d.bc15.ps_mode()
# FIXME: Save the "Power Supply" mode state in the unit (new command required)

    def _step_output(self):
        """Tests of the output.

        Check the accuracy of the current sensor.

        """
        self.fifo_push(((s.oVout, 14.40), ))
        d.bc15_puts(
            'not-pulsing-volts=14432 ;mV \r\nnot-pulsing-current=1987 ;mA ')
        d.bc15_puts('3')
        d.bc15_puts('mv-set=14400 ;mV \r\nnot-pulsing-volts=14432 ;mV ')
        d.bc15_puts(
            'set_volts_mv_num                        902 \r\n'
            'set_volts_mv_den                      14400 ')
        for str in (('', ) * 3):
            d.bc15_puts(str)

        d.dcl.output(2.0, True)
        time.sleep(0.5)
        d.bc15.stat()
        vout = tester.MeasureGroup(
            (m.dmm_vout, m.arm_vout, m.arm_2amp, m.arm_2amp_lucky,
             m.arm_switch, )).reading1
        # Calibrate output voltage
        d.bc15.cal_vout(vout)
        self.fifo_push(((s.oVout, 14.40), ))
        m.dmm_vout_cal.measure()

    def _step_loaded(self):
        """Tests of the output."""
        self.fifo_push(((s.oVout, (14.4, ) * 5 + (11.0, ), ), ))
        d.bc15_puts(
            'not-pulsing-volts=14432 ;mV \r\nnot-pulsing-current=14000 ;mA ')

        d.dcl.output(14.0, True)
        time.sleep(0.5)
        d.bc15.stat()
        tester.MeasureGroup(
            (m.dmm_vout, m.arm_vout, m.arm_14amp, m.ramp_ocp, ))
