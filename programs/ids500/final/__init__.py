#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Final Test Program."""

from functools import wraps
import logging
import tester
import share
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
        dev.dcs_5v.output(5.0, True)
        dev.rla_enable.set_on()
        dev.dcs_tecvset.output(0.0, True)
        tester.MeasureGroup((mes.dmm_tecoff, mes.dmm_tecvmon0v), timeout=5)
        dev.dcl_tec.output(0.3)
        dev.dcs_tecvset.output(voltage=5.0, delay=0.1)
        Vset, Vmon, Vtec = tester.MeasureGroup(
            (mes.dmm_tecvset, mes.dmm_tecvmon, mes.dmm_tec), timeout=5).readings
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        sen.oMirTecErr.store(Vtec - (Vset * 3))
        mes.tecerr.measure(timeout=5)
        sen.oMirTecVmonErr.store(Vmon - (Vtec / 3))
        mes.tecvmonerr.measure(timeout=5)
        tester.MeasureGroup((mes.ui_YesNoPsu, mes.ui_YesNoTecGreen), timeout=5)
        dev.rla_tecphase.set_on()
        tester.MeasureGroup((mes.dmm_tecphase, mes.ui_YesNoTecRed), timeout=5)
        dev.rla_tecphase.set_off()

    @teststep
    def _step_ldd(self, dev, mes, sen):
        """Check LDdev.

           Check led status.
           Check voltages at 0A, 6A & 50A.

        """
        # Run LDD at 0A
        dev.dcs_isset.output(0.0, True)
        dev.rla_crowbar.set_on()
        dev.rla_interlock.set_on()
        dev.rla_enableis.set_on()
        tester.MeasureGroup(
            (mes.dmm_isvmon, mes.dmm_isout0v, mes.dmm_isiout0v), timeout=5)
        # Run LDD at 6A
        dev.dcs_isset.output(voltage=0.6, delay=1)
        mes.dmm_isvmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_isset06v, mes.dmm_isout06v, mes.dmm_isiout06v),
            timeout=5).readings
        self._ldd_err(Iset, Iout, Imon)
        # Run LDD at 50A
        mes.ui_YesNoLddGreen.measure(timeout=5)
        dev.dcs_isset.output(voltage=5.0, delay=1)
        mes.dmm_isvmon.measure(timeout=5)
        Iset, Iout, Imon = tester.MeasureGroup(
            (mes.dmm_isset5v, mes.dmm_isout5v, mes.dmm_isiout5v),
            timeout=5).readings
        for name in ('SetMonErr', 'SetOutErr', 'MonOutErr'):
            self.limits[name].limit = (-0.7, 0.7)
        self._ldd_err(Iset, Iout, Imon)
        # LDD off
        mes.ui_YesNoLddRed.measure(timeout=5)
        dev.dcs_isset.output(0.0, False)
        dev.rla_crowbar.set_off()
        dev.rla_interlock.set_off()
        dev.rla_enableis.set_off()

    def _ldd_err(self, Iset, Iout, Imon):
        """Check the accuracy between set and measured values for LDdev."""
        mes, sen = self.meas, self.sensor
        self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
        # Compare Set value to Mon
        sen.oMirIsErr.store((Iset * 10) - (Imon * 10))
        mes.setmonerr.measure()
        # Compare Set value to Out
        sen.oMirIsErr.store((Iset * 10) - (Iout * 1000))
        mes.setouterr.measure()
        # Compare Mon to Out
        sen.oMirIsErr.store((Imon * 10) - (Iout * 1000))
        mes.monouterr.measure()

    @teststep
    def _step_comms(self, dev, mes, sen):
        """Write HW version and serial number. Read back values."""
        dev.pic.open()
        dev.pic.clear_port()
        dev.pic.sw_test_mode()
        hwrev = mes.ui_hwrev.measure().reading1
        dev.pic.exp_cnt = 3
        dev.pic['WriteHwRev'] = hwrev
        dev.pic.exp_cnt = 1
        mes.pic_hwrev.testlimit[0].limit = hwrev
        mes.pic_hwrev.measure()
        sernum = share.get_sernum(
            self.uuts, self.limits['SerNum'], mes.ui_sernum)
        dev.pic.exp_cnt = 3
        dev.pic['WriteSerNum'] = sernum
        dev.pic.exp_cnt = 1
        mes.pic_sernum.testlimit[0].limit = sernum
        mes.pic_sernum.measure()
