#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Test Program."""

import logging

import share
import tester
from . import support
from . import limit

INI_SUB_LIMIT = limit.DATA


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class InitialSub(tester.TestSequence):

    """IDS-500 Initial Subboard Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
# FIXME: Make a class for each PCB - Like in the CMRSBP program
        _isMicro, _isSyn, _isAux, _isBias, _isBus = {
            'IDS500 Initial Micro':   (True,  False, False, False, False),
            'IDS500 Initial Synbuck': (False,  True, False, False, False),
            'IDS500 Initial Aux':     (False,  False, True, False, False),
            'IDS500 Initial Bias':    (False,  False, False, True, False),
            'IDS500 Initial Bus':     (False,  False, False, False, True),
            }[selection.name]
        self._logger.debug(
            'Initial TestType: Micro %s, Synbuck %s, Aux %s,'
            ' Bias %s, Bus %s',
            _isMicro, _isSyn, _isAux, _isBias, _isBus)
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_pwrup_micro, None, _isMicro),
            ('PowerUp', self._step_pwrup_aux, None, _isAux),
            ('KeySw1', self._step_key_switch1, None, _isAux),
            ('Program', self._step_program, None, _isMicro),
            ('Comms', self._step_comms, None, _isMicro),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global d, s, m, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_pwrup_micro(self):
        """Apply input DC and measure."""
        self.fifo_push(((s.oVsec5VuP, 5.0), ))

        t.pwrup_micro.run()

    def _step_program(self):
        """Program the PIC micro."""
        self._logger.info('Start PIC programmer')
        d.rla_Prog.set_on()
        pic = share.ProgramPIC(
            hexfile=limit.PIC_HEX,
            working_dir=limit.HEX_DIR,
            device_type='18F4520',
            sensor=s.oMirPIC, fifo=self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        m.pgmPIC.measure()

    def _step_comms(self):
        """Communicate with the PIC console."""
        if self._fifo:
            d.pic_ser.put(b'I, 1, 2,Software Revision\r\n')
            d.pic_ser.put(b'D, 16, 25,MICRO Temp.(C)\r\n')

        m.pic_SwRev.measure()
        m.pic_MicroTemp.measure()

    def _step_pwrup_aux(self):
        """Apply input DC and measure."""
        self.fifo_push(
            ((s.o20VL, 21.0), (s.o_20V, -21.0), (s.o5V, 0.0),(s.o15V, 15.0),
             (s.o_15V, -15.0), (s.o15Vp, 0.0), (s.o15VpSw, 0.0),
             (s.oPwrGood, 0.0), ))

        t.pwrup_aux.run()

    def _step_key_switch1(self):
        """Turn on KeySw1 and measure voltages."""
        self.fifo_push(
            ((s.o5V, 5.0), (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
             (s.o15VpSw, 0.0), (s.oPwrGood, 5.0), ))

        t.key_sw1.run()
