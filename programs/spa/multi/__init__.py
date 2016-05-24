#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spa RGB/TRI Initial Test Program.

Call 'self.abort()' to stop program running at end of current step.
'self._result_map' is a list of 'uut.Result' indexed by position.

"""

import time
import threading
import queue
import logging
import traceback
import serial
import tester
from . import support
from . import limit
from . import p89lpc924

MeasureGroup = tester.measure.group

RGB_LIMIT = limit.DATA_RGB
TRI_LIMIT = limit.DATA_TRI

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements

# Set to True to program uC
_DO_PROGRAM = True
# UCFG1 register value as 2 hex digits
_UCFG1 = '23'

# Settling times after changing AC Input.
_AC_SETTLE_TIME = 0.2
# Scale factor to apply to requested AC voltage before setting on AC Source
_AC_SCALE = 4.80
# Maximum AC Source setting we will allow in ac_in().
_AC_VSET_MAX = 190.0

# Time to switch off AC to get a colour change.
_COLOUR_CHANGE_OFF_TIME = 2.0
_COLOUR_CHANGE_WAIT_TIME = 1.0

# Time to do a Firmware Reset
_FIRMWARE_RESET_TIME = 0.1
_FIRMWARE_RESET_WAIT_TIME = 0.5

# From Spa Testing Notes Rev 1:
# B.Power Supplies - Performed With Power On.
# i. Check VCC voltage (Across C9).
#    For Vin = 12Vac, 50Hz - Must be 3.6 VDC +/- 0.3V.
# C.Functional Testing - Performed with a load attached.
# i. Firmware Reset.
#  a. Apply 12Vac, 50Hz for a minimum of 2 seconds.
#  b. Interrupt input AC power for 100mS +/- 10mS.
#  c. Observe Blue flashing at approximately 1 second ON, 1 second OFF.
#  d. Average operating current during ON time must be 720mA ~ 880mA.
# ii.Colour Change for RGB Configuration.
#  a. Apply 12Vac, 50Hz for a minimum of 2 seconds.
#  b. Perform Firmware Reset.
#  c. Interrupt input AC power for 2 +/- 0.25 seconds.
#  d. Observe LED array is now displaying Magenta.
#  e. Leave power connected for at least 2 seconds.
#  f. Repeat c~e above to observe Red, Lime then Green after each power cycle.
#  g. Average operating current must be 720mA ~ 880mA.
# iii.Confirm Colour Change operation as prescribed in ii above.
#  a. While Green, adjust Vin to 10.5VAC +/- 0.1.
#  b. Measure and record average LED operating current and input AC current.
#  c. Repeat b & c above for 12VAC, 24VAC, 32VAC and 35VAC +/- 0.1.
#  d. Average operating current for 12V to 35V AC must be between 720mA~880mA.
#     Average operating current at 10.5V must be between 650 mA ~ 880 mA
# iv. Perform a Firmware Reset to ensure the unit is reset back to its
#     default state.

# Colour Change Sequences:
#   RGB:    Blue, Magenta, Red, Yellow, Green, Cyan, Pinkish-White,
#               Redish-White, Smooth-Rainbow, Switched-Rainbow.
#   TRI:    Blue, White, Green.


class InitialMulti(tester.TestSequence):

    """Spa RGB/TRI Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerOn', self._step_poweron, None, True),
            ('Program', self._step_program, None, _DO_PROGRAM),
            ('Blue', self._step_blue, None, True),
            ('Red', self._step_red, None, True),
            ('Green12', self._step_green12, None, True),
            ('Green24', self._step_green24, None, True),
            ('Green32', self._step_green32, None, True),
            ('Green35', self._step_green35, None, True),
            ('Green10', self._step_green10, None, True),
            ('Reset', self._step_firmware_reset, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Parameter selects 'RGB' or 'TRI' version software.
        hexfilename = test_limits['Hex' + selection.parameter].limit
        self._logger.info('Create. Hex file "%s"', hexfilename)
        # Read Hex file
        hex = open('spa_multi/' + hexfilename, 'r')
        self._hexfile = ()
        for ln in hex.readlines():
            ln = ln.replace('\n', '').replace('\r', '')
            self._hexfile += (ln, )
        hex.close()
        # RGB version has extra colour changes
        self._is_rgb = selection.parameter == 'RGB'
        # This is a multi-unit parallel program so we can't stop on errors.
        self.stop_on_failrdg = False
        # This is a multi-unit parallel program so we can't raise exceptions.
        tester.measure.exception_upon_fail(False)
        # Last AC Source set voltage
        self._last_vac = 0.0
        # Suppress lower level logging
        log = logging.getLogger('tester.spa_multi.p89lpc924')
        log.setLevel(logging.INFO)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d)
        global m
        m = support.Measurements(s, self._limits)
        # Switch on DC Source that power the test fixture
        d.dcsFixture.output(voltage=9.0, output=True)
        d.dcsAuxPos.output(voltage=15.0, output=True)
        d.dcsAuxNeg.output(voltage=15.0, output=True)
        time.sleep(1)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m
        m = None
        global d
        # Switch off DC Source that power the test fixture
        for dc in (d.dcsFixture, d.dcsAuxPos, d.dcsAuxNeg):
            dc.output(voltage=0.0, output=False)
        d = None
        global s
        s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        self._ac_in(0.0, output=False)
        # Reset Logical Devices
        d.reset()

    def _step_poweron(self):
        """Initial Power-Up.

        Trigger the Arduino reset generator, then switch on AC power.
        The reset generator will hold uC reset active, wait 1sec, then pulse
        the reset line to make the uC go into ISP mode.

        """
        self.fifo_push(
            ((s.oVcc1, 3.31), (s.oVcc2, 3.32),
            (s.oVcc3, 3.33), (s.oVcc4, 3.34), ))
        self._ac_in(0.0, output=True)
        if _DO_PROGRAM:
            d.rla_isp.pulse(duration=0.1)
        self._ac_in(12.0, ramp=False, correct=False)
        # Measure AC input and all Vcc.
        MeasureGroup((m.dmm_Vcc1, m.dmm_Vcc2, m.dmm_Vcc3, m.dmm_Vcc4))

    def _step_program(self):
        """Program uC.

        Start 4 threads to program each of the 4 uC.
        The UUTs are left running in BLUE SOLID mode at 12Vac.

        """
        # Make a queue for return of programmer results
        pgm_q = queue.Queue()
        # Start uC programmer threads
        uc1_name = 0
        uc1_port = '/dev/ttyUSB0'
        uc1 = threading.Thread(
            target=_programmer, name='Isp1Thread',
            args=(uc1_name, uc1_port, self._hexfile, pgm_q))
        uc1.start()
        uc2_name = 1
        uc2_port = '/dev/ttyUSB1'
        uc2 = threading.Thread(
            target=_programmer, name='Isp2Thread',
            args=(uc2_name, uc2_port, self._hexfile, pgm_q))
        uc2.start()
        uc3_name = 2
        uc3_port = '/dev/ttyUSB2'
        uc3 = threading.Thread(
            target=_programmer, name='Isp3Thread',
            args=(uc3_name, uc3_port, self._hexfile, pgm_q))
        uc3.start()
        uc4_name = 3
        uc4_port = '/dev/ttyUSB3'
        uc4 = threading.Thread(
            target=_programmer, name='Isp4Thread',
            args=(uc4_name, uc4_port, self._hexfile, pgm_q))
        uc4.start()
        # Wait for programming completion
        self._logger.info('All programmers running')
        uc1.join()
        uc2.join()
        uc3.join()
        uc4.join()
        # Look at programmer output queue ('source' indexes into 'results')
        self._logger.info('Programmers stopped')
        results = [0, 0, 0, 0]
        while not pgm_q.empty():
            source, error = pgm_q.get()
            if error:
                results[source] = 1
        # The programmer mirror sensors
        sensors = (s.oMir1, s.oMir2, s.oMir3, s.oMir4)
        # Write result values into the mirror sensors
        for i in range(4):
            val = results[i]
            sensors[i].store(val)
        # 'Measure' the mirror sensors to check and log data
        MeasureGroup((m.pgm1, m.pgm2, m.pgm3, m.pgm4))
        # Power cycle to start the software
        self._ac_in(0.0)
        time.sleep(3)
        self._ac_in(12.0, ramp=False, correct=False)
        time.sleep(1)
        # Firmware reset to get into BLUE FLASH mode
        self._step_firmware_reset()
        # Power cycle to restart into BLUE mode
        self._ac_in(0.0, output=True)
        time.sleep(10)
        self._ac_in(12.0, ramp=False)

    def _step_blue(self):
        """Blue LED running current.

        UUTs are already running at BLUE when this is called.

        """
        self.fifo_push(
            ((s.oAcVin, 12.01),
             (s.dso_blue, ((7.51, 7.52, 7.53, 7.54), )), ))
        m.dmm_AcVin12.measure()
        m.dso_blue.measure()

    def _step_red(self):
        """Red LED running current.

        UUTs are running at BLUE when this is called.

        """
        self.fifo_push(((s.dso_red, ((7.51, 7.52, 7.53, 7.54), )), ))
        # Change to MAGENTA
        if self._is_rgb:
            self._colour_change(msg='-> Magenta', correct=False)
        # Change to RED/WHITE
        self._colour_change(msg='-> Red/White')
        m.dso_red.measure()

    def _step_green12(self):
        """Green LED current regulation at 12Vac.

        UUTs are running at 12Vac RED when this is called.

        """
        if self._is_rgb:
            self._colour_change(msg='-> Yellow', correct=False)
        self._colour_change(msg='-> Green')
        self.fifo_push(
            ((s.oAcVin, 12.01), (s.oAcIin1, 0.35 / 5), (s.oAcIin2, 0.35 / 5),
             (s.oAcIin3, 0.35 / 5), (s.oAcIin4, 0.35 / 5),
             (s.dso_green, ((7.51, 7.52, 7.53, 7.54), )), ))
        MeasureGroup(
            (m.dmm_AcVin12, m.dso_green, m.dmm_AcIin1_12, m.dmm_AcIin2_12,
             m.dmm_AcIin3_12, m.dmm_AcIin4_12))

    def _step_green24(self):
        """Green LED current regulation at 24Vac."""
        self._ac_in(24.0)
        self.fifo_push(
            ((s.oAcVin, 24.01), (s.oAcIin1, 0.22 / 5), (s.oAcIin2, 0.22 / 5),
             (s.oAcIin3, 0.22 / 5), (s.oAcIin4, 0.22 / 5),
             (s.dso_green, ((7.1, 7.2, 7.3, 7.4), )), ))
        MeasureGroup(
            (m.dmm_AcVin24, m.dso_green, m.dmm_AcIin1_24, m.dmm_AcIin2_24,
             m.dmm_AcIin3_24, m.dmm_AcIin4_24))

    def _step_green32(self):
        """Green LED current regulation at 32Vac."""
        self._ac_in(32.0)
        self.fifo_push(
            ((s.oAcVin, 32.01), (s.oAcIin1, 0.20 / 5), (s.oAcIin2, 0.20 / 5),
             (s.oAcIin3, 0.20 / 5), (s.oAcIin4, 0.20 / 5),
             (s.dso_green, ((7.61, 7.62, 7.63, 7.64), )), ))
        MeasureGroup(
            (m.dmm_AcVin32, m.dso_green, m.dmm_AcIin1_32, m.dmm_AcIin2_32,
             m.dmm_AcIin3_32, m.dmm_AcIin4_32))

    def _step_green35(self):
        """Green LED current regulation at 35Vac."""
        self._ac_in(35.0)
        self.fifo_push(
            ((s.oAcVin, 35.01), (s.oAcIin1, 0.18 / 5), (s.oAcIin2, 0.18 / 5),
             (s.oAcIin3, 0.18 / 5), (s.oAcIin4, 0.18 / 5),
             (s.dso_green, ((7.71, 7.72, 7.73, 7.74), )), ))
        MeasureGroup(
            (m.dmm_AcVin35, m.dso_green, m.dmm_AcIin1_35, m.dmm_AcIin2_35,
             m.dmm_AcIin3_35, m.dmm_AcIin4_35))

    def _step_green10(self):
        """Green LED current regulation at 10.5Vac."""
        self._ac_in(10.5)
        self.fifo_push(
            ((s.oAcVin, 10.5), (s.oAcIin1, 0.25 / 5), (s.oAcIin2, 0.25 / 5),
             (s.oAcIin3, 0.25 / 5), (s.oAcIin4, 0.25 / 5),
             (s.dso_green, ((7.81, 7.82, 7.83, 7.84), )), ))
        MeasureGroup(
            (m.dmm_AcVin10, m.dso_green10, m.dmm_AcIin1_10, m.dmm_AcIin2_10,
             m.dmm_AcIin3_10, m.dmm_AcIin4_10))
        self._logger.info('Restore 12Vac')
        self._ac_in(12.0)

    def _step_firmware_reset(self, vset=12.0):
        """Firmware Reset.

        "Interrupt input AC power for 100mS +/- 10mS."

        """
        self._logger.info('Firmware reset')
        self._ac_in(0.0)
        time.sleep(_FIRMWARE_RESET_TIME)
        self._ac_in(vset, ramp=False, correct=False)
        time.sleep(_FIRMWARE_RESET_WAIT_TIME)

    def _step_error_check(self):
        """Check physical instruments for errors."""
        self._devices.interface.reset()
        d.error_check()

    def _colour_change(self, vset=12.0, msg=None, correct=True):
        """Colour Change.

        "Interrupt input AC power for 2 +/- 0.25 seconds."

        """
        self._logger.info('Colour change %s', msg)
        self._ac_in(0.0)
        time.sleep(_COLOUR_CHANGE_OFF_TIME)
        self._ac_in(vset, ramp=False, correct=correct)
        time.sleep(_COLOUR_CHANGE_WAIT_TIME)

    def _ac_in(self, vset, output=True, ramp=True, correct=True):
        """Set the AC Source for the target input voltage."""
        vsrc = vset * _AC_SCALE
        vsrc += {0.0: 0.0, 10.5: 4.6, 12.0: 8.0,
                 24.0: 3.7, 32.0: 2.5, 35.0: 2.3,
                 }[vset]
        # A just-in-case check to stop blowing up units...
        if vsrc > _AC_VSET_MAX:
            raise ValueError('AC Source setting too high')
        # Switch off immediately, otherwise ramp to change voltage
        if vset < 10.0:
            ramp = False
        if ramp:
            delay = 0.01
            step = 2.0
            d.acsource.linear(
                start=self._last_vac, end=vsrc, step=step, delay=delay)
        else:
            d.acsource.output(voltage=vsrc, output=output)
        self._last_vac = vsrc
        # Correct the AC voltage to allow for transformer drops
        if correct and vset > 10.0:
            s.oAcVin.configure()
            s.oAcVin.opc()
            self.fifo_push(((s.oAcVin, vset), ))
            for _ in range(4):
                vact = s.oAcVin.read()[0]
                verror = vset - vact
                if abs(verror) < 0.09:
                    break
                if abs(verror) < 3.0:
                    vsrc += verror * _AC_SCALE
                d.acsource.output(voltage=vsrc, output=output)
            time.sleep(_AC_SETTLE_TIME)


