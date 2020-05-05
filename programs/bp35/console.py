#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""BP35 / BP35-II ARM processor console driver."""

import time

import setec

import share


class _Console():

    """Base class for a BP35 / BP35-II console."""

    # Number of lines in startup banner
    banner_lines = 3
    # Time it takes for Manual Mode command to take effect (sec)
    manual_mode_wait = 2.1
    # "CAN Bound" is STATUS bit 28
    can_bound = 1 << 28
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
            'NV-DEFAULT', writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        'NVWIPE': parameter.Boolean(
            'NV-FACTORY-WIPE',
            writeable=True, readable=False, write_format='{1}'),
        # Product specific commands
        'VSET_CAL': parameter.Calibration('VSET'),    # Voltage reading
        'VBUS_CAL': parameter.Calibration('VBUS'),    # Voltage setpoint
        'BUS_ICAL': parameter.Calibration('ICONV'),   # Current reading
        'CAN': parameter.String(
            'CAN', writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': parameter.Hex('CANSTATS', read_format='{0}?'),
        # X-Register product specific parameters
        'PFC_EN': parameter.Boolean('PFC_ENABLE', writeable=True),
        'DCDC_EN': parameter.Boolean('CONVERTER_ENABLE', writeable=True),
        'VOUT': parameter.Float(
            'CONVERTER_VOLTS_SETPOINT', writeable=True,
            minimum=0.0, maximum=14.0, scale=1000),
        'IOUT': parameter.Float(
            'CONVERTER_CURRENT_SETPOINT', writeable=True,
            minimum=15.0, maximum=40.0, scale=1000),
        'FAN': parameter.Float(
            'FAN_SPEED', writeable=True,
            minimum=0, maximum=100, scale=10),
        'AUX_RELAY': parameter.Boolean('AUX_CHARGE_RELAY', writeable=True),
        'CAN_PWR_EN': parameter.Boolean(
            'CAN_BUS_POWER_ENABLE', writeable=True),
        '3V3_EN': parameter.Boolean('3V3_ENABLE', writeable=True),
        'CAN_EN': parameter.Boolean('CAN_ENABLE', writeable=True),
        'LOAD_SET': parameter.Float(
            'LOAD_SWITCH_STATE_0', writeable=True,
            minimum=0, maximum=0x0FFFFFFF, scale=1),
        'VOUT_OV': parameter.Float(
            'CONVERTER_OVERVOLT', writeable=True,
            minimum=0, maximum=2, scale=1),
        'SLEEP_MODE': parameter.Float(
            'SLEEPMODE', writeable=True,
            minimum=0, maximum=3, scale=1),
        'TASK_STARTUP': parameter.Float(
            'TASK_STARTUP', writeable=True,
            minimum=0, maximum=3, scale=1),
        'BATT_TYPE': parameter.Float('BATTERY_TYPE_SWITCH', scale=1),
        'BATT_SWITCH': parameter.Boolean('BATTERY_ISOLATE_SWITCH'),
        'PRI_T': parameter.Float('PRIMARY_TEMPERATURE', scale=10),
        'SEC_T': parameter.Float('SECONDARY_TEMPERATURE', scale=10),
        'BATT_T': parameter.Float('BATTERY_TEMPERATURE', scale=10),
        'BUS_V': parameter.Float('BUS_VOLTS', scale=1000),
        'BUS_I': parameter.Float('CONVERTER_CURRENT', scale=1000),
        'AUX_V': parameter.Float('AUX_INPUT_VOLTS', scale=1000),
        'AUX_I': parameter.Float('AUX_INPUT_CURRENT', scale=1000),
        'CAN_V': parameter.Float('CAN_BUS_VOLTS_SENSE', scale=1000),
        'BATT_V': parameter.Float('BATTERY_VOLTS', scale=1000),
        'BATT_I': parameter.Float('BATTERY_CURRENT', scale=1000),
        'AC_F': parameter.Float('AC_LINE_FREQUENCY', scale=1000),
        'AC_V': parameter.Float('AC_LINE_VOLTS', scale=1),
        'I2C_FAULTS': parameter.Float('I2C_FAULTS', scale=1),
        'SPI_FAULTS': parameter.Float('SPI_FAULTS', scale=1),
        'OPERATING_MODE': parameter.Hex('CHARGER_MODE'),
        'OCP_CAL': parameter.Float(      # OCP setpoint
            'CAL_I_CONVSET', writeable=True, maximum=65535),
        'STATUS': parameter.Hex(
            'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
        'CAN_BIND': parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=can_bound),
        # SR Solar Regulator commands
        'SR_HW_VER': parameter.Float(
            'SOLAR_REG_HW_VERS', writeable=True, scale=1),
        'SR_VSET': parameter.Float(
            'SOLAR_REG_V', writeable=True, scale=1000),
        'SR_ISET': parameter.Float(
            'SOLAR_REG_I', writeable=True, scale=1000),
        'SR_VCAL': parameter.Float(
            'SOLAR_REG_CAL_V_OUT', writeable=True, scale=1000),
        'SR_ICAL': parameter.Float(
            'SOLAR_REG_CAL_I_OUT', writeable=True, scale=1000),
        'SR_IOUT': parameter.Float('SOLAR_REG_IOUT', scale=1000),
        'SR_DEL_CAL': parameter.Boolean(
            'SOLAR_REG_DEL_CAL', writeable=True),
        'SR_VIN': parameter.Float('SOLAR_REG_VIN', scale=1000),
        'SR_VIN_CAL': parameter.Float(
            'SOLAR_REG_CAL_V_IN', writeable=True, scale=1000),
        'SR_TEMP': parameter.Float('SOLAR_REG_TEMP', scale=10),
        'SR_ALIVE': parameter.Boolean('SOLAR_REG_ALIVE'),
        'SR_ERROR': parameter.Float('SOLAR_REG_ERRORCODE'),
        'SR_RELAY': parameter.Float('SOLAR_REG_RELAY'),
        # PM Solar Regulator commands
        'PM_ALIVE': parameter.Boolean('SOLAR_SI_ALIVE'),
        'PM_RELAY': parameter.Boolean('SOLAR_SI_RAW_OUTPUTS', writeable=True),
        'PM_ICAL': parameter.Float('CAL_IZ_SOLAR_SI', writeable=True),
        'PM_IOUT': parameter.Float('SOLAR_SI_MA', scale=1000),
        'PM_IOUT_REV': parameter.Float('SOLAR_SI_MA_REVERSED', scale=1000),
        'PM_ZEROCAL': parameter.Calibration('ISSI'),
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
        self._timer = setec.BackgroundTimer()

    def brand(self, hw_ver, sernum, reset_relay, is_pm, pic_hw_ver):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self['NVWIPE'] = True
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVWRITE'] = True
        if not is_pm:
            self['SR_DEL_CAL'] = True
            self['SR_HW_VER'] = pic_hw_ver
        reset_relay.pulse(0.1)    # Reset is required because of HW_VER setting
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

    def power_on(self):
        """Power ON the converter circuits."""
        self['PFC_EN'] = True
        time.sleep(0.5)
        self['DCDC_EN'] = True
        time.sleep(0.5)
        self['VOUT_OV'] = 2         # OVP Latch reset

    def load_set(self, set_on=True, loads=()):
        """Set the state of load outputs.

        @param set_on True to set loads ON, False to set OFF.
             ON = 0x01 (Green LED ON, Load ON)
            OFF = 0x10 (Red LED ON, Load OFF)
        @param loads Tuple of loads to set ON or OFF (0-13).

        """
        value = 0x0AAAAAAA if set_on else 0x05555555
        code = 0x1 if set_on else 0x2
        for load in loads:
            if load not in range(14):
                raise ValueError('Load must be 0-13')
            mask = ~(0x3 << (load * 2)) & 0xFFFFFFFF
            bits = code << (load * 2)
            value = value & mask | bits
        self['LOAD_SET'] = value

    def sr_set(self, voltage, current, delay=0):
        """Set the state of the SR Solar Regulator.

        @param voltage Voltage setpoint (V)
        @param current Current setpoint (A)

        """
        self.action(
            '{0} {1} SOLAR-SETP-V-I'.format(
                round(voltage * 1000), round(current * 1000)))
        time.sleep(delay)

    def ocp_cal(self):
        """Read the OCP calibration constant.

        Implemented as a method to enable unittest.
        Unittest cannot override __getattr__ used for element indexing.

        """
        return self['OCP_CAL']


class DirectConsole(_Console, share.console.BadUart):

    """Console for a direct connection."""


class TunnelConsole(_Console, share.console.CANTunnel):

    """Console for a CAN tunneled connection."""
