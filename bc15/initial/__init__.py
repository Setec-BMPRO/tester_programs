#!/usr/bin/env python3
"""BC15 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
import share.isplpc
from share.sim_serial import SimSerial
from .. import console
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM12'}[os.name]
# ARM software image file
_ARM_BIN = 'bc15_1.0.1230.bin'

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

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
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Serial connection to the BC15 console
        bc15_ser = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        bc15_ser.setPort(_ARM_PORT)
        # BC15 Console driver
        self._bc15 = console.Console(bc15_ser)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._bc15)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        # Apply power to fixture Comms circuit.
        d.dcs_vcom.output(12.0, True)
        time.sleep(1)       # Allow OS to detect USB serial port

    def _bc15_puts(self,
                   string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the BC15 buffer only if FIFOs are enabled."""
        if self._fifo:
            self._bc15.puts(string_data, preflush, postflush, priority)

    def _bc15_putstartup(self):
        """Push startup banner strings into fake serial port."""
        self._bc15_puts(
            'BC15\r\n'                          # BEGIN Startup messages
            'Build date:       06/11/2015\r\n'
            'Build time:       15:31:40\r\n'
            'SystemCoreClock:  48000000\r\n'
            'Software version: 1.0.11705.1203\r\n'
            'nonvol: reading crc invalid at sector 14 offset 0\r\n'
            'nonvol: reading nonvol2 OK at sector 15 offset 2304\r\n'
            'Hardware version: 0.0.[00]\r\n'
            'Serial number:    A9999999999\r\n'
            'Please type help command.\r\n'
            '> '                                # END Startup messages
            '"OK\\n PROMPT\r\n'                 # 1st command echo
            'OK\r\n'                            # and it's response
            '0 ECHO\r\nOK\r\n'                  # ECHO command echo
            'OK\r\n')                           # and it's response
        self._bc15_puts(
            'OK\r\n'                            # UNLOCK response
            'OK\r\n'                            # NV-DEFAULT response
            'OK\r\n'                            # NV-WRITE response
            '1.0.11778.1230\r\nOK\r\n',         # SwVer response
            preflush=1)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        # Remove power from fixture circuit.
        d.dcs_vcom.output(0, False)
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._bc15.close()
        d.acsource.output(voltage=0.0, output=False)
        d.dcl.output(2.0)
        time.sleep(1)
        d.discharge.pulse()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_part_detect(self):
        """Measure fixture lock and part detection microswitches."""
        self.fifo_push(((s.olock, 0.0), (s.ofanshort, 3300.0), ))
        MeasureGroup((m.dmm_lock, m.dmm_fanshort, ), timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        3V3 is injected to power the ARM for programming.

        """
        # Apply and check injected rail
        d.dcs_3v3.output(9.0, True)
        self.fifo_push(((s.o3V3, 3.3), ))
        m.dmm_3V3.measure(timeout=5)
        time.sleep(2)
        # Set BOOT active before RESET so the ARM boot-loader runs
        d.rla_boot.set_on()
        time.sleep(1)
        d.rla_reset.pulse(0.1)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        try:
            ser = SimSerial(port=_ARM_PORT, baudrate=115200)
            # Program the device
            pgm = share.isplpc.Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=False)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except share.isplpc.ProgrammingError:
                s.oMirARM.store(1)
        finally:
            ser.close()
        m.pgmARM.measure()
        # Remove BOOT signal from ARM
        d.rla_boot.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected voltage.
        Write Non-Volatile memory defaults.

        """
        d.dcs_3v3.output(9.0, True)
        d.rla_reset.pulse(0.1)
        time.sleep(0.5)
        self._bc15_putstartup()
        self._bc15.open()
        self._bc15.defaults()
        m.arm_SwVer.measure()
        self._bc15.close()
        d.dcs_3v3.output(0.0, False)

    def _step_powerup(self):
        """Power up the Unit with 240Vac and go to Power Supply mode."""
        self.fifo_push(
            ((s.oACin, 240.0), (s.oVbus, 330.0), (s.o12Vs, 12.0),
             (s.o3V3, 3.3), (s.o15Vs, 15.0), (s.oVout, (0.2, 14.4)), ))
        t.pwr_up.run()
        self._bc15_putstartup()
        self._bc15.open()
        self._bc15_puts('OK\r\n' * 10)
        self._bc15.ps_mode()
        m.dmm_vout.measure()
