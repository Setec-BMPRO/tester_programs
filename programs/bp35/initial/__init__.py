#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
from isplpc import Programmer, ProgrammingError
from ...share.programmer import ProgramPIC
from ...share.sim_serial import SimSerial
from ..console import Console
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
_HW_VER = (3, 0, 'A')
# ARM software image file
_ARM_VER = '1.2.12876.3637'
_ARM_BIN = 'bp35_' + _ARM_VER + '.bin'
# Soler Regulator Hardware version
_SR_HW_VER = 1
# dsPIC software image file
_PIC_HEX = 'bp35sr_1.0.12123.142.hex'

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
            ('SolarReg', self._step_solar_reg, None, True),
            ('Aux', self._step_aux, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('Output', self._step_output, None, True),
            ('TestUnit', self._step_test_unit, None, True),
            ('CanBus', self._step_canbus, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Serial connection to the BP35 console
        bp35_ser = SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        bp35_ser.setPort(_ARM_PORT)
        # BP35 Console driver
        self._bp35 = Console(bp35_ser)
        self.sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._bp35)
        m = support.Measurements(s, self._limits)
        # Apply power to fixture (Comms & Trek2) circuits.
        d.dcs_vcom.output(12.0, True)

    def _bp35_puts(self,
                   string_data, preflush=0, postflush=1, priority=False,
                   addcrlf=True):
        """Push string data into the BP35 buffer.

        Only push if FIFOs are enabled.
        postflush=1 since the reader stops a flush marker or empty buffer.

        """
        if self._fifo:
            if addcrlf:
                string_data = string_data + '\r\n'
            self._bp35.puts(string_data, preflush, postflush, priority)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        # Remove power from fixture circuits.
        d.dcs_vcom.output(0, False)
        m = d = s = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._bp35.close()
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
        Apply power to the unit's Battery terminals and Solar Reg input
        to power up the micros.

        """
        self.fifo_push(
            ((s.oLock, 10.0), (s.osw1, 100.0), (s.osw2, 100.0),
             (s.osw3, 100.0), (s.osw4, 100.0),
             (s.oVbat, 12.0), (s.o3V3, 3.3), (s.o3V3prog, 3.3), ))

        self.sernum = m.ui_SnEntry.measure()[1][0]
        MeasureGroup(
            (m.dmm_lock, m.dmm_sw1, m.dmm_sw2, m.dmm_sw3, m.dmm_sw4, ),
            timeout=5)
        # Apply DC Sources to Battery terminals and Solar Reg input
        d.dcs_vbat.output(12.4, True)
        d.rla_vbat.set_on()
        d.dcs_sreg.output(20.0, True)
        MeasureGroup((m.dmm_vbatin, m.dmm_3V3, m.dmm_3V3prog), timeout=5)

    def _step_program_pic(self):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        # Start the PIC programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        d.rla_pic.set_on()
        pic = ProgramPIC(
            _PIC_HEX, folder, '33FJ16GS402', s.oMirPIC, self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_pic.set_off()
        m.pgmPIC.measure()

    def _step_program_arm(self):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        d.rla_boot.set_on()
        d.rla_reset.pulse(0.1)
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, _ARM_BIN)
        with open(file, 'rb') as infile:
            bindata = bytearray(infile.read())
        self._logger.debug('Read %d bytes from %s', len(bindata), file)
        try:
            ser = SimSerial(port=_ARM_PORT, baudrate=115200)
            pgm = Programmer(
                ser, bindata, erase_only=False, verify=False, crpmode=False)
            try:
                pgm.program()
                s.oMirARM.store(0)
            except ProgrammingError:
                s.oMirARM.store(1)
        except:
            raise
        finally:
            ser.close()
        m.pgmARM.measure()
        d.rla_boot.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        self.fifo_push(((s.oSnEntry, ('A1526040123', )), ))
        for str in (('Banner1\r\nBanner2', ) +  # Banner lines
                    ('', ) * 5 +                # defaults
                    ('', ) * 2                  # SR setup
                    ):
            self._bp35_puts(str)
        self._bp35_puts(_ARM_VER, postflush=0)  # SwVer measure

        self._bp35.open()
        d.rla_reset.pulse(0.1)
        time.sleep(1)
        self._bp35.action(None, delay=0.5, expected=2)  # Flush banner
        self._bp35.defaults(_HW_VER, self.sernum)
        self._bp35['SR_DEL_CAL'] = True
        d.dcs_sreg.output(0.0)
        time.sleep(1)
        d.dcs_sreg.output(22.0)
        time.sleep(1)
        self._bp35['SR_HW_VER'] = _SR_HW_VER
        m.arm_SwVer.measure()
        self._bp35.manual_mode()

    def _step_solar_reg(self):
        """Test the Solar Regulator board.

        Set the Solar Reg output voltage to 13.65V.
        Measure actual Solar Reg output voltage.
        Calibrate and measure again.

        """
        self.fifo_push(((s.oVsreg, (13.0, 13.5)), ))
        self._bp35_puts('1.0')
        self._bp35_puts('0')
        self._bp35_puts('275', postflush=0)

        MeasureGroup((m.arm_solar_alive, m.arm_vout_ov, ))
        srtemp = self._bp35['SR_TEMP']
        self._logger.debug('Temperature: %s', srtemp)
        vset = self._limits['Vset'].limit
        iset = self._limits['Iset'].limit
        self._bp35['SR_VSET'] = vset
        self._bp35['SR_ISET'] = iset
        time.sleep(2)
        self._bp35['VOUT_OV'] = 2     # OVP Latch reset
        vmeasured = m.dmm_vsregpre.measure(timeout=5)[1][0]
        self._bp35['SR_VCAL'] = vmeasured
        time.sleep(1)
        m.dmm_vsregpost.measure(timeout=5)
        # Remove Solar Reg input voltage
        d.dcs_sreg.output(0.0, output=False)

    def _step_aux(self):
        """Apply Auxillary input and measure voltage and current."""
        self.fifo_push(
            ((s.ARM_AuxV, 13.5), (s.ARM_AuxI, 0.35), (s.oVbat, 13.5), ))

        d.dcs_vaux.output(13.5, output=True)
        d.dcl_bat.output(0.5)
        self._bp35['AUX_RELAY'] = True
        MeasureGroup(
            (m.dmm_vaux, m.arm_auxV, m.arm_auxI), timeout=5)
        self._bp35['AUX_RELAY'] = False
        d.dcs_vaux.output(0.0, output=False)
        d.dcl_bat.output(0.0)

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac."""
        self.fifo_push(
            ((s.oACin, 240.0), (s.o12Vpri, 12.5), (s.o5Vusb, 5.0),
             (s.o3V3, 3.3), (s.o15Vs, 12.5), (s.oVbat, 12.8),
             (s.oVpfc, (415.0, 415.0), )))
        for str in (('0', ) +
                    ('', ) * 3
                    ):
            self._bp35_puts(str)
        self._bp35_puts('0', postflush=0)

        # Apply 240Vac & check
        d.acsource.output(voltage=240.0, output=True)
        MeasureGroup((m.arm_vout_ov, ))
        MeasureGroup(
            (m.dmm_acin, m.dmm_12Vpri, m.dmm_5Vusb, ),
            timeout=10)
        # Enable PFC & DCDC converters
        self._bp35.power_on()
        # Wait for PFC overshoot to settle
        _PFC_STABLE = 0.05
        m.dmm_vpfc.stable(_PFC_STABLE)
        # Remove injected Battery voltage
        d.rla_vbat.set_off()
        d.dcs_vbat.output(0.0, output=False)
        # Is it all still running?
        MeasureGroup((m.arm_vout_ov, ))
        MeasureGroup(
            (m.dmm_3V3, m.dmm_15Vs, m.dmm_vbat),
            timeout=10)

    def _step_output(self):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        self.fifo_push(
            ((s.oVload, (0.0, ) + (12.8, ) * 14),
             (s.oVload, (0.25, 12.34)),  ))

        # All outputs OFF
        self._bp35.load_set(set_on=True, loads=())
        # A little load on the output.
        d.dcl_out.output(1.0, True)
        m.dmm_vloadOff.measure(timeout=2)
        # One at a time ON
        for ld in range(14):
            tester.testsequence.path_push('L{}'.format(ld + 1))
            self._bp35.load_set(set_on=True, loads=(ld, ))
            m.dmm_vload.measure(timeout=2)
            tester.testsequence.path_pop()
        # All outputs ON
        self._bp35.load_set(set_on=False, loads=())
        # Test Remote Load Isolator Switch
        tester.testsequence.path_push('RemoteSw')
        d.rla_loadsw.set_on()
        m.dmm_vloadOff.measure(timeout=5)
        d.rla_loadsw.set_off()
        m.dmm_vload.measure(timeout=5)
        tester.testsequence.path_pop()

    def _step_test_unit(self):
        """Test functions of the unit."""
        self.fifo_push(
            ((s.ARM_AcV, 240.0), (s.ARM_AcF, 50.0),
             (s.ARM_SecT, 26.0), (s.ARM_Vout, 12.8), (s.ARM_Fan, 50),
             (s.oFan, (0, 12.0)), (s.ARM_BattI, 4.0),
             (s.oVbat, 12.8), (s.oVbat, (12.8, ) * 6 + (11.0, ), ), ))
        # (s.ARM_PriT, 26.0), [disabled because it has bugs...]

        # m.arm_priT, [disabled because it has bugs...]
        MeasureGroup((m.arm_acv, m.arm_acf, m.arm_secT,
                     m.arm_vout, m.arm_fan, m.dmm_fanOff), timeout=5)
        self._bp35['FAN'] = 100
        m.dmm_fanOn.measure(timeout=5)
        d.dcl_out.binary(1.0, 28.0, 5.0)
        d.dcl_bat.output(4.0, output=True)
        MeasureGroup((m.dmm_vbat, m.arm_battI, ), timeout=5)
        if self._fifo:
            for sen in s.ARM_Loads:
                sen.store(2.0)
        for ld in range(14):
            tester.testsequence.path_push('L{}'.format(ld + 1))
            m.arm_loads[ld].measure(timeout=5)
            tester.testsequence.path_pop()
        m.ramp_OCP.measure(timeout=5)
        d.dcl_bat.output(0.0)

    def _step_canbus(self):
        """Test the Can Bus."""
        for str in ('junk', '', '0x10000000', '', 'RRQ,32,0,7'):
            self._bp35_puts(str)

        m.arm_can_stats.measure()
        self._bp35.can_mode(True)
        m.arm_can_id.measure()
