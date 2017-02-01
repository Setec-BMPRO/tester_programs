#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""J35 Initial Test Program."""

import tester
import share
from share import oldteststep
from . import support
from . import limit

INI_LIMIT_A = limit.DATA_A
INI_LIMIT_B = limit.DATA_B
INI_LIMIT_C = limit.DATA_C


class Initial(tester.TestSequence):     # pylint:disable=R0902

    """J35 Initial Test Program."""

    def __init__(self, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        super().__init__(None, fifo)
        self.phydev = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.teststep = None
        self.sernum = None
        self.variant = None

    def open(self):
        """Prepare for testing."""
        self.logdev = support.LogicalDevices(self.phydev, self.fifo)
        self.sensors = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensors, self.limits)
        self.teststep = support.SubTests(self.logdev, self.meas)
        self.variant = limit.VARIANT[self.limits['Variant'].limit]
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep(
                'ProgramARM', self.logdev.program_arm.program, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('Aux', self._step_aux),
            tester.TestStep(
                'Solar', self._step_solar, self.variant['SolarCan']),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('RemoteSw', self.teststep.remote_sw.run),
            tester.TestStep('Load', self._step_load),
            tester.TestStep('OCP', self.teststep.ocp.run),
            tester.TestStep(
                'CanBus', self._step_canbus, self.variant['SolarCan']),
            )
        super().open(sequence)
        # Power to fixture Comms circuits.
        self.logdev.dcs_vcom.output(9.0, True)

    def close(self):
        """Finished testing."""
        self.logdev.dcs_vcom.output(0, False)
        self.logdev = None
        self.sensors = None
        self.meas = None
        self.teststep = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switch.
        Apply power to the unit's Battery terminals to power up the micro.

        """
        mes.dmm_lock.measure(timeout=5)
        self.sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        # Apply DC Source to Battery terminals
        dev.dcs_vbat.output(12.6, True)
        tester.MeasureGroup(
            (mes.dmm_vbatin, mes.dmm_3v3u), timeout=5)

    @oldteststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Put device into manual control mode.

        """
        dev.j35.open()
        dev.j35.brand(self.variant['HwVer'], self.sernum, dev.rla_reset)
        dev.j35.manual_mode(True)   # Start the change to manual mode
        mes.arm_swver.measure()

    @oldteststep
    def _step_aux(self, dev, mes):
        """Test Auxiliary input."""
        dev.dcs_vaux.output(13.5, True)
        mes.dmm_vaux.measure(timeout=5)
        dev.dcl_bat.output(0.5, True)
        dev.j35['AUX_RELAY'] = True
        tester.MeasureGroup(
            (mes.dmm_vbatout, mes.arm_auxv, mes.arm_auxi), timeout=5)
        dev.j35['AUX_RELAY'] = False
        dev.dcs_vaux.output(0.0, False)
        dev.dcl_bat.output(0.0)

    @oldteststep
    def _step_solar(self, dev, mes):
        """Test Solar input."""
        dev.dcs_solar.output(13.5, True)
        dev.j35['SOLAR'] = True
        tester.MeasureGroup((mes.dmm_vbatout, mes.dmm_vair), timeout=5)
        dev.j35['SOLAR'] = False
        dev.dcs_solar.output(0.0, False)

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        dev.j35.manual_mode()     # Complete the change to manual mode
        if self.variant['Derate']:
            dev.j35.derate()      # Derate for lower output current
        dev.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (mes.dmm_acin, mes.dmm_vbus, mes.dmm_12vpri, mes.arm_vout_ov),
            timeout=5)
        dev.j35.dcdc_on()
        mes.dmm_vbat.measure(timeout=5)
        dev.dcs_vbat.output(0.0, False)
        tester.MeasureGroup(
            (mes.arm_vout_ov, mes.dmm_3v3, mes.dmm_15vs, mes.dmm_vbat,
             mes.dmm_fanOff, mes.arm_acv, mes.arm_acf, mes.arm_secT,
             mes.arm_vout, mes.arm_fan),
            timeout=5)
        dev.j35['FAN'] = 100
        mes.dmm_fanOn.measure(timeout=5)

    @oldteststep
    def _step_output(self, dev, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        dev.j35.load_set(set_on=True, loads=())   # All outputs OFF
        dev.dcl_out.output(1.0, True)  # A little load on the output
        mes.dmm_vloadoff.measure(timeout=2)
        for load in range(self.limits['LOAD_COUNT'].limit):  # One at a time ON
            with tester.PathName('L{0}'.format(load + 1)):
                dev.j35.load_set(set_on=True, loads=(load, ))
                mes.dmm_vload.measure(timeout=2)
        dev.j35.load_set(set_on=False, loads=())  # All outputs ON

    @oldteststep
    def _step_load(self, dev, mes):
        """Test with load."""
        dev.dcl_out.binary(1.0, self.limits['LOAD_CURRENT'].limit, 5.0)
        for load in range(self.limits['LOAD_COUNT'].limit):
            with tester.PathName('L{0}'.format(load + 1)):
                mes.arm_loads[load].measure(timeout=5)
        dev.dcl_bat.output(4.0, True)
        tester.MeasureGroup(
            (mes.dmm_vbatload, mes.arm_battI, ), timeout=5)

    @oldteststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        tester.MeasureGroup(
            (mes.dmm_canpwr, mes.arm_can_bind, ), timeout=10)
        dev.j35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        dev.j35['CAN'] = limit.CAN_ECHO
        echo_reply = dev.j35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self.sensors.mir_can.store(echo_reply)
        mes.rx_can.measure()
