#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 ARM processor console driver."""

import time
import share


class _Console():

    """Communications to J35 console."""

    # Number of lines in startup banner
    banner_lines = 2
    # "CAN Bound" is STATUS bit 28
    can_bound = 1 << 28
    # Time it takes for Manual Mode command to take effect
    manual_mode_wait = 2.1
    parameter = share.console.parameter
    cmd_data = {
        # Common commands
        'UNLOCK': parameter.Boolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'RESTART': parameter.Boolean(
            'RESTART', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': parameter.String(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': parameter.String(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': parameter.String('SW-VERSION', read_format='{0}?'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'NVWIPE': parameter.Boolean(
            'NV-FACTORY-WIPE',
            writeable=True, readable=False, write_format='{1}'),
        # Product specific commands
        'VSET_CAL': parameter.Calibration('VSET'),    # Voltage reading
        'VBUS_CAL': parameter.Calibration('VBUS'),    # Voltage setpoint
        'BUS_ICAL': parameter.Calibration('ICONV'),   # Current reading
        'CAN': parameter.String('CAN',
            writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': parameter.Hex('CANSTATS', read_format='{0}?'),
        # X-Register product specific parameters
        'DCDC_EN': parameter.Boolean('CONVERTER_ENABLE', writeable=True),
        'VOUT': parameter.Float(
            'CONVERTER_VOLTS_SETPOINT', writeable=True,
            minimum=0.0, maximum=14.0, scale=1000),
        'IOUT': parameter.Float(
            'CONVERTER_CURRENT_SETPOINT', writeable=True,
            minimum=15.0, maximum=35.0, scale=1000),
        'FAN': parameter.Float(
            'FAN_SPEED', writeable=True, minimum=0, maximum=100, scale=10),
        'AUX_RELAY': parameter.Boolean('AUX_CHARGE_RELAY', writeable=True),
        'SOLAR': parameter.Boolean('SOLAR_CHARGE_RELAY', writeable=True),
        'LOAD_SET': parameter.Hex(
            'LOAD_SWITCH_STATE_0', writeable=True,
            minimum=0, maximum=0x0FFFFFFF),
        'VOUT_OV': parameter.Float(
            'CONVERTER_OVERVOLT', writeable=True,
            minimum=0, maximum=2, scale=1),
        'SLEEP_MODE': parameter.Float(
            'SLEEPMODE', writeable=True, minimum=0, maximum=3, scale=1),
        'TASK_STARTUP': parameter.Float(
            'TASK_STARTUP', writeable=True, minimum=0, maximum=3, scale=1),
        'SEC_T': parameter.Float('SECONDARY_TEMPERATURE', scale=10),
        'BUS_V': parameter.Float('BUS_VOLTS', scale=1000),
        'OCP_CAL': parameter.Float(      # OCP setpoint
            'CAL_I_CONVSET', writeable=True, maximum=65535),
        'AUX_V': parameter.Float('AUX_INPUT_VOLTS', scale=1000),
        'AUX_I': parameter.Float('AUX_INPUT_CURRENT', scale=1000),
        'CAN_V': parameter.Float('CAN_BUS_VOLTS_SENSE', scale=1000),
        'BATT_I': parameter.Float('BATTERY_CURRENT', scale=1000),
        'BATT_SWITCH': parameter.Boolean('BATTERY_ISOLATE_SWITCH'),
        'CONV_MAX': parameter.Float(
            'MLC_MAX_CONVERTER_MW', writeable=True, scale=1000),
        'CONV_RATED': parameter.Float(
            'MLC_CONVERTER_RATED_MA', writeable=True, scale=1000),
        'CONV_DERATED': parameter.Float(
            'MLC_CONVERTER_DERATED_MA', writeable=True, scale=1000),
        'CONV_FAULT': parameter.Float(
            'MLC_CONVERTER_FAULT_MA', writeable=True, scale=1000),
        'INHIBIT_BY_AUX': parameter.Boolean(
            'LOAD_SWITCH_INHIBITED_BY_AUX', writeable=True,),
        'AC_F': parameter.Float('AC_LINE_FREQUENCY', scale=1000),
        'AC_V': parameter.Float('AC_LINE_VOLTS', scale=1),
        'STATUS': parameter.Hex(
            'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
        'CAN_BIND': parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=can_bound),
        }

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        # Add in the 14 load switch current readings
        for i in range(1, 15):
            self.cmd_data['LOAD_{0}'.format(i)] = (
                share.console.parameter.Float(
                    'LOAD_SWITCH_CURRENT_{0}'.format(i), scale=1000)
                )
        self._timer = share.timers.BackgroundTimer()

    def brand(self, hw_ver, sernum, reset_relay):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self['NVWIPE'] = True
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)

    def set_sernum(self, sernum):
        """Brand the unit with Serial Number."""
        self['SER_ID'] = sernum
        self['NVWRITE'] = True

    def manual_mode(self, start=False, vout=None, iout=None):
        """Set the unit to Manual Mode.

        The unit takes some time for the command to take effect. We use a
        timer to run this delay in the background.

        @param start True to start the entry to Manual Mode
                     False to finish the transition to Manual Mode
        @param vout Output voltage setpoint in Volts
        @param iout Output OCP setpoint in Amps

        """
        if start:  # Trigger manual mode, and start a timer
            self['SLEEP_MODE'] = 3
            self._timer.start(self.manual_mode_wait)
        else:   # Complete manual mode setup once the timer is done.
            self._timer.wait()
            self['TASK_STARTUP'] = 0
            self['IOUT'] = iout
            self['VOUT'] = vout
            self['VOUT_OV'] = 2     # OVP Latch reset
            self['FAN'] = 0

    def derate(self):
        """Derate for the 20A version (J35-A)."""
        self['CONV_MAX'] = 288
        self['CONV_RATED'] = 20.0
        self['CONV_DERATED'] = 10.0
        self['CONV_FAULT'] = 25.0
        self['INHIBIT_BY_AUX'] = False
        self['IOUT'] = 20.0

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

    def ocp_cal(self):
        """Read the OCP calibration constant.

        Implemented as a method to enable unittest.
        Unittest cannot override __getattr__ used for element indexing.

        """
        return self['OCP_CAL']


class DirectConsole(_Console, share.console.BadUart):

    """Console for a direct connection."""


class TunnelConsole(_Console, share.console.Base):

    """Console for a CAN tunneled connection.

    The CAN tunnel does not need the BadUartConsole stuff.

    """
