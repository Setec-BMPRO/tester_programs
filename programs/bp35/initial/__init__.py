#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

from functools import wraps
import logging
import time
import tester
import share
from . import support
from . import limit

INI_LIMIT = limit.DATA


def teststep(func):
    """Decorator to add arguments to the test step calls."""
    @wraps(func)
    def new_func(self):
        return func(self, self.logdev, self.sensor, self.meas)
    return new_func


class Initial(tester.TestSequence):

    """BP35 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep('ProgramPIC', self._step_program_pic, not fifo),
            tester.TestStep('ProgramARM', self._step_program_arm, not fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('SolarReg', self._step_solar_reg),
            tester.TestStep('Aux', self._step_aux),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('CanBus', self._step_canbus),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.phydev = physical_devices
        self.limits = test_limits
        self.sernum = None
        self.hwver = None
        self.logdev = None
        self.sensor = None
        self.meas = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self.logdev = support.LogicalDevices(self.phydev, self.fifo)
        self.sensor = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensor, self.limits)
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

    @teststep
    def _step_prepare(self, dev, sen, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switches.
        Apply power to the unit's Battery terminals and Solar Reg input
        to power up the micros.

        """
        self.fifo_push(
            ((sen.lock, 10.0), (sen.hardware, 1000),
             (sen.vbat, 12.0), (sen.o3v3, 3.3), (sen.o3v3prog, 3.3),
             (sen.sernum, ('A1626010123', )), ))

        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        mes.dmm_lock.measure(timeout=5)
        # Detect the hardware version & choose correct HW_VER values
        if mes.hardware8.measure().result:
            self._logger.info(repr('Hardware Version 8+'))
            self.hwver = limit.ARM_HW_VER8
        elif mes.hardware5.measure().result:
            self._logger.info(repr('Hardware Version 5-7'))
            self.hwver = limit.ARM_HW_VER5
        else:
            self._logger.info(repr('Hardware Version 1-4'))
            self.hwver = limit.ARM_HW_VER
        # Apply DC Sources to Battery terminals and Solar Reg input
        dev.dcs_vbat.output(limit.VBAT_IN, True)
        dev.rla_vbat.set_on()
        dev.dcs_sreg.output(limit.SOLAR_VIN, True)
        tester.MeasureGroup(
            (mes.dmm_vbatin, mes.dmm_3v3, mes.dmm_3v3prog), timeout=5)

    @teststep
    def _step_program_pic(self, dev, sen, mes):
        """Program the dsPIC device.

        Device is powered by Solar Reg input voltage.

        """
        dev.program_pic.program()
        dev.dcs_sreg.output(0.0)  # Switch off the Solar

    @teststep
    def _step_program_arm(self, dev, sen, mes):
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

    @teststep
    def _step_initialise_arm(self, dev, sen, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        self.fifo_push(((sen.sernum, ('A1526040123', )), ))
        for dat in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) + ('success', ) * 2 + ('', ) * 4 +
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) +
                (limit.ARM_VERSION, ) +
                ('', ) + ('0x10000', ) + ('', ) * 3     # Manual mode
            ):
            dev.bp35_puts(dat)

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
        dev.bp35['SR_HW_VER'] = limit.PIC_HW_VER
        # Restart required because of HW_VER setting
        dev.rla_reset.pulse(0.1)
        dev.bp35.action(None, delay=1.5, expected=2)  # Flush banner
        dev.bp35['UNLOCK'] = True
        mes.arm_swver.measure()
        dev.bp35.manual_mode()

    @teststep
    def _step_solar_reg(self, dev, sen, mes):
        """Test & Calibrate the Solar Regulator board."""
        self.fifo_push(((sen.vsreg, (13.0, 13.5)), ))
        for dat in (
                ('1.0', '0') +      # Solar alive, Vout OV
                ('0', ) * 3 +       # 2 x Solar VI, Vout OV
                ('0', '1') +        # Errorcode, Relay
                ('0', )             # SR Cal
            ):
            dev.bp35_puts(dat)

        tester.MeasureGroup((mes.arm_solar_alive, mes.arm_vout_ov, ))
        # The SR needs V & I set to zero after power up or it won't start.
        dev.bp35.solar_set(0, 0)
        # Now set the actual output settings
        dev.bp35.solar_set(limit.SOLAR_VSET, limit.SOLAR_ISET)
        time.sleep(2)           # Wait for the Solar to start & overshoot
        dev.bp35['VOUT_OV'] = 2   # Reset OVP Latch because the Solar overshot
        # Check that Solar Reg is error-free & the relay is ON
        tester.MeasureGroup((mes.arm_solar_error, mes.arm_solar_relay, ))
        vmeasured = mes.dmm_vsregpre.measure(timeout=5).reading1
        dev.bp35['SR_VCAL'] = vmeasured   # Calibrate voltage setpoint
        time.sleep(1)
        mes.dmm_vsregpost.measure(timeout=5)
        dev.dcs_sreg.output(0.0, output=False)

    @teststep
    def _step_aux(self, dev, sen, mes):
        """Apply Auxiliary input."""
        self.fifo_push(((sen.vbat, 13.5), ))
        for dat in ('', '13500', '350', ''):
            dev.bp35_puts(dat)

        dev.dcs_vaux.output(limit.VAUX_IN, output=True)
        dev.dcl_bat.output(0.5)
        dev.bp35['AUX_RELAY'] = True
        tester.MeasureGroup(
            (mes.dmm_vaux, mes.arm_auxv, mes.arm_auxi), timeout=5)
        dev.bp35['AUX_RELAY'] = False
        dev.dcs_vaux.output(0.0, output=False)
        dev.dcl_bat.output(0.0)

    @teststep
    def _step_powerup(self, dev, sen, mes):
        """Power-Up the Unit with 240Vac."""
        self.fifo_push(
            ((sen.acin, 240.0), (sen.pri12v, 12.5), (sen.o3v3, 3.3),
             (sen.o15Vs, 12.5), (sen.vbat, 12.8),
             (sen.vpfc, (415.0, 415.0), )))
        for dat in ('', ) * 4 + ('0', ) * 2:
            dev.bp35_puts(dat)

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

    @teststep
    def _step_output(self, dev, sen, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        self.fifo_push(((sen.vload, (0.0, ) + (12.8, ) * 14), ))
        for dat in ('', ) * (1 + 14 + 1):
            dev.bp35_puts(dat)

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

    @teststep
    def _step_remote_sw(self, dev, sen, mes):
        """Test Remote Load Isolator Switch."""
        self.fifo_push(((sen.vload, (0.25, 12.34)), ))

        dev.rla_loadsw.set_on()
        mes.dmm_vloadOff.measure(timeout=5)
        dev.rla_loadsw.set_off()
        mes.dmm_vload.measure(timeout=5)

    @teststep
    def _step_ocp(self, dev, sen, mes):
        """Test functions of the unit."""
        self.fifo_push(
            ((sen.fan, (0, 12.0)),
             (sen.vbat, 12.8), (sen.vbat, (12.8, ) * 6 + (11.0, ), ), ))
        if self.fifo:
            for sen in sen.arm_loads:
                sen.store(2.0)
        for dat in ('240', '50000', '350', '12800', '500', '', '4000'):
            dev.bp35_puts(dat)

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

    @teststep
    def _step_canbus(self, dev, sen, mes):
        """Test the Can Bus."""
        for dat in ('0x10000000', '', '0x10000000', '', ''):
            dev.bp35_puts(dat)
        dev.bp35_puts('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        mes.arm_can_bind.measure(timeout=10)
        dev.bp35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(limit.CAN_ECHO))
        dev.bp35['CAN'] = limit.CAN_ECHO
        echo_reply = dev.bp35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        sen.mir_can.store(echo_reply)
        mes.rx_can.measure()
