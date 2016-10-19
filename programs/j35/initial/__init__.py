#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Initial Test Program."""

import tester
import share
from . import support
from . import limit

INI_LIMIT = limit.DATA


class Initial(tester.TestSequence):     # pylint:disable=R0902

    """J35 Initial Test Program."""

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
            tester.TestStep('ProgramARM', self._step_program_arm, not fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('Aux', self._step_aux),
            tester.TestStep('Solar', self._step_solar),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('RemoteSw', self._step_remote_sw),
            tester.TestStep('Load', self._step_load),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('CanBus', self._step_canbus),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self.phydev = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.teststep = None
        self.sernum = None
        self.j35 = None

    def open(self):
        """Prepare for testing."""
        self.logdev = support.LogicalDevices(self.phydev, self.fifo)
        self.j35 = self.logdev.j35
        self.sensors = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensors, self.limits)
        self.teststep = support.SubTests(self.logdev, self.meas)
        # Power to fixture Comms circuits.
        self.logdev.dcs_vcom.output(9.0, True)

    def close(self):
        """Finished testing."""
        self.logdev.dcs_vcom.output(0, False)
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.teststep = None
        self.j35 = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    def _step_prepare(self):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switch.
        Apply power to the unit's Battery terminals to power up the micro.

        """
        dev, mes = self.logdev, self.meas
        mes.dmm_lock.measure(timeout=5)
        self._sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        # Apply DC Source to Battery terminals
        dev.dcs_vbat.output(12.6, True)
        tester.MeasureGroup(
            (mes.dmm_vbatin, mes.dmm_vair, mes.dmm_3v3u), timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        self.logdev.program_arm.program()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Put device into manual control mode.

        """
        self.j35.open()
        self.j35.brand(limit.ARM_HW_VER, self.sernum, self.logdev.rla_reset)
        self.j35.manual_mode(True)     # Start the change to manual mode
        self.meas.arm_swver.measure()

    def _step_aux(self):
        """Test Auxiliary input."""
        dev, mes = self.logdev, self.meas
        dev.dcs_vaux.output(13.5, True)
        mes.dmm_vaux.measure(timeout=5)
        dev.dcl_bat.output(0.5, True)
        self.j35['AUX_RELAY'] = True
        tester.MeasureGroup(
            (mes.dmm_vbatout, mes.arm_auxv, mes.arm_auxi), timeout=5)
        self.j35['AUX_RELAY'] = False
        dev.dcs_vaux.output(0.0, False)
        dev.dcl_bat.output(0.0)

    def _step_solar(self):
        """Test Solar input."""
        dev, mes = self.logdev, self.meas
        dev.dcs_solar.output(13.5, True)
        self.j35['SOLAR'] = True
        tester.MeasureGroup((mes.dmm_vbatout, ), timeout=5)
        self.j35['SOLAR'] = False
        dev.dcs_solar.output(0.0, False)

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac."""
        dev, mes = self.logdev, self.meas
        self.j35.manual_mode()     # Complete the change to manual mode
        dev.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (mes.dmm_acin, mes.dmm_vbus, mes.dmm_12vpri, mes.arm_vout_ov),
            timeout=5)
        self.j35.dcdc_on()
        mes.dmm_vbat.measure(timeout=5)
        dev.dcs_vbat.output(0.0, False)
        tester.MeasureGroup(
            (mes.arm_vout_ov, mes.dmm_3v3, mes.dmm_15vs, mes.dmm_vbat,
             mes.dmm_fanOn, mes.arm_acv, mes.arm_acf, mes.arm_secT,
             mes.arm_vout, mes.arm_fan),
            timeout=5)
        mes.dmm_fanOff.measure(timeout=10)
        self.j35['FAN'] = 100
        mes.dmm_fanOn.measure(timeout=5)

    def _step_output(self):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        dev, mes = self.logdev, self.meas
        self.j35.load_set(set_on=True, loads=())   # All outputs OFF
        dev.dcl_out.output(1.0, True)  # A little load on the output
        mes.dmm_vloadoff.measure(timeout=2)
        for load in range(limit.LOAD_COUNT):  # One at a time ON
            with tester.PathName('L{0}'.format(load + 1)):
                self.j35.load_set(set_on=True, loads=(load, ))
                mes.dmm_vload.measure(timeout=2)
        self.j35.load_set(set_on=False, loads=())  # All outputs ON

    def _step_remote_sw(self):
        """Test Remote switch."""
        self.teststep.remote_sw.run()

    def _step_load(self):
        """Test with load."""
        dev, mes = self.logdev, self.meas
        dev.dcl_out.binary(1.0, limit.LOAD_CURRENT, 5.0)
        for load in range(limit.LOAD_COUNT):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.arm_loads[load].measure(timeout=5)
        dev.dcl_bat.output(4.0, True)
        tester.MeasureGroup(
            (mes.dmm_vbat, mes.arm_battI, ), timeout=5)

    def _step_ocp(self):
        """Test OCP."""
        self.teststep.ocp.run()

    def _step_canbus(self):
        """Test the Can Bus."""
        dev, mes = self.logdev, self.meas
        tester.MeasureGroup(
            (mes.dmm_canpwr, mes.arm_can_bind, ), timeout=10)
        self.j35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self.j35['CAN'] = limit.CAN_ECHO
        echo_reply = dev.j35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self.sensors.mir_can.store(echo_reply)
        mes.rx_can.measure()
