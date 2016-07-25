#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initial Test Program for GENIUS-II and GENIUS-II-H."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA         # GENIUS-II limits
INI_LIMIT_H = limit.DATA_H      # GENIUS-II-H limits


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """GENIUS-II Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('Program', self._step_program, None, True),
            ('Aux', self._step_aux, None, True),
            ('PowerUp', self._step_powerup, None, True),
            ('VoutAdj', self._step_vout_adj, None, True),
            ('ShutDown', self._step_shutdown, None, True),
            ('OCP', self._step_ocp, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is a GENIUS-II-H if BattLoad current > 20A
        self._fullload = test_limits['MaxBattLoad'].limit
        self._isH = (self._fullload > 20)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global m, d, s, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_program(self):
        """Apply external dc, measure and program the board."""
        self.fifo_push(((s.olock, 0.0), (s.ovbatctl, 13.0), (s.ovdd, 5.0), ))
        d.dcs_vbatctl.output(13.0, True)
        tester.MeasureGroup((m.dmm_lock, m.dmm_vbatctl, m.dmm_vdd), timeout=5)
        if not self._fifo:
            d.program_pic.program()
        d.dcs_vbatctl.output(0.0, False)

    def _step_aux(self):
        """Apply external dc and measure."""
        self.fifo_push(((s.ovout, 13.65), (s.ovaux, 13.70), ))
        t.aux.run()

    def _step_powerup(self):
        """Check flying leads, apply 240Vac and measure voltages."""
        self.fifo_push(((s.oflyld, 30.0), (s.oacin, 240.0), (s.ovbus, 330.0),
                       (s.ovcc, 16.0), (s.ovbat, 13.0), (s.ovout, 13.0),
                       (s.ovdd, 5.0), (s.ovctl, 12.0), ))
        t.pwrup.run()

    def _step_vout_adj(self):
        """Vout adjustment.

         Adjust pot R39.
         Measure voltages.

         """

        self.fifo_push(((s.oAdjVout, True), (s.ovout, (13.65, 13.65, 13.65)),
                    (s.ovbatctl, 13.0), (s.ovbat, 13.65), (s.ovdd, 5.0), ))
        tester.MeasureGroup((m.ui_AdjVout, m.dmm_vout, m.dmm_vbatctl,
                            m.dmm_vbat, m.dmm_vdd, ),timeout=2)

    def _step_shutdown(self):
        """Shutdown."""

        self.fifo_push(((s.ovbat, 13.65), ))
        tester.MeasureGroup((m.dmm_vbat, ),timeout=5)

    def _step_ocp(self):
        """
        Ramp up load until OCP.

        Shutdown and recover.

        """
        self.fifo_push(((s.oVout, (13.5, ) * 11 + (13.0, ), ),
                        (s.oVout, (0.1, 13.6, 13.6)), (s.oVbat, 13.6)))
        d.dcl.output(0.0, output=True)
        d.dcl.binary(0.0, 32.0, 5.0)
        if self._isH:
            m.ramp_OCP_H.measure()
            t.shdnH.run()
        else:
            m.ramp_OCP.measure()
            t.shdn.run()