def _programmer(myname, port, hexfile, result_q):
    """Thread worker to program a uC.

    myname: My thread name.
    port: List of command arguments.
    hexfile: HEX file contents as Tuple of lines.
    result_q: Queue for result tuple: (myname, error).

    """
    logger = logging.getLogger(__name__)
    error = False
    dev = None
    try:
        dev = p89lpc924.P89LPC924(port=port, baud=9600, timeout=1.0)
        dev.read_device_id()
        status_byte = dev.read_status_byte()
        # status_byte b'00' means device is already programmed. Erase it.
        if status_byte == b'00':
            logger.debug('Erasing Device')
            # erase 3 x 1k sectors (0000 to 08FF)
            for adr in ('0000', '0400', '0800'):
                dev.erase_sector(adr)
            # erase 8 x 64b pages (0C00 to 0DFF)
            for adr in ('0C00', '0C40', '0C80', '0CC0',
                        '0D00', '0D40', '0D80', '0DC0'):
                dev.erase_page(adr)
            # Leave the ISP code alone (0E00 to 0FFF)
        dev.read_boot_vector()
        dev.read_UCFG1_register()
        # Write all hex lines into device
        logger.debug('Programming Device')
        for rec in hexfile:
            dev.write_hex_record(rec)
        # Set status bit to zero to run user code at reset
        dev.write_status_bit_zero()
        # Set UCFG1 register
        dev.write_UCFG1_register(_UCFG1)
        # Read back some settings
        dev.read_status_byte()
        dev.read_boot_vector()
        dev.read_UCFG1_register()

    except serial.SerialException as e:
        # Usually if the port cannot be opened
        logger.debug('Serial Error: %s', e)
        error = True
    except p89lpc924.ISPError as e:
        # Device is not programming
        logger.debug('ISP%s Error: %s', myname, e)
        error = True
    except Exception:
        # Log more info on any other exception
        exc_str = traceback.format_exc()
        logger.error('%s', exc_str)
        error = True
    if dev:
        dev.close()
    result_q.put((myname, error))
