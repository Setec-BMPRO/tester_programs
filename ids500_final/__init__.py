#!/usr/bin/env python3
"""IDS-500 Final Test Program."""

import os
import logging
import time
import serial
import queue
import threading

import tester
from . import support
from . import limit
import share.ids500

MeasureGroup = tester.measure.group


LIMIT_DATA = limit.DATA

# Serial port for the PIC.
_PIC_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'COM1',
             }[os.name]

_NEW_PSU  =  False

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class MockSerial():

    """Simulated serial port for testing."""

    def __init__(self, port=None, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1, timeout=None, xonxoff=False, rtscts=False,
                 writeTimeout=None, dsrdtr=False, interCharTimeout=None):
        """Create internal data storage queue."""
        # Queue to hold data to be read by read()
        self.in_queue = queue.Queue()
        # Queue to hold data written by write()
        self.out_queue = queue.Queue()
        # Control of read() enable
        self._enable = threading.Event()
        self._enable.set()

    def put(self, data):
        """Put data into the read-back queue."""
        self.in_queue.put(data)

    def get(self):
        """Get data from the written-out queue."""
        if not self.out_queue.empty():
            data = self.out_queue.get()
        else:
            data = b''
        return data

    def flush(self):
        """Flush both input and output queues."""
        self.flushInput()
        self.flushOutput()

    def flushInput(self):
        """Flush input queue."""
        while not self.in_queue.empty():
            self.in_queue.get()

    def flushOutput(self):
        """Flush output queue."""
        while not self.out_queue.empty():
            self.out_queue.get()

    def enable(self):
        """Enable reading of the read-back queue."""
        self._enable.set()

    def disable(self):
        """Disable reading of the read-back queue."""
        self._enable.clear()

    def read(self, size=1):
        """A non-blocking read.

        @return bytes.

        """
# FIXME: Honour the size argument
        if self._enable.is_set() and not self.in_queue.empty():
            data = self.in_queue.get()
        else:
# FIXME: Should we use the timeout from the call to __init__() ?
            time.sleep(0.1)
            data = b''
        return data

    def write(self, data):
        """Write data bytes to the written-out queue."""
        self.out_queue.put(data)


