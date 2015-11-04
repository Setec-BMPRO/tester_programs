#!/usr/bin/env python3
"""BC15 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
import share.isplpc
import share.programmer
from share.sim_serial import SimSerial
import share.bc15
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt':    'COM2',
             }[os.name]
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
_HW_VER = (1, 0, '')
# ARM software image file
_ARM_BIN = 'bc15_1.0.3156.bin'

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
        self._bc15 = share.bc15.Console(
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        self._bc15.setPort(_ARM_PORT)

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

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._bc15.close()
        global m, d, s, t
        # Remove power from fixture circuit.
        d.dcs_vcom.output(0, False)
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
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
        self.fifo_push(((s.olock, 10.0), ))
        MeasureGroup((m.dmm_lock, ), timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        # Set BOOT active before RESET so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Reset micro.
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
                ser, bindata, erase_only=False, verify=True, crpmode=False)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except share.isplpc.ProgrammingError:
                s.oMirARM.store(1)
        finally:
            try:
                ser.close()
            except:
                pass
        m.pgmARM.measure()
        # Reset BOOT to ARM
        d.rla_boot.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.

        """
        dummy_sn = 'A1526040123'
        self.fifo_push(((s.oSnEntry, (dummy_sn, )), ))
        sernum = m.ui_SnEntry.measure()[1][0]
#        sernum = dummy_sn
        self._bc15.open()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        self._bc15_puts('Banner1\r\nBanner2\r\n')
        self._bc15.action(None, delay=0.5, expected=2)  # Flush banner
        self._bc15.defaults(_HW_VER, sernum)
        self._bc15_puts('1.0.10902.3156\r\n')
        m.arm_SwVer.measure()

    def _step_powerup(self):
        """Power up the Unit with 240Vac."""
        self.fifo_push(((s.oACin, 240.0), (s.oVout, 12.0), ))

    def _bc15_puts(self,
                   string_data, preflush=0, postflush=0, priority=False):
        """Push string data into the BC15 buffer only if FIFOs are enabled."""
        if self._fifo:
            self._bc15.puts(string_data, preflush, postflush, priority)
