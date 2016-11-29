#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Final Test Program."""

from functools import wraps
import logging
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

def teststep(func):
    """Decorator to add arguments to the test step calls."""
    @wraps(func)
    def new_func(self):
        return func(self, self.logdev, self.meas, self.sensor)
    return new_func


class Final(tester.TestSequence):

    """IDS-500 Final Test Programes."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        super().__init__(selection, None, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.phydev = physical_devices
        self.limits = test_limits
        self.logdev = None
        self.sensor = None
        self.meas = None
        self.subtest = None

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self.logdev = support.LogicalDevices(self.phydev, self.fifo)
        self.sensor = support.Sensors(self.logdev, self.limits)
        self.meas = support.Measurements(self.sensor, self.limits)
        self.subtest = support.SubTests(self.logdev, self.meas)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self.subtest.pwr_up.run),
            tester.TestStep('KeySw1', self.subtest.key_sw1.run),
            tester.TestStep('KeySw12', self.subtest.key_sw12.run),
            tester.TestStep('TEC', self._step_tec),
            tester.TestStep('LDD', self._step_ldd),
            tester.TestStep('OCP', self.subtest.ocp.run),
            tester.TestStep('Comms', self._step_comms),
            tester.TestStep('EmergStop', self.subtest.emg_stop.run),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self.logdev.reset()

    @teststep
    def _step_tec(self, dev, mes, sen):
        """Check TEC."""
        dev.dcs_5V.output(5.0, True)
        dev.rla_Enable.set_on()
        dev.dcs_TecVset.output(0.0, True)
        tester.MeasureGroup((mes.dmm_TecOff, mes.dmm_TecVmon0V), timeout=5)
        dev.dcl_Tec.output(0.3)
        dev.dcs_TecVset.output(voltage=5.0, delay=0.1)
        Vset, Vmon, Vtec = tester.MeasureGroup(
            (mes.dmm_TecVset, mes.dmm_TecVmon, mes.dmm_Tec), timeout=5).readings
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        sen.oMirTecErr.store(Vtec - (Vset * 3))
        mes.TecErr.measure(timeout=5)
        sen.oMirTecVmonErr.store(Vmon - (Vtec / 3))
        mes.TecVmonErr.measure(timeout=5)
        tester.MeasureGroup((mes.ui_YesNoPsu, mes.ui_YesNoTecGreen), timeout=5)
        dev.rla_TecPhase.set_on()
        tester.MeasureGroup((mes.dmm_TecPhase, mes.ui_YesNoTecRed), timeout=5)
        dev.rla_TecPhase.set_off()

    @teststep
    def _step_ldd(self, dev, mes, sen):
        """Check LDdev.

           Check led status.
           Check voltages at 0A, 6A & 50A.

        """
        # Run LDD at 0A
        dev.dcs_IsSet.output(0.0, True)
        dev.rla_Crowbar.set_on()
        dev.rla_Interlock.set_on()
        dev.rla_EnableIs.set_on()
        tester.MeasureGroup(
            (mes.dmm_IsVmon, mes.dmm_IsOut0V, mes.dmm_IsIout0V), timeout=5)
        # Run LDD at 6A
        dev.dcs_IsSet.output(voltage=0.6, delay=1)
        mes.dmm_IsVmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_IsSet06V, mes.dmm_IsOut06V, mes.dmm_IsIout06V),
            timeout=5).readings
        self._ldd_err(Iset, Iout, Imon)
        # Run LDD at 50A
        mes.ui_YesNoLddGreen.measure(timeout=5)
        dev.dcs_IsSet.output(voltage=5.0, delay=1)
        mes.dmm_IsVmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_IsSet5V, mes.dmm_IsOut5V, mes.dmm_IsIout5V),
            timeout=5).readings
        for name in ('SetMonErr', 'SetOutErr', 'MonOutErr'):
            self.limits[name].limit = (-0.7, 0.7)
        self._ldd_err(Iset, Iout, Imon)
        # LDD off
        mes.ui_YesNoLddRed.measure(timeout=5)
        dev.dcs_IsSet.output(0.0, False)
        dev.rla_Crowbar.set_off()
        dev.rla_Interlock.set_off()
        dev.rla_EnableIs.set_off()

    def _ldd_err(self, Iset, Iout, Imon):
        """Check the accuracy between set and measured values for LDdev."""
        mes, sen = self.meas, self.sensor
        self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
        # Compare Set value to Mon
        sen.oMirIsErr.store((Iset * 10) - (Imon * 10))
        mes.SetMonErr.measure()
        # Compare Set value to Out
        sen.oMirIsErr.store((Iset * 10) - (Iout * 1000))
        mes.SetOutErr.measure()
        # Compare Mon to Out
        sen.oMirIsErr.store((Imon * 10) - (Iout * 1000))
        mes.MonOutErr.measure()

    @teststep
    def _step_comms(self, dev, mes, sen):
        """Write HW version and serial number. Read back values."""
        dev.pic.open()
        dev.pic.clear_port()
        dev.pic.sw_test_mode()
        dev.pic['HwRev'] = limit.HW_REV
        dev.pic.clear_port()
        self.limits['HwRev'].limit = limit.HW_REV
        mes.pic_hwrev.measure()
        sernum = mes.ui_SerEntry.measure().reading1
        dev.pic['SerNum'] = sernum
        dev.pic.clear_port()
        self.limits['SerChk'].limit = sernum
        mes.pic_serchk.measure()
