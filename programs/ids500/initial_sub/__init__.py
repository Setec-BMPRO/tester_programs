#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Test Program."""

import logging

import tester
from . import support
from . import limit

INI_MIC_LIMIT = limit.DATA_MIC
INI_AUX_LIMIT = limit.DATA_AUX
INI_BIAS_LIMIT = limit.DATA_BIAS
INI_BUS_LIMIT = limit.DATA_BUS
INI_SYN_LIMIT = limit.DATA_SYN


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class _Main(tester.TestSequence):

    """IDS-500 Base Subboard Test Program."""

    def __init__(self, selection, sequence, fifo):
        """Common test program segments.

           @param selection Product test program
           @param sequence Test sequence
           @param fifo True to enable FIFOs

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        super().__init__(selection, sequence, fifo)

    def close(self):
        """Finished testing."""
        self._logger.info('BaseClose')
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()


class InitialMicro(_Main):

    """IDS-500 Initial Micro Test Program."""

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
        sequence = (
            ('Program', self._step_program, None, True),
            ('Comms', self._step_comms, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        global d, m, s
        d = support.LogicalDevMicro(self._devices, self._fifo)
        s = support.SensorMicro(d, self._limits)
        m = support.MeasureMicro(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def _step_program(self):
        """Apply Vcc and program the board."""
        self.fifo_push(((s.oVsec5VuP, 5.0), ))
        d.dcs_vcc.output(5.0, True)
        m.dmm_vsec5VuP.measure(timeout=5)
        if not self._fifo:
            d.program_picMic.program()

    def _step_comms(self):
        """Communicate with the PIC console."""
        for str in (
                ('I, 1, 2,Software Revision', ) +
                ('D, 16, 25,MICRO Temp.(C)', )
                ):
            d.pic_puts(str)
# FIXME: Console requires return + line feed. Override write/read functions.
        m.swrev.measure().reading1
        m.microtemp.measure().reading1


class InitialAux(_Main):

    """IDS-500 Initial Aux Test Program."""

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
        sequence = (
            ('PowerUp', self._step_pwrup, None, True),
            ('KeySwitch', self._step_key_switches12, None, True),
            ('ACurrent', self._step_acurrent, None, True),
            ('OCP', self._step_ocp, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        global d, m, s, t
        d = support.LogicalDevAux(self._devices, self._fifo)
        s = support.SensorAux(d, self._limits)
        m = support.MeasureAux(s, self._limits)
        t = support.SubTestAux(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def _step_pwrup(self):
        """Check Fixture Lock, apply 240Vac and measure voltages."""
        self.fifo_push(
            ((s.olock, 0.0), (s.o20VL, 21.0), (s.o_20V, -21.0), (s.o5V, 0.0),
             (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 0.0),
             (s.o15VpSw, 0.0), (s.oPwrGood, 0.0), ))
        t.pwrup.run()

    def _step_key_switches12(self):
        """Apply 5V to ENABLE_Aux, ENABLE +15VPSW and measure voltages."""
        self.fifo_push(
            ((s.o5V, 5.0), (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
             (s.o15VpSw, (0.0, 15.0)), (s.oPwrGood, 5.0), ))
        t.key_sws.run()

    def _step_acurrent(self):
        """Test ACurrent: No load, 5V load, 5V load + 15Vp load """
        self.fifo_push(
            ((s.oACurr5V, (0.0, 2.0, 2.0)), (s.oACurr15V, (0.1, 0.1, 1.3)), ))
        t.acurr.run()

    def _step_ocp(self):
        """Measure OCP and voltage a/c R657 with 5V applied via a 100k."""
        self.fifo_push(((s.o5V, (5.0, ) * 20 + (4.7, ), ),
                (s.o15Vp, (15.0, ) * 30 + (14.1, ), ), (s.oAuxTemp, 3.5)))
        t.ocp.run()


class InitialBias(_Main):

    """IDS-500 Initial Bias Test Program."""

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
        sequence = (
            ('PowerUp', self._step_pwrup, None, True),
            ('OCP', self._step_ocp, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        global d, m, s
        d = support.LogicalDevBias(self._devices, self._fifo)
        s = support.SensorBias(d, self._limits)
        m = support.MeasureBias(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def _step_pwrup(self):
        """Check Fixture Lock, apply 240Vac and measure voltages."""
        self.fifo_push(((s.olock, 0.0), (s.o400V, 400.0), (s.oPVcc, 14.0), ))
        m.dmm_lock.measure(timeout=5)
        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup((m.dmm_400V, m.dmm_pvcc, ),timeout=5)

    def _step_ocp(self):
        """Measure OCP."""
        self.fifo_push(((s.o12Vsbraw, (13.0, ) * 4 + (12.5, 0.0), ), ))
        tester.MeasureGroup(
                (m.dmm_12Vsbraw, m.ramp_OCP, m.dmm_12Vsbraw2,),timeout=1)


class InitialBus(_Main):

    """IDS-500 Initial Bus Test Program."""

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
        sequence = (
            ('PowerUp', self._step_pwrup, None, True),
            ('TecLddStartup', self._step_tec_ldd, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        global d, m, s, t
        d = support.LogicalDevBus(self._devices, self._fifo)
        s = support.SensorBus(d, self._limits)
        m = support.MeasureBus(s, self._limits)
        t = support.SubTestBus(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def _step_pwrup(self):
        """Check Fixture Lock, apply 240Vac and measure voltage."""
        self.fifo_push(((s.olock, 0.0), (s.o400V, 400.0), ))
        t.pwrup.run()

    def _step_tec_ldd(self):
        """ """
        self.fifo_push(
                ((s.o20VT, (23, 23, 22, 19)), (s.o9V, (11, 10, 10, 11 )),
                (s.o20VL, (23, 23, 21, 23)), (s.o_20V, (-23, -23, -21, -23)),))
        t.tl_startup.run()


class InitialSyn(_Main):

    """IDS-500 Initial SynBuck Test Program."""

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
        sequence = (
            ('Program', self._step_program, None, True),
            ('PowerUp', self._step_pwrup, None, True),
            ('TecEnable', self._step_tec_enable, None, True),
            ('TecReverse', self._step_tec_rev, None, True),
            ('LddEnable', self._step_ldd_enable, None, True),
            ('ISSetAdj', self._step_ISset_adj, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        super().open()
        self._logger.info('Open')
        global d, m, s, t
        d = support.LogicalDevSyn(self._devices, self._fifo)
        s = support.SensorSyn(d, self._limits)
        m = support.MeasureSyn(s, self._limits)
        t = support.SubTestSyn(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def _step_program(self):
        """Check Fixture Lock, apply Vcc and program the board."""
        self.fifo_push(((s.olock, 0.0), ))
        m.dmm_lock.measure(timeout=5)
        d.dcs_vsec5Vlddtec.output(5.0, True)
        if not self._fifo:
            d.program_picSyn.program()

    def _step_pwrup(self):
        """Apply 240Vac and measure voltages."""
        self.fifo_push(
            ((s.o20VT, 20.0), (s.o_20V, -20.0), (s.o9V, 9.0), (s.oTec, 0.0),
            (s.oLdd, 0.0), (s.oLddVmon, 0.0), (s.oLddImon, 0.0),
            (s.oTecVmon, 0.0), (s.oTecVset, 0.0), ))
        t.pwrup.run()

    def _step_tec_enable(self):
        """Enable TEC, set dc input and measure voltages."""
        self.fifo_push(
            ((s.oTecVmon, (0.5, 2.5, 5.0)), (s.oTec, (0.5, 7.5, 15.0)), ))
        t.tec_en.run()

    def _step_tec_rev(self):
        """Reverse TEC and measure voltages."""
        self.fifo_push(((s.oTecVmon, (5.0,) * 2), (s.oTec, (-15.0, 15.0)), ))
        t.tec_rv.run()

    def _step_ldd_enable(self):
        """Enable LDD, set dc input and measure voltages."""
        self.fifo_push(
            ((s.oLdd, (0.0, 0.65, 1.3)), (s.oLddShunt, (0.0, 0.006, 0.05)),
            (s.oLddImon, (0.0, 0.6, 5.0)), ))
        t.ldd_en.run()

    def _step_ISset_adj(self):
        """Set LDD current and adjust for accuracy of output."""
        # To test adjuster, add delay to Adj sensor and make NoDelays False.
        self.fifo_push(((s.oLddIset, 5.01),
                    (s.oAdjLdd, True),
                    (s.oLddShunt, (0.0495, 0.0495, 0.05005)), ))
        d.dcs_lddiset.output(5.0, True)
        setI = m.dmm_ISIset5V.measure(timeout=5).reading1 * 10
        lo_lim = setI - (setI * 0.2/100)
        hi_lim = setI + (setI * 0.2/100)
        self._limits['AdjLimits'].limit = (lo_lim, hi_lim)
        tester.MeasureGroup((m.dmm_ISIout50A, m.ui_AdjLdd,
                                    m.dmm_ISIoutPost, ),timeout=2)
