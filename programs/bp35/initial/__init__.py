#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""BP35 Initial Test Program."""

import logging
import time
import tester
import share
from . import support
from . import limit

INI_LIMIT = limit.DATA


class Initial(tester.TestSequence):

    """BP35 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.phydev = physical_devices
        self.limits = test_limits
        self.sernum = None
        self.hwver = None
        self.hwver_pic = None
        self.logdev = None
        self.sensor = None
        self.meas = None

    def open(self, sequence=None):
        """Prepare for testing."""
        self._logger.info('Open')
        self.logdev = support.LogicalDevices(self.phydev, self.fifo)
        self.sensor = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensor, self.limits)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep(
                'ProgramPIC', self._step_program_pic, not self.fifo),
            tester.TestStep(
                'ProgramARM', self._step_program_arm, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('SolarReg', self._step_solar_reg),
            tester.TestStep('Aux', self._step_aux),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('CanBus', self._step_canbus),
            )
        super().open(sequence)
        # Apply power to fixture (Comms & Trek2) circuits.
        self.logdev.dcs_vcom.output(12.0, True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        # Remove power from fixture circuits.
        self.logdev.dcs_vcom.output(0, False)
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.logdev.reset()

    @share.oldteststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals and Solar Reg input
        to power up the micros.

        """
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        mes.dmm_lock.measure(timeout=5)
        # Detect the hardware version & choose correct HW_VER values
        if mes.hardware8.measure().result:
            self._logger.info(repr('Hardware Version 8+'))
            self.hwver = limit.ARM_HW_VER8
            dev.program_pic.hexfile = limit.PIC_HEX8
            self.hwver_pic = limit.PIC_HW_VER8
        elif mes.hardware5.measure().result:
            self._logger.info(repr('Hardware Version 5-7'))
            self.hwver = limit.ARM_HW_VER5
            dev.program_pic.hexfile = limit.PIC_HEX1
            self.hwver_pic = limit.PIC_HW_VER1
        else:
            self._logger.info(repr('Hardware Version 1-4'))
            self.hwver = limit.ARM_HW_VER1
            dev.program_pic.hexfile = limit.PIC_HEX1
            self.hwver_pic = limit.PIC_HW_VER1
        # Apply DC Sources to Battery terminals and Solar Reg input
        dev.dcs_vbat.output(limit.VBAT_IN, True)
        dev.rla_vbat.set_on()
        dev.dcs_sreg.output(limit.SOLAR_VIN, True)
        tester.MeasureGroup(
            (mes.dmm_vbatin, mes.dmm_3v3, mes.dmm_solarvcc), timeout=5)

    @share.oldteststep
    def _step_program_pic(self, dev, mes):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        dev.program_pic.program()
        dev.dcs_sreg.output(0.0)  # Switch off the Solar

    @share.oldteststep
    def _step_program_arm(self, dev, mes):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        dev.program_arm.program()
        # Reset microprocessor for boards that need reprogramming by Service
        dev.dcs_vbat.output(0.0)
        dev.dcl_bat.output(1.0)
        time.sleep(1)
        dev.dcl_bat.output(0.0)
        dev.dcs_vbat.output(limit.VBAT_IN)

    @share.oldteststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        dev.bp35.open()
        dev.rla_reset.pulse(0.1)
        dev.dcs_sreg.output(limit.SOLAR_VIN)
        dev.bp35.action(None, delay=1.5, expected=2)  # Flush banner
        dev.bp35['UNLOCK'] = True
        dev.bp35['HW_VER'] = self.hwver
        dev.bp35['SER_ID'] = self.sernum
        dev.bp35['NVDEFAULT'] = True
        dev.bp35['NVWRITE'] = True
        dev.bp35['SR_DEL_CAL'] = True
        dev.bp35['SR_HW_VER'] = self.hwver_pic
        # Restart required because of HW_VER setting
        dev.rla_reset.pulse(0.1)
        dev.bp35.action(None, delay=1.5, expected=2)  # Flush banner
        dev.bp35['UNLOCK'] = True
        mes.arm_swver.measure()
        dev.bp35.manual_mode()

    @share.oldteststep
    def _step_solar_reg(self, dev, mes):
        """Test & Calibrate the Solar Regulator board."""
        # Switch on fixture BC282 to power Solar Reg input
        dev.rla_acsw.set_on()
        dev.acsource.output(voltage=240.0, output=True)
        dev.dcs_sreg.output(0.0, output=False)
        tester.MeasureGroup((mes.arm_solar_alive, mes.arm_vout_ov, ))
        # The SR needs V & I set to zero after power up or it won't start.
        dev.bp35.solar_set(0, 0)
        # Now set the actual output settings
        dev.bp35.solar_set(limit.SOLAR_VSET, limit.SOLAR_ISET)
        time.sleep(2)           # Wait for the Solar to start & overshoot
        dev.bp35['VOUT_OV'] = 2     # Reset OVP Latch because the Solar overshot
        # Read solar input voltage and setup ARM measurement limits
        solar_vin = mes.dmm_solarvin.measure(timeout=5).reading1
        mes.arm_solar_vin_pre.testlimit = (
            tester.testlimit.LimitHiLoPercent(
                'ARM-SolarVin-Pre',
                (solar_vin, limit.SOLAR_VIN_PRE_PERCENT)), )
        mes.arm_solar_vin_post.testlimit = (
            tester.testlimit.LimitHiLoPercent(
                'ARM-SolarVin-Post',
                (solar_vin, limit.SOLAR_VIN_POST_PERCENT)), )
        # Check that Solar Reg is error-free, the relay is ON, Vin reads ok
        tester.MeasureGroup(
            (mes.arm_solar_error, mes.arm_solar_relay,
             mes.arm_solar_vin_pre, ))
        vmeasured = mes.dmm_vsregpre.measure(timeout=5).reading1
        dev.bp35['SR_VCAL'] = vmeasured   # Calibrate output voltage setpoint
        dev.bp35['SR_VIN_CAL'] = solar_vin  # Calibrate input voltage reading
        # New solar sw ver 182 is too dumb to change the setpoint until a
        # DIFFERENT voltage setpoint is given...
        dev.bp35.solar_set(limit.SOLAR_VSET - 0.05, limit.SOLAR_ISET)
        dev.bp35.solar_set(limit.SOLAR_VSET, limit.SOLAR_ISET)
        time.sleep(1)
        tester.MeasureGroup(
            (mes.arm_solar_vin_post, mes.dmm_vsregpost, ))
        dev.dcl_bat.output(limit.SOLAR_ICAL, True)
        mes.arm_isregpre.measure(timeout=5)
        dev.bp35['SR_ICAL'] = limit.SOLAR_ICAL  # Calibrate current setpoint
        time.sleep(1)
        mes.arm_isregpost.measure(timeout=5)
        dev.dcl_bat.output(0.0)
        # Switch off fixture BC282
        dev.acsource.output(voltage=0.0)
        dev.rla_acsw.set_off()

    @share.oldteststep
    def _step_aux(self, dev, mes):
        """Apply Auxiliary input."""
        dev.dcs_vaux.output(limit.VAUX_IN, output=True)
        dev.dcl_bat.output(0.5)
        dev.bp35['AUX_RELAY'] = True
        tester.MeasureGroup(
            (mes.dmm_vaux, mes.arm_auxv, mes.arm_auxi), timeout=5)
        dev.bp35['AUX_RELAY'] = False
        dev.dcs_vaux.output(0.0, output=False)
        dev.dcl_bat.output(0.0)

    @share.oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        # Apply 240Vac & check
        dev.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup((mes.dmm_acin, mes.dmm_pri12v), timeout=10)
        # Enable PFC & DCDC converters
        dev.bp35.power_on()
        # Wait for PFC overshoot to settle
        mes.dmm_vpfc.stable(limit.PFC_STABLE)
        mes.arm_vout_ov.measure()
        # Remove injected Battery voltage
        dev.rla_vbat.set_off()
        dev.dcs_vbat.output(0.0, output=False)
        # Is it now running on it's own?
        mes.arm_vout_ov.measure()
        tester.MeasureGroup(
            (mes.dmm_3v3, mes.dmm_15vs, mes.dmm_vbat), timeout=10)

    @share.oldteststep
    def _step_output(self, dev, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        # All outputs OFF
        dev.bp35.load_set(set_on=True, loads=())
        # A little load on the output.
        dev.dcl_out.output(1.0, True)
        mes.dmm_vloadOff.measure(timeout=2)
        # One at a time ON
        for load in range(14):
            with tester.PathName('L{}'.format(load + 1)):
                dev.bp35.load_set(set_on=True, loads=(load, ))
                mes.dmm_vload.measure(timeout=2)
        # All outputs ON
        dev.bp35.load_set(set_on=False, loads=())

    @share.oldteststep
    def _step_remote_sw(self, dev, mes):
        """Test Remote Load Isolator Switch."""
        dev.rla_loadsw.set_on()
        mes.dmm_vloadOff.measure(timeout=5)
        dev.rla_loadsw.set_off()
        mes.dmm_vload.measure(timeout=5)

    @share.oldteststep
    def _step_ocp(self, dev, mes):
        """Test functions of the unit."""
        tester.MeasureGroup(
            (mes.arm_acv, mes.arm_acf, mes.arm_secT, mes.arm_vout,
             mes.arm_fan, mes.dmm_fanOff), timeout=5)
        dev.bp35['FAN'] = 100
        mes.dmm_fanOn.measure(timeout=5)
        dev.dcl_out.binary(1.0, 28.0, 5.0)
        dev.dcl_bat.output(4.0, output=True)
        tester.MeasureGroup((mes.dmm_vbat, mes.arm_battI, ), timeout=5)
        for load in range(14):
            with tester.PathName('L{}'.format(load + 1)):
                mes.arm_loads[load].measure(timeout=5)
        mes.ramp_ocp.measure(timeout=5)
        dev.dcl_bat.output(0.0)

    @share.oldteststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes.arm_can_bind.measure(timeout=10)
        dev.bp35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(limit.CAN_ECHO))
        dev.bp35['CAN'] = limit.CAN_ECHO
        echo_reply = dev.bp35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        self.sensor.mir_can.store(echo_reply)
        mes.rx_can.measure()
