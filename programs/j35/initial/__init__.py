#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Initial Test Program."""

import logging
import time

import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA

# These module level variables are to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """J35 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits
           @param fifo True if FIFOs are enabled

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('Prepare', self._step_prepare, None, True),
            ('ProgramARM', self._step_program_arm, None, not fifo),
            ('Initialise', self._step_initialise_arm, None, True),
            ('Aux', self._step_aux, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('Output', self._step_output, None, True),
            ('Load', self._step_load, None, True),
            ('OCP', self._step_ocp, None, True),
            ('CanBus', self._step_canbus, None, True),
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
        global d, s, m, t
        d = support.LogicalDevices(self._devices, self._fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)
        # Apply power to fixture (Comms & CN101) circuits.
        d.dcs_vcom.output(9.0, True)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global d, s, m, t
        # Remove power from fixture circuits.
        d.dcs_vcom.output(0, False)
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_prepare(self):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switch.
        Apply power to the unit's Battery terminals to power up the micro.

        """
        self.fifo_push(
            ((s.olock, 10.0), (s.ovbat, 12.0), (s.o3V3U, 3.3), (s.o3V3, 3.3),
             (s.sernum, ('A1626010123', )), ))

        m.dmm_lock.measure(timeout=5)
        self._sernum = m.ui_sernum.measure().reading1
        # Apply DC Sources to Battery terminals
        d.dcs_vbat.output(12.5, True)
        tester.MeasureGroup(
            (m.dmm_vbatin, m.dmm_3v3u, m.dmm_3v3), timeout=5)

    def _step_program_arm(self):
        """Program the ARM device.

        Device is powered by injected Battery voltage.

        """
        d.program_arm.program()

    def _step_initialise_arm(self):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Write Non-Volatile memory defaults.
        Put device into manual control mode.

        """
        self.fifo_push(((s.sernum, ('A1526040123', )), ))
        for dat in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) + ('success', ) * 2 + ('', ) * 2 +
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) +
                (limit.ARM_VERSION, ) +
                ('', ) + ('0x10000', ) + ('', ) * 3     # Manual mode
            ):
            d.j35_puts(dat)

        d.j35.open()
        d.rla_reset.pulse(0.1)
        d.j35.action(None, delay=1.5, expected=2)  # Flush banner
        d.j35['UNLOCK'] = True
        d.j35['HW_VER'] = limit.ARM_HW_VER
        d.j35['SER_ID'] = self._sernum
        d.j35['NVDEFAULT'] = True
        d.j35['NVWRITE'] = True
        # Restart required because of HW_VER setting
        d.rla_reset.pulse(0.1)
        d.j35.action(None, delay=1.5, expected=2)  # Flush banner
        d.j35['UNLOCK'] = True
        m.arm_swver.measure()
        d.j35.manual_mode()

    def _step_aux(self):
        """Test Auxiliary input."""
        self.fifo_push(((s.oaux, 12.8), (s.oair, 12.8), ))
        for dat in ('', '12500', '1100', ''):
            d.j35_puts(dat)

        d.dcs_vaux.output(12.8, True)
        d.dcs_vbat.output(0.0)
        d.dcl_bat.output(0.5)
        d.j35['AUX_RELAY'] = True
        tester.MeasureGroup((m.dmm_vaux, m.dmm_vair, m.arm_auxv,
                                m.arm_auxi), timeout=5)
        d.j35['AUX_RELAY'] = False
        d.dcs_vbat.output(12.5)
        d.dcs_vaux.output(0.0, False)
        d.dcl_bat.output(0.0)

    def _step_powerup(self):
        """Power-Up the Unit with 240Vac.

        Test functions of the unit.

        """
        self.fifo_push(
            ((s.oacin, 240.0), (s.ovbus, 340.0), (s.o12Vpri, 12.5),
            (s.o3V3, 3.3), (s.o15Vs, 12.5), (s.ovout, 12.8), (s.ovbat, 12.8),
            (s.ofan, (0, 12.0)), ))
        for dat in ('', ) * 3 + ('0', ) * 2:
            d.j35_puts(dat)
        for dat in ('240', '50000', '350', '12800', '500', '', ):
            d.j35_puts(dat)

        # Apply 240Vac & check
        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup((m.dmm_acin, m.dmm_vbus, m.dmm_12vpri), timeout=10)
        # Enable DCDC converters
        d.j35.power_on()
        m.arm_vout_ov.measure()
        # Remove injected Battery voltage
        d.dcs_vbat.output(0.0, False)
        d.dcl_bat.output(0.5, True)
        time.sleep(0.5)
        d.dcl_bat.output(0.0, False)
        # Is it now running on it's own?
        m.arm_vout_ov.measure()
        tester.MeasureGroup((m.dmm_3v3, m.dmm_15vs, m.dmm_vout, m.dmm_vbat,
                            m.dmm_fanOff, m.arm_acv, m.arm_acf, m.arm_secT,
                            m.arm_vout,
                            m.arm_fan), timeout=10)
        d.j35['FAN'] = 100
        m.dmm_fanOn.measure(timeout=5)

    def _step_output(self):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.
        Test Remote switch.

        """
        self.fifo_push(((s.ovload, (0.0, ) + (12.8, ) * 14),
                        (s.ovload, (0.25, 12.34)), ))
        for dat in ('', ) * (1 + 14 + 1):
            d.j35_puts(dat)

        # All outputs OFF
        d.j35.load_set(set_on=True, loads=())
        # A little load on the output
        d.dcl_out.output(1.0, True)
        m.dmm_vloadoff.measure(timeout=2)
        # One at a time ON
        for load in range(14):
            tester.testsequence.path_push('L{}'.format(load + 1))
            d.j35.load_set(set_on=True, loads=(load, ))
            m.dmm_vload.measure(timeout=2)
            tester.testsequence.path_pop()
        # All outputs ON
        d.j35.load_set(set_on=False, loads=())
        # Test Remote switch
        t.rem_sw.run()

    def _step_load(self):
        """Test with load."""
        self.fifo_push(((s.ovbat, 12.8), ))
        d.j35_puts('4000')
        if self._fifo:
            for sen in s.arm_loads:
                sen.store(2.0)

        d.dcl_out.binary(1.0, 28.0, 5.0)
        d.dcl_bat.output(4.0, output=True)
        tester.MeasureGroup((m.dmm_vbat, m.arm_battI, ), timeout=5)
        for load in range(14):
            tester.testsequence.path_push('L{}'.format(load + 1))
            m.arm_loads[load].measure(timeout=5)
            tester.testsequence.path_pop()

    def _step_ocp(self):
        """Test OCP."""
        self.fifo_push(((s.ovbat, (12.8, ) * 7 + (11.0, ), ), ))
        m.ramp_ocp.measure(timeout=5)
        d.dcl_bat.output(0.0)

    def _step_canbus(self):
        """Test the Can Bus."""
        for dat in ('0x10000000', '', '0x10000000', '', ''):
            d.j35_puts(dat)
        d.j35_puts('RRQ,36,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.arm_can_bind.measure(timeout=10)
        d.j35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(limit.CAN_ECHO))
        d.j35['CAN'] = limit.CAN_ECHO
        echo_reply = d.j35_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.mir_can.store(echo_reply)
        m.rx_can.measure()
