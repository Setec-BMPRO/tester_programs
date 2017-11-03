#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 ARM processor console driver."""

import time
import share

# Some easier to use short names
Sensor = share.console.Sensor
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat
ParameterCalibration = share.console.ParameterCalibration
ParameterHex = share.console.ParameterHex


class _Console():

    """Communications to J35 console."""

    # Number of lines in startup banner
    banner_lines = 2
    # "CAN Bound" is STATUS bit 28
    can_bound = 1 << 28
    # Time it takes for Manual Mode command to take effect
    manual_mode_wait = 2.1
    cmd_data = {
        # Common commands
        'UNLOCK': ParameterBoolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'RESTART': ParameterBoolean(
            'RESTART', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': ParameterString(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': ParameterString('SW-VERSION', read_format='{0}?'),
        'NVDEFAULT': ParameterBoolean(
            'NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'NVWIPE': ParameterBoolean(
            'NV-FACTORY-WIPE',
            writeable=True, readable=False, write_format='{1}'),
        # Product specific commands
        'VSET_CAL': ParameterCalibration('VSET'),    # Voltage reading
        'VBUS_CAL': ParameterCalibration('VBUS'),    # Voltage setpoint
        'BUS_ICAL': ParameterCalibration('ICONV'),   # Current reading
        'CAN': ParameterString('CAN',
            writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': ParameterHex('CANSTATS', read_format='{0}?'),
        # X-Register product specific parameters
        'DCDC_EN': ParameterBoolean('CONVERTER_ENABLE', writeable=True),
        'VOUT': ParameterFloat(
            'CONVERTER_VOLTS_SETPOINT', writeable=True,
            minimum=0.0, maximum=14.0, scale=1000),
        'IOUT': ParameterFloat(
            'CONVERTER_CURRENT_SETPOINT', writeable=True,
            minimum=15.0, maximum=35.0, scale=1000),
        'FAN': ParameterFloat(
            'FAN_SPEED', writeable=True, minimum=0, maximum=100, scale=10),
        'AUX_RELAY': ParameterBoolean('AUX_CHARGE_RELAY', writeable=True),
        'SOLAR': ParameterBoolean('SOLAR_CHARGE_RELAY', writeable=True),
        'LOAD_SET': ParameterHex(
            'LOAD_SWITCH_STATE_0', writeable=True,
            minimum=0, maximum=0x0FFFFFFF),
        'VOUT_OV': ParameterFloat(
            'CONVERTER_OVERVOLT', writeable=True,
            minimum=0, maximum=2, scale=1),
        'SLEEP_MODE': ParameterFloat(
            'SLEEPMODE', writeable=True, minimum=0, maximum=3, scale=1),
        'TASK_STARTUP': ParameterFloat(
            'TASK_STARTUP', writeable=True, minimum=0, maximum=3, scale=1),
        'SEC_T': ParameterFloat('SECONDARY_TEMPERATURE', scale=10),
        'BUS_V': ParameterFloat('BUS_VOLTS', scale=1000),
        'OCP_CAL': ParameterFloat(      # OCP setpoint
            'CAL_I_CONVSET', writeable=True, maximum=65535),
        'AUX_V': ParameterFloat('AUX_INPUT_VOLTS', scale=1000),
        'AUX_I': ParameterFloat('AUX_INPUT_CURRENT', scale=1000),
        'CAN_V': ParameterFloat('CAN_BUS_VOLTS_SENSE', scale=1000),
        'BATT_I': ParameterFloat('BATTERY_CURRENT', scale=1000),
        'BATT_SWITCH': ParameterBoolean('BATTERY_ISOLATE_SWITCH'),
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
        'STATUS': ParameterHex(
            'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
        'CAN_BIND': ParameterHex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=can_bound),
        }

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        # Add in the 14 load switch current readings
        for i in range(1, 15):
            self.cmd_data['LOAD_{0}'.format(i)] = ParameterFloat(
                'LOAD_SWITCH_CURRENT_{0}'.format(i), scale=1000)
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