class Main(tester.TestSequence):

    """IDS-500 Final Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('KeySw1', self._step_key_switch1, None, True),
            ('KeySw12', self._step_key_switch12, None, True),
            ('TEC', self._step_tec, None, True),
            ('LDD', self._step_ldd, None, True),
            ('OCP', self._step_ocp, None, True),
            ('Comms', self._step_comms, None, True),
            ('EmergStop', self._step_emerg_stop, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._HW = {'IDS500-FIN-06A': '06A'}[selection.name]
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        if self._fifo:
            self._pic_ser = MockSerial()
        else:
            self._pic_ser = serial.Serial(port=_PIC_PORT,
                                          baudrate=19200, timeout=0.1)
        self._picdev = share.ids500.Console(self._pic_ser)
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits, self._picdev)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._pic_ser.close()
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Set min loads, apply input AC and measure voltages."""
        self.fifo_push(
            ((s.Tec, 0.0), (s.TecVmon, 0.0), (s.Ldd, 0.0), (s.IsVmon, 0.0),
             (s.o15V, 0.0), (s.o_15V, 0.0), (s.o15Vp, 0.0), (s.o15VpSw, 0.0),
             (s.o5V, 0.0), ))
        t.pwr_up.run()

    def _step_key_switch1(self):
        """Turn on KeySw1 and measure voltages."""
        self.fifo_push(
            ((s.Tec, 0.0), (s.TecVmon, 0.0), (s.Ldd, 0.0), (s.IsVmon, 0.0),
             (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
             (s.o15VpSw, 0.0), (s.o5V, 5.0), ))
        t.key_sw1.run()

    def _step_key_switch12(self):
        """With KeySw1 on, turn on KeySw2 and measure voltages."""
        self.fifo_push(
            ((s.Tec, 0.0), (s.TecVmon, 0.0), (s.Ldd, 0.0), (s.IsVmon, 0.0),
             (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
             (s.o15VpSw, 15.0), (s.o5V, 5.0), ))
        t.key_sw12.run()

    def _step_tec(self):
        """Check TEC.

           Check led status.
           Check voltages.

        """
        self.fifo_push(
            ((s.TecVset, 5.05), (s.TecVmon, (0.0, 4.99)),
             (s.Tec, (0.0, 15.0, -15.0)), (s.oYesNoPsu, True),
             (s.oYesNoTecGreen, True), (s.oYesNoTecRed, True), ))
        t.tec_pre.run()
        Vset, Vmon, Vtec = MeasureGroup(
            (m.dmm_TecVset, m.dmm_TecVmon, m.dmm_Tec), timeout=5)[1]
        self._logger.debug('Vset:%s, Vmon:%s, Vtec:%s', Vset, Vmon, Vtec)
        s.oMirTecErr.store(Vtec - (Vset * 3))
        m.TecErr.measure()
        s.oMirTecVmonErr.store(Vmon - (Vtec / 3))
        m.TecVmonErr.measure()
        t.tec_post.run()

    def _step_ldd(self):
        """Check LDD.

           Check led status.
           Check voltages at 0A, 6A & 50A.

        """
        self.fifo_push(
            ((s.IsVmon, (2.0,) * 3), (s.IsSet, (0.6, 5.0)),
             (s.IsIout, (0.0, 0.601, 5.01)), (s.IsOut, (0.0, 0.00602, 0.0502)),
             (s.oYesNoLddGreen, True), (s.oYesNoLddRed, True), ))
        t.ldd_06V.run()
        Iset, Iout, Imon = MeasureGroup(
            (m.dmm_IsSet06V, m.dmm_IsOut06V, m.dmm_IsIout06V), timeout=5)[1]
        self._ldd_err(Iset, Iout, Imon)
        t.ldd_5V.run()
        Iset, Iout, Imon = MeasureGroup(
            (m.dmm_IsSet5V, m.dmm_IsOut5V, m.dmm_IsIout5V), timeout=5)[1]
        for name in ('SetMonErr', 'SetOutErr', 'MonOutErr'):
            self._limits[name].limit = (-0.7, 0.7)
        self._ldd_err(Iset, Iout, Imon)
        t.ldd_off.run()

    def _ldd_err(self, Iset, Iout, Imon):
        """Check the accuracy between set and measured values for LDD."""
        self._logger.debug('Iset:%s, Iout:%s, Imon:%s', Iset, Iout, Imon)
        # Compare Set value to Mon
        s.oMirIsErr.store((Iset * 10) - (Imon * 10))
        m.SetMonErr.measure()
        # Compare Set value to Out
        s.oMirIsErr.store((Iset * 10) - (Iout * 1000))
        m.SetOutErr.measure()
        # Compare Mon to Out
        s.oMirIsErr.store((Imon * 10) - (Iout * 1000))
        m.MonOutErr.measure()

    def _step_ocp(self):
        """Measure OCP points."""
        self.fifo_push(
            ((s.o5V, (5.0, ) * 21 + (3.9,), ),
             (s.o15Vp, (15.0, ) * 21 + (11.9,), ),
             (s.o15VpSw, (15.0, ) * 21 + (11.9,), ),
             (s.Tec, (15.0, ) * 21 + (11.9,), ),
             (s.o15Vp, (15.0,) * 3), ))
        _subtests = (t.ocp_5V, t.ocp_15Vp, t.ocp_15VpSw, t.ocp_tec)
        for sbtst in _subtests:
            sbtst.run()
            t.restart.run()

    def _step_comms(self):
        """Write HW version, enter serial number."""
        self.fifo_push(((s.oSerEntry, ('A1504010034',)), ))
        self._picdev.sw_test_mode()
        if self._fifo:
            self._pic_ser.put(b'Software Test Mode Entered\r\n' +
                              b'\r\nSetting Change Done\r\n\n')
        m.pic_SwTstMode.measure()
        self._picdev.write_hwver(self._HW)
        self._limits['HwVerCheck'].limit = self._HW
        if self._fifo:
            self._pic_ser.put(b'I,  2, 06A,Hardware Revision\r\n')
        m.pic_HwVerChk.measure()
        result, sernum = m.ui_SerEntry.measure()
        self._limits['SerCheck'].limit = sernum[0]
        if self._fifo:
            if _NEW_PSU:
                self._pic_ser.put(b'\r\nSetting Change Done\r\n\n')
            else:
                self._pic_ser.put(b'M, 6,Setting is Protected\r\n')
        self._picdev.write_ser(sernum[0])
        if self._fifo:
            self._pic_ser.put(b'I,  3, A1504010034,Serial Number\r\n')
        m.pic_SerChk.measure()

    def _step_emerg_stop(self):
        """Activate emergency stop and measure voltages."""
        self.fifo_push(
            ((s.Tec, 0.0), (s.TecVmon, 0.0), (s.Ldd, 0.0), (s.IsVmon, 0.0),
             (s.o15V, 0.0), (s.o_15V, 0.0), (s.o15Vp, 0.0), (s.o15VpSw, 0.0),
             (s.o5V, 0.0), ))
        t.emg_stop.run()
