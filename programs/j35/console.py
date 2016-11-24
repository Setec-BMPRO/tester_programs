#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 ARM processor console driver."""

import time
import threading
from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex
ParameterCAN = console.ParameterCAN
ParameterRaw = console.ParameterRaw

# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF
# "CAN Bound" is STATUS bit 28
_CAN_BOUND = (1 << 28)

# Time it takes for Manual Mode command to take effect
_MANUAL_MODE_WAIT = 2.1


class Console(console.Variable, console.BadUartConsole):

    """Communications to J35 console."""

    def __init__(self, port, fifo):
        """Create console instance."""
        self.fifo = fifo
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BadUartConsole.__init__(self, port)
        self.cmd_data = {
            'DCDC_EN': ParameterBoolean('CONVERTER_ENABLE', writeable=True),
            'VOUT': ParameterFloat(
                'CONVERTER_VOLTS_SETPOINT', writeable=True,
                minimum=0.0, maximum=14.0, scale=1000),
            'IOUT': ParameterFloat(
                'CONVERTER_CURRENT_SETPOINT', writeable=True,
                minimum=15.0, maximum=35.0, scale=1000),
            'FAN': ParameterFloat(
                'FAN_SPEED', writeable=True,
                minimum=0, maximum=100, scale=10),
            'AUX_RELAY': ParameterBoolean('AUX_CHARGE_RELAY', writeable=True),
            'SOLAR': ParameterBoolean('SOLAR_CHARGE_RELAY', writeable=True),
            'LOAD_SET': ParameterFloat(
                'LOAD_SWITCH_STATE_0', writeable=True,
                minimum=0, maximum=0x0FFFFFFF, scale=1),
            'VOUT_OV': ParameterFloat(
                'CONVERTER_OVERVOLT', writeable=True,
                minimum=0, maximum=2, scale=1),
            'SLEEP_MODE': ParameterFloat(
                'SLEEPMODE', writeable=True,
                minimum=0, maximum=3, scale=1),
            'TASK_STARTUP': ParameterFloat(
                'TASK_STARTUP', writeable=True,
                minimum=0, maximum=3, scale=1),
            'SW_VER': ParameterString('SW-VERSION', read_format='{}?'),
            'SEC_T': ParameterFloat('SECONDARY_TEMPERATURE', scale=10),
            'BUS_V': ParameterFloat('BUS_VOLTS', scale=1000),
            'AUX_V': ParameterFloat('AUX_INPUT_VOLTS', scale=1000),
            'AUX_I': ParameterFloat('AUX_INPUT_CURRENT', scale=1000),
            'CAN_V': ParameterFloat('CAN_BUS_VOLTS_SENSE', scale=1000),
            'BATT_I': ParameterFloat('BATTERY_CURRENT', scale=1000),
            'CONV_MAX': ParameterFloat(
                'MLC_MAX_CONVERTER_MW', writeable=True, scale=1000),
            'CONV_RATED': ParameterFloat(
                'MLC_CONVERTER_RATED_MA', writeable=True, scale=1000),
            'CONV_DERATED': ParameterFloat(
                'MLC_CONVERTER_DERATED_MA', writeable=True, scale=1000),
            'CONV_FAULT': ParameterFloat(
                'MLC_CONVERTER_FAULT_MA', writeable=True, scale=1000),
            'INHIBIT_BY_AUX': ParameterBoolean(
                'LOAD_SWITCH_INHIBITED_BY_AUX', writeable=True,),
            'AC_F': ParameterFloat('AC_LINE_FREQUENCY', scale=1000),
            'AC_V': ParameterFloat('AC_LINE_VOLTS', scale=1),
            'SER_ID': ParameterString(
                'SET-SERIAL-ID', writeable=True, readable=False,
                write_format='"{} {}'),
            'HW_VER': ParameterString(
                'SET-HW-VER', writeable=True, readable=False,
                write_format='{0[0]} {0[1]} "{0[2]} {1}'),
            'STATUS': ParameterHex(
                'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex(
                'STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=_CAN_BOUND),
            'CAN': ParameterString('CAN',
                writeable=True, write_format='"{} {}'),
            'CAN_STATS': ParameterHex('CANSTATS', read_format='{}?'),
            'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            }
        # Add in the 14 load switch current readings
        for i in range(1, 15):
            self.cmd_data['LOAD_{}'.format(i)] = ParameterFloat(
                'LOAD_SWITCH_CURRENT_{}'.format(i), scale=1000)
        # Event timer for entry into Manual Mode
        self._myevent = threading.Event()
        self._mytimer = None

    def brand(self, hw_ver, sernum, reset_relay):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=2)  # Flush banner
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True
        # Restart required because of HW_VER setting
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=2)  # Flush banner

    def manual_mode(self, start=False):
        """Set the unit to Manual Mode.

        The unit takes some time for the command to take effect. We use a
        timer to run this delay in the background.

        @param start True to start the entry to Manual Mode
                     False to finish the transition to Manual Mode

        """
        if start:  # Trigger manual mode, and start a timer
            self['SLEEP_MODE'] = 3
            if not self.fifo:
                self._mytimer = threading.Timer(
                    _MANUAL_MODE_WAIT, self._myevent.set)
                self._mytimer.start()
        else:   # Complete manual mode setup once the timer is done.
            if not self.fifo:
                self._myevent.wait()
            self['TASK_STARTUP'] = 0
            self['IOUT'] = 35.0
            self['VOUT'] = 12.8
            self['VOUT_OV'] = 2     # OVP Latch reset
            self['FAN'] = 0

    def derate(self):
        """Derate for the 20A version (J35-A)."""
        self['CONV_MAX'] = 28.8
        self['CONV_RATED'] = 20.0
        self['CONV_DERATED'] = 10.0
        self['CONV_FAULT'] = 25.0
        self['INHIBIT_BY_AUX'] = False

    def dcdc_on(self):
        """Power ON the DC-DC converter circuits."""
        self['DCDC_EN'] = True
        time.sleep(0.5)
        self['VOUT_OV'] = 2     # OVP Latch reset

    def load_set(self, set_on=True, loads=()):
        """Set the state of load outputs.

        @param set_on True to set loads ON, False to set OFF.
                      ON = 0x01, OFF = 0x00
        @param loads Tuple of loads to set ON or OFF (0-13).

        """
        value = 0 if set_on else 0x05555555
        code = 0x1 if set_on else 0
        for load in loads:
            if load not in range(14):
                raise ValueError('Load must be 0-13')
            mask = ~(0x3 << (load * 2)) & 0xFFFFFFFF
            bits = code << (load * 2)
            value = value & mask | bits
        self['LOAD_SET'] = value

    def can_testmode(self, state):
        """Enable or disable CAN Test Mode.

        Once test mode is active, all CAN packets received will display onto
        the console. This means that the Command-Response protocol cannot
        be used any more as it breaks with the extra asynchronous messages.

        """
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = _CAN_ON | reply
        else:
            value = _CAN_OFF & reply
        self['STATUS'] = value
