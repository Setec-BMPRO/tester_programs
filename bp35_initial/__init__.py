#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

import os
import inspect
import serial
import logging
import time

import tester
import share.programmer
import share.trek2
import share.isplpc
import share.mock_serial
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt':    'COM2',
             }[os.name]

_ARM_BIN = 'BP35_1.0.3025.bin'

_PIC_HEX = '.hex'

_HEX_DIR = {'posix': '/opt/setec/ate4/bp35_initial',
            'nt': r'C:\TestGear\TcpServer\bp35_initial',
           }[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """BP35 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FixtureLock', self._step_fixture_lock, None, True),
            ('ProgramARM', self._step_program_arm, None, True),
            ('ProgramPIC', self._step_program_pic, None, False),
            ('TestArm', self._step_test_arm, None, False),
            ('CanBus', self._step_canbus, None, False),
            ('OCP', self._step_ocp, None, False),
            ('ShutDown', self._step_shutdown, None, False),
            ('ErrorCheck', self._step_error_check, None, True),
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
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            d.acsource.output(voltage=0.0, output=False)
            d.dcl.output(2.0)
            if self._fifo:
                d.discharge.pulse(0.1)
            else:
                time.sleep(1)
                d.discharge.pulse()
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.oLock, 10.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        External Vbat is applied to power the ARM for programming.

        """
        self.fifo_push(((s.o3V3, 3.30), ))
        # Apply and check injected rails
        d.dcs_vcom.output(12.0, True)
        d.dcs_vbat.output(12.0, True)
        MeasureGroup((m.dmm_3V3, ), timeout=5)
        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        # Start the ARM programmer
        self._logger.info('Start ARM programmer')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        ser = serial.Serial(port=_ARM_PORT, baudrate=115200)
        ser.flush()
        # Program the device
        pgm = share.isplpc.Programmer(
            ser, bindata, erase_only=False, verify=True, crpmode=False)
        try:
            pgm.program()
            s.oMirARM.store(0)
        except share.isplpc.ProgrammingError:
            s.oMirARM.store(1)
        ser.close()
        m.pgmARM.measure()
        # Reset BOOT to ARM
        d.rla_boot.set_off()

    def _step_program_pic(self):
        """Program the PIC device.

        External Vbat powers the PIC for programming.

        """
        self.fifo_push(((s.o5Vprog, 5.0), ))
        m.dmm_5Vprog.measure(timeout=5)
        # Start the PIC programmer
        self._logger.info('Start PIC programmer')
        d.rla_pic.set_on()
        pic = share.programmer.ProgramPIC(_PIC_HEX, _HEX_DIR, '33FJ16GS402',
                                          s.oMirPIC, self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_pic.set_off()
        m.pgmPIC.measure()

    def _step_test_arm(self):
        """Test the ARM device."""
        self.fifo_push(((s.oACin, 240.0), ))

        t.pwr_up.run()
        if self._fifo:
            self._arm_ser = share.mock_serial.MockSerial()
        else:
            self._arm_ser = serial.Serial(
                port=_ARM_PORT, baudrate=115200, timeout=0.1)
        self._armdev = share.trek2.Console(self._arm_ser)
        # Reset micro.
        d.rla_reset.pulse(0.1)
        self._armdev.unlock()

    def _step_canbus(self):
        """Test the Can Bus."""

    def _step_ocp(self):
        """Ramp up load until OCP."""
        self.fifo_push(((s.oVout, (12.8, ) * 11 + (11.0, ), ), ))
        d.dcl.output(0.0, output=True)
        d.dcl.binary(0.0, 32.0, 5.0)
        m.ramp_OCP.measure()

    def _step_shutdown(self):
        """Apply overload to shutdown. Check load switch."""
        self.fifo_push(((s.oVout, (0.0, 12.0, 0.0, 12.0)), (s.oVbat, 12.0), ))
        t.shdn.run()
