#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Initial Test Program."""

import sys
import os
import inspect
import time
import subprocess
import logging
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """BatteryCheck Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PreProgram', self._step_pre_program),
            tester.TestStep('ProgramAVR', self._step_program_avr, not fifo),
            tester.TestStep('ProgramARM', self._step_program_arm, not fifo),
            tester.TestStep('InitialiseARM', self._step_initialise_arm),
            tester.TestStep('TestARM', self._step_test_arm),
            tester.TestStep('TestBlueTooth', self._step_test_bluetooth),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._sernum = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices, self.fifo)
        s = support.Sensors(d)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_pre_program(self):
        """Prepare for Programming.

        Set the Input DC voltage to 15V.
        Vbatt (12V Reg) is generated to power the unit.
        5V Reg and 12V Reg are generated to program the ATtiny10.

        """
        self.fifo_push(
            ((s.oSnEntry, ('A1509020010', )), (s.reg5V, 5.10),
             (s.reg12V, 12.00), (s.o3V3, 3.30), ))

        # Hold the ARM device in reset before power-on
        d.rla_reset.set_on()
        # Apply and check supply rails
        d.dcs_input.output(15.0, output=True)
        self._sernum = m.ui_SnEntry.measure().reading1
        tester.MeasureGroup((m.dmm_reg5V, m.dmm_reg12V, m.dmm_3V3), 2)

    def _step_program_avr(self):
        """Program the AVR ATtiny10 device."""
        d.rla_avr.set_on()
        time.sleep(2)   # Wait for the programmer to 'see' the 5V power
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        avr_cmd = [
            limit.AVRDUDE,
            '-P', 'usb',
            '-p', 't10',
            '-c', 'avrisp2',
            '-U', 'flash:w:' + limit.AVR_HEX,
            '-U', 'fuse:w:0xfe:m',
            ]
        try:
            console = subprocess.check_output(avr_cmd, cwd=folder)
            result = 0
            self._logger.debug(console)
        except subprocess.CalledProcessError:
            err_msg = '{} {}'.format(sys.exc_info()[0], sys.exc_info()[1])
            result = 1
            self._logger.warning(err_msg)
        d.rla_avr.set_off()
        s.oMirAVR.store(result)
        m.pgmAVR.measure()
        # Power cycle the unit to start the new code.
        d.dcs_input.output(output=False)
        time.sleep(1)
        d.dcs_input.output(output=True)

    def _step_program_arm(self):
        """Program the ARM device.

        The AVR will force the ARM into boot-loader mode 6.5sec
        after loss of the 5Hz heartbeat signal on BOOT.

        """
        d.rla_boot.set_on()
        d.rla_reset.set_off()
        self._logger.debug('Wait for AVR to bootload ARM...')
        time.sleep(6.5)
        d.rla_boot.set_off()
        d.rla_arm.set_on()      # Connect ARM programming port
        d.programmer.program()
        d.rla_arm.set_off()

    def _step_initialise_arm(self):
        """Initialise the ARM device."""
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) * 3
                ):
            d.arm_puts(str)

        d.arm.open()
        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        d.arm['UNLOCK'] = True
        d.arm['NVWRITE'] = True
        time.sleep(1.0)  # NVWRITE delay
        d.arm['SER_ID'] = self._sernum
        d.arm['NVWRITE'] = True
        time.sleep(1.0)  # NVWRITE delay

    def _step_test_arm(self):
        """Get data from the ARM device.

        Simulate and read back battery current from the ARM.
        Test the alarm relay.

        """
        self.fifo_push(
            ((s.relay, 5.0), (s.shunt, 62.5 / 1250), ))
        for str in (('-62000mA', ) +
                    ('', ) * 2 +
                    (limit.ARM_VERSION, ) +
                    ('12120', ) +
                    ('', )
                    ):
            d.arm_puts(str)

        d.dcs_shunt.output(62.5 * limit.SHUNT_SCALE, True)
        time.sleep(1.5)  # ARM rdgs settle
        batt_curr, curr_ARM = tester.MeasureGroup(
            (m.dmm_shunt, m.currARM), timeout=5).readings
        # Compare simulated battery current against ARM reading, in %
        percent_error = ((batt_curr - curr_ARM) / batt_curr) * 100
        s.oMirCurrErr.store(percent_error)
        # Disable alarm process so it won't switch the relay back
        d.arm['SYS_EN'] = 4
        d.arm['ALARM-RELAY'] = True
        tester.MeasureGroup((m.dmm_relay, m.currErr, m.softARM, m.voltARM))
        d.arm['ALARM-RELAY'] = False
        d.dcs_shunt.output(0.0, False)

    def _step_test_bluetooth(self):
        """Test the Bluetooth transmitter function.

        Scan for BT device and match against serial number.

        """
        d.bt_puts('OK', preflush=2)
        d.bt_puts('OK', preflush=1)
        d.bt_puts('OK', preflush=1)
        d.bt_puts('+RDDSRES=112233445566,BCheck A1509020010,2,3')
        d.bt_puts('+RDDSCNF=0')

        d.rla_reset.pulse_on(0.1)
        time.sleep(2.0)  # ARM startup delay
        self._logger.debug('Scan for Serial Number: "%s"', self._sernum)
        d.bt.open()
        reply = d.bt.scan(self._sernum)
        s.oMirBT.store(reply)
        m.BTscan.measure()
        d.bt.close()
