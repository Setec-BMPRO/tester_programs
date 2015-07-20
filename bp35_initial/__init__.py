#!/usr/bin/env python3
"""BP35 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
import share.isplpc
import share.programmer
import share.sim_serial
import share.bp35
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
_ARM_BIN = 'bp35_1.0.3119.bin'
# dsPIC software image file
_PIC_HEX = 'bp35sr_1.hex'

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
            ('PartDetect', self._step_part_detect, None, True),
            ('ProgramARM', self._step_program_arm, None, True),
            ('ProgramPIC', self._step_program_pic, None, True),
            ('PowerUp', self._step_powerup, None, False),
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
        self._bp35 = share.bp35.Console(
            simulation=self._fifo,
            baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        self._bp35.setPort(_ARM_PORT)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits, self._bp35)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        try:
            self._bp35.close()
        except:
            pass
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
            d.dcl_out.output(2.0)
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

    def _step_part_detect(self):
        """Measure fixture lock and part detection microswitches."""
        self.fifo_push(
            ((s.oLock, 10.0), (s.osw1, 100.0), (s.osw2, 100.0),
             (s.osw3, 100.0), (s.osw4, 100.0), ))
        MeasureGroup(
            (m.dmm_Lock, m.dmm_sw1, m.dmm_sw2, m.dmm_sw3, m.dmm_sw4, ),
             timeout=5)
        # Apply power to comms circuit.
        d.dcs_vcom.output(12.8, True)

    def _step_program_arm(self):
        """Program the ARM device.

        External Vbat is applied to power the ARM for programming.

        """
        self.fifo_push(((s.o3V3, 3.3), ))
        # Apply and check injected rails
        d.dcs_vbat.output(12.8, True)
        d.rla_vbat.set_on()
        MeasureGroup((m.dmm_Vbat, m.dmm_3V3, ), timeout=5)
        # Set BOOT active before power-on so the ARM boot-loader runs
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
            ser = share.sim_serial.SimSerial(port=_ARM_PORT, baudrate=115200)
            ser.flush()
            # Program the device (LPC1549 has internal CRC for verification)
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
        # Reset BOOT to ARM
        d.rla_boot.set_off()

    def _step_program_pic(self):
        """Program the dsPIC device.

        External Vbat powers the PIC for programming.

        """
        self.fifo_push(((s.o3V3prog, 3.3), ))
        m.dmm_3V3prog.measure(timeout=5)
        # Start the PIC programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        d.rla_pic.set_on()
        pic = share.programmer.ProgramPIC(
            _PIC_HEX, folder, '33FJ16GS402', s.oMirPIC, self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_pic.set_off()
        m.pgmPIC.measure()

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac."""
        self.fifo_push(
            ((s.oACin, 240.0), (s.oVbus, 415.0), (s.o12Vpri, 12.5),
             (s.o5Vusb, 5.0), (s.o3V3, 3.3), (s.o15Vs, 12.5),
             (s.oVout, 12.8), (s.oVbat, 12.8),
             (s.oVout, 12.8), (s.oVbat, 12.8), ))
        t.pwr_up.run()

    def _step_test_arm(self):
        """Test the ARM device."""
        dummy_sn = 'A1526040123'
        self.fifo_push(((s.oSnEntry, (dummy_sn, )), ))
#        sernum = m.ui_SnEntry.measure()[1][0]
        sernum = dummy_sn
        self._bp35.open()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        if self._fifo:
            # Startup banner
            self._bp35.puts('Banner1\r\nBanner2\r\n')
            # Going into Test Mode
            self._bp35.putch('"STATUS XN?', preflush=1)
            self._bp35.puts('0x00000000\r\n')
            self._bp35.putch('$80000000 "STATUS XN!', preflush=1, postflush=1)
            # Unlock
            self._bp35.putch('$DEADBEA7 UNLOCK', preflush=1, postflush=1)
            # Set hardware ID
            self._bp35.putch('1 0 " SET-HW-VER', preflush=1, postflush=1)
            # Set software ID
            self._bp35.putch('"{} SET-SERIAL-ID'.format(dummy_sn),
                preflush=1, postflush=1)
            # Set & Write defaults
            self._bp35.putch('NV-DEFAULT', preflush=1, postflush=1)
            self._bp35.putch('NV-WRITE', preflush=1, postflush=1)
            # Version queries
            self._bp35.putch('SW-VERSION?', preflush=1)
            self._bp35.puts('1.0\r\n')
            self._bp35.putch('BUILD?', preflush=1)
            self._bp35.puts('3119\r\n')
        self._bp35.action(None, expected=2)    # Flush banner (2 lines)
        self._bp35.testmode(True)
        self._bp35.defaults(_HW_VER, sernum)
        self._bp35.version()

    def _step_canbus(self):
        """Test the Can Bus."""

    def _step_ocp(self):
        """Ramp up load until OCP."""
        self.fifo_push(((s.oVout, (12.8, ) * 16 + (11.0, ), ),
                        (s.oVbat, (12.8, ) * 16 + (11.0, ), ), ))
        d.dcl_out.output(0.0, output=True)
        d.dcl_bat.output(0.0, output=True)
        d.dcl_out.binary(0.0, 30.0, 5.0)
        m.ramp_OutOCP.measure()
        d.dcl_out.output(0.0)
        d.dcs_vbat.output(12.8, True)
        d.rla_vbat.set_on()
        m.dmm_Vbat.measure(timeout=5)
        d.dcl_bat.binary(0.0, 18.0, 5.0)
        m.ramp_BatOCP.measure()
        d.dcl_bat.output(0.0)
        d.rla_vbat.set_off()

    def _step_shutdown(self):
        """Apply overload to shutdown. Check load switch."""
        self.fifo_push(((s.oVout, (0.0, 12.8, 0.0, 12.8)), (s.oVbat, 12.9), ))
        t.shdn.run()
