#!/usr/bin/env python3
"""BP35 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
import share.isplpc
import share.programmer
from share.sim_serial import SimSerial
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
_ARM_BIN = 'bp35_1.0.3156.bin'
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
            ('Prepare', self._step_prepare, None, True),
            ('ProgramPIC', self._step_program_pic, None, not fifo),
            ('ProgramARM', self._step_program_arm, None, not fifo),
            ('Initialise', self._step_initialise_arm, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('Load', self._step_load, None, True),
            ('TestUnit', self._step_test_unit, None, True),
            ('CanBus', self._step_canbus, None, False),
            ('OCP', self._step_ocp, None, True),
            ('Aux', self._step_aux, None, True),
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
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        self._bp35.setPort(_ARM_PORT)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._bp35)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        # Apply power to fixture (Comms & Trek2) circuits.
        d.dcs_vcom.output(12.0, True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._bp35.close()
        global m, d, s, t
        # Remove power from fixture circuits.
        d.dcs_vcom.output(0, False)
        m = d = s = t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            d.acsource.output(voltage=0.0, output=False)
            d.dcl_out.output(2.0)
            time.sleep(1)
            d.discharge.pulse()
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_prepare(self):
        """Prepare to run a test.

        Measure fixture lock and part detection microswitches.
        Apply power to the unit's Battery terminals to power up the micros.

        """
        self.fifo_push(
            ((s.oLock, 10.0), (s.osw1, 100.0), (s.osw2, 100.0),
             (s.osw3, 100.0), (s.osw4, 100.0),
             (s.oVbat, 12.0), (s.o3V3, 3.3),))
        MeasureGroup(
            (m.dmm_lock, m.dmm_sw1, m.dmm_sw2, m.dmm_sw3, m.dmm_sw4, ),
             timeout=5)
        # Apply DC Source to Battery terminals
        d.dcs_vbat.output(12.4, True)
        d.rla_vbat.set_on()
        MeasureGroup((m.dmm_vbatin, m.dmm_3V3, ), timeout=5)

    def _step_program_pic(self):
        """Program the dsPIC device.

        Device is powered by injected Battery voltage.

        """
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

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        dummy_sn = 'A1526040123'
        self.fifo_push(((s.oSnEntry, (dummy_sn, )), ))
#        sernum = m.ui_SnEntry.measure()[1][0]
        sernum = dummy_sn
        self._bp35.open()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        self._bp35.puts('Banner1\r\nBanner2\r\n')
        self._bp35.action(None, delay=0.5, expected=2)  # Flush banner
        self._bp35.defaults(_HW_VER, sernum)
        self._bp35.puts('1.0.10902.3156\r\n')
        m.arm_SwVer.measure()
        self._bp35.manual_mode()

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac."""
        self.fifo_push(
            ((s.oACin, 240.0), (s.o12Vpri, 12.5), (s.o5Vusb, 5.0),
             (s.o3V3, 3.3), (s.o15Vs, 12.5), (s.oVbat, 12.8),
             (s.oVpfc, (415.0, 415.0), )))
        # Apply 240Vac & check
        d.acsource.output(voltage=240.0, output=True)
        MeasureGroup(
            (m.dmm_acin, m.dmm_12Vpri, m.dmm_5Vusb, ), timeout=10)
        # Enable PFC & DCDC converters
        self._bp35.power_on()
        # Wait for PFC overshoot to settle
        _PFC_STABLE = 0.05
        m.dmm_vpfc.stable(_PFC_STABLE)
        # Remove injected Battery voltage
        d.rla_vbat.set_off()
        d.dcs_vbat.output(0.0, output=False)
        # Is it all still running?
        MeasureGroup((m.dmm_3V3, m.dmm_15Vs, m.dmm_vbat), timeout=10)

    def _step_load(self):
        """Test the load output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        self.fifo_push(((s.oVout, (0.0, ) + (12.8, ) * 14),  ))
        # All outputs OFF
        self._bp35.load_set(set_on=True, loads=())
        m.dmm_voutOff.measure(timeout=2)
        # One at a time ON
        for ld in range(14):
            self._bp35.load_set(set_on=True, loads=(ld, ))
            m.dmm_vout.measure(timeout=2)
        # All outputs ON
        self._bp35.load_set(set_on=False, loads=())

    def _step_test_unit(self):
        """Test functions of the unit."""
        self.fifo_push(
            ((s.ARM_AcV, 240.0), (s.ARM_AcF, 50.0), (s.ARM_PriT, 26.0),
             (s.ARM_SecT, 26.0), (s.ARM_BattT, 26.0), (s.ARM_Vout, 12.8),
             (s.ARM_Fan, 50), (s.oFan, (0, 12.0)), (s.ARM_BattI, 4.0),
             (s.oVbat, 12.8), ))
        if self._fifo:
            for sen in s.ARM_Loads:
                sen.store(2.0)
        MeasureGroup((m.arm_acv, m.arm_acf, m.arm_priT, m.arm_secT, m.arm_battT,
                    m.arm_vout, m.arm_fan, m.dmm_fanOff), timeout=5)
        self._bp35['FAN'] = 100
        m.dmm_fanOn.measure(timeout=5)
        d.dcl_out.output(28.0, output=True)
        d.dcl_bat.output(4.0, output=True)
        MeasureGroup((m.dmm_vbat, ) + m.arm_loads + (m.arm_battI, ), timeout=5)

    def _step_canbus(self):
        """Test the Can Bus."""
        self.fifo_push(
            ((s.ARM_CANBIND, 0x10000000), (s.ARM_CANID, ('RRQ,16,0,7', )), ))
#        m.arm_can_bind.measure(timeout=5)
#        time.sleep(1)
#        self._bp35.puts('0x10000000\r\n')   # Going into CAN Test Mode
        self._bp35.can_mode(True)
        m.arm_can_id.measure()

    def _step_ocp(self):
        """Ramp up load until OCP."""
        self.fifo_push(((s.oVout, (12.8, ) * 16 + (11.0, ), ),
                        (s.oVbat, (12.8, ) * 10 + (11.0, ), ), ))
        t.ocp.run()

    def _step_aux(self):
        """Apply Auxillary input and measure voltage and current."""
        self.fifo_push(((s.ARM_AuxV, 12.5), (s.ARM_AuxI, 2.0), (s.oVout, 12.5), ))
        self._bp35['AUX_RELAY'] = True
        t.aux.run()

    def _step_shutdown(self):
        """Apply overload to shutdown."""
# FIXME: In manual mode it won't shutdown! No need to do this?
#        self.fifo_push(((s.oVout, (0.0, 12.8, 0.0, 12.8)), (s.oVbat, 12.9), ))
#        t.shdn.run()
