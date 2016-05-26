#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

import os
import inspect
import logging
import time

import tester
from share import ProgramPIC
from . import support
from . import limit

MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

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
        self._sernum = None
        self._hwver = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices, self._fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        # Apply power to fixture (Comms & Trek2) circuits.
        d.dcs_vcom.output(12.0, True)

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
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_prepare(self):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals and Solar Reg input
        to power up the micros.

        """
        self.fifo_push(
            ((s.oLock, 10.0), (s.hardware, 1000),
             (s.oVbat, 12.0), (s.o3V3, 3.3), (s.o3V3prog, 3.3),
             (s.oSnEntry, ('A1626010123', )), ))

        self._sernum = m.ui_SnEntry.measure().reading1
        m.dmm_lock.measure(timeout=5)
        # Detect the hardware version
        if m.hardware5.measure().result:
            self._logger.info(repr('Hardware Version 5+'))
            self._hwver = limit.ARM_HW_VER5
        else:
            self._logger.info(repr('Hardware Version 1-4'))
            self._hwver = limit.ARM_HW_VER
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
            limit.PIC_HEX, folder, '33FJ16GS402', s.oMirPIC, self._fifo)
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
        # Program the ARM device
        d.programmer.program()
        d.rla_boot.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        self.fifo_push(((s.oSnEntry, ('A1526040123', )), ))
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) + ('success', ) * 2 + ('', ) * 4 +
                (limit.ARM_VERSION, ) +
                ('', ) * 4                  # Manual mode
                ):
            d.bp35_puts(str)

# FIXME: Remove power to microprocessor and start again.
#       Needed when upgrading a programmed unit.
        d.dcs_vbat.output(0.0)
        time.sleep(2.0)
        d.dcs_vbat.output(12.4)
        time.sleep(2.0)

        d.bp35.open()
        d.rla_reset.pulse(0.1)
        d.bp35.action(None, delay=1.5, expected=2)  # Flush banner
        d.bp35['UNLOCK'] = '$DEADBEA7'
        d.bp35['HW_VER'] = self._hwver
        d.bp35['SER_ID'] = self._sernum
        d.bp35['NVDEFAULT'] = True
        d.bp35['NVWRITE'] = True
        d.bp35['SR_DEL_CAL'] = True
        d.dcs_sreg.output(0.0)
        time.sleep(1)
        d.dcs_sreg.output(22.0)
        time.sleep(1)
        d.bp35['SR_HW_VER'] = limit.PIC_HW_VER
        m.arm_SwVer.measure()
        d.bp35.manual_mode()

    def _step_solar_reg(self):
        """Test the Solar Regulator board.

        Set the Solar Reg output voltage to 13.65V.
        Measure actual Solar Reg output voltage.
        Calibrate and measure again.

        """
        self.fifo_push(((s.oVsreg, (13.0, 13.5)), ))
        for str in (('1.0', '0', '200') +   # Solar alive, Vout OV, SR Temp
                    ('0', ) * 4             # 2 x Solar VI, Vout OV, SR Cal
                    ):
            d.bp35_puts(str)

        MeasureGroup((m.arm_solar_alive, m.arm_vout_ov, ))
        srtemp = d.bp35['SR_TEMP']
        self._logger.debug('Temperature: %s', srtemp)
        # The SR needs V & I set to zero after power up or it won't start.
        d.bp35.action('{} {} SOLAR-SETP-V-I'.format(0, 0))
        # Now set the actual output settings
        d.bp35.action(
            '{} {} SOLAR-SETP-V-I'.format(
                int(limit.SOLAR_VSET * 1000),
                int(limit.SOLAR_ISET * 1000)
                ))
        time.sleep(2)
        d.bp35['VOUT_OV'] = 2     # OVP Latch reset
        vmeasured = m.dmm_vsregpre.measure(timeout=5).reading1
        d.bp35['SR_VCAL'] = vmeasured
        time.sleep(1)
        m.dmm_vsregpost.measure(timeout=5)
        # Remove Solar Reg input voltage
        d.dcs_sreg.output(0.0, output=False)

    def _step_aux(self):
        """Apply Auxillary input and measure voltage and current."""
        self.fifo_push(((s.oVbat, 13.5), ))
        for str in (('', '13500', '350', '')):
             d.bp35_puts(str)

        d.dcs_vaux.output(13.5, output=True)
        d.dcl_bat.output(0.5)
        d.bp35['AUX_RELAY'] = True
        MeasureGroup((m.dmm_vaux, m.arm_auxV, m.arm_auxI), timeout=5)
        d.bp35['AUX_RELAY'] = False
        d.dcs_vaux.output(0.0, output=False)
        d.dcl_bat.output(0.0)

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac."""
        self.fifo_push(
            ((s.oACin, 240.0), (s.o12Vpri, 12.5), (s.o5Vusb, 5.0),
             (s.o3V3, 3.3), (s.o15Vs, 12.5), (s.oVbat, 12.8),
             (s.oVpfc, (415.0, 415.0), )))
        for str in (('0', ) +
                    ('', ) * 4 +
                    ('0', )
                    ):
            d.bp35_puts(str)

        # Apply 240Vac & check
        d.acsource.output(voltage=240.0, output=True)
        MeasureGroup((m.arm_vout_ov, ))
        MeasureGroup((m.dmm_acin, m.dmm_12Vpri, m.dmm_5Vusb, ), timeout=10)
        # Enable PFC & DCDC converters
        d.bp35.power_on()
        # Wait for PFC overshoot to settle
        _PFC_STABLE = 0.05
        m.dmm_vpfc.stable(_PFC_STABLE)
        # Remove injected Battery voltage
        d.rla_vbat.set_off()
        d.dcs_vbat.output(0.0, output=False)
        # Is it all still running?
        MeasureGroup((m.arm_vout_ov, ))
        MeasureGroup((m.dmm_3V3, m.dmm_15Vs, m.dmm_vbat), timeout=10)

    def _step_output(self):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        self.fifo_push(
            ((s.oVload, (0.0, ) + (12.8, ) * 14 + (0.25, 12.34)),  ))
        for str in (('', ) * (1 + 14 + 1)):
            d.bp35_puts(str)

        # All outputs OFF
        d.bp35.load_set(set_on=True, loads=())
        # A little load on the output.
        d.dcl_out.output(1.0, True)
        m.dmm_vloadOff.measure(timeout=2)
        # One at a time ON
        for ld in range(14):
            tester.testsequence.path_push('L{}'.format(ld + 1))
            d.bp35.load_set(set_on=True, loads=(ld, ))
            m.dmm_vload.measure(timeout=2)
            tester.testsequence.path_pop()
        # All outputs ON
        d.bp35.load_set(set_on=False, loads=())
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
            ((s.oFan, (0, 12.0)),
             (s.oVbat, 12.8), (s.oVbat, (12.8, ) * 6 + (11.0, ), ), ))
        if self._fifo:
            for sen in s.ARM_Loads:
                sen.store(2.0)
        for str in (('240', '50000', '350', '12800', '500', '', '4000')):
            d.bp35_puts(str)

        MeasureGroup(
            (m.arm_acv, m.arm_acf, m.arm_secT, m.arm_vout, m.arm_fan,
             m.dmm_fanOff), timeout=5)
        d.bp35['FAN'] = 100
        m.dmm_fanOn.measure(timeout=5)
        d.dcl_out.binary(1.0, 28.0, 5.0)
        d.dcl_bat.output(4.0, output=True)
        MeasureGroup((m.dmm_vbat, m.arm_battI, ), timeout=5)
        for ld in range(14):
            tester.testsequence.path_push('L{}'.format(ld + 1))
            m.arm_loads[ld].measure(timeout=5)
            tester.testsequence.path_pop()
        m.ramp_OCP.measure(timeout=5)
        d.dcl_bat.output(0.0)

    def _step_canbus(self):
        """Test the Can Bus."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            d.bp35_puts(str)
        d.bp35_puts('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.arm_can_bind.measure(timeout=10)
        d.bp35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(limit.CAN_ECHO))
        d.bp35['CAN'] = limit.CAN_ECHO
        echo_reply = d.bp35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.oMirCAN.store(echo_reply)
        m.rx_can.measure()
