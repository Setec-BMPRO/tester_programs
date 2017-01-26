#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 ARM processor console driver."""

import time
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


class Console(console.Variable, console.BadUartConsole):

    """Communications to BP35 console."""

    def __init__(self, port):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BadUartConsole.__init__(self, port)
        self.cmd_data = {
            'PFC_EN': ParameterBoolean('PFC_ENABLE', writeable=True),
            'DCDC_EN': ParameterBoolean('CONVERTER_ENABLE', writeable=True),
            'VOUT': ParameterFloat(
                'CONVERTER_VOLTS_SETPOINT', writeable=True,
                minimum=0.0, maximum=14.0, scale=1000),
            'IOUT': ParameterFloat(
                'CONVERTER_CURRENT_SETPOINT', writeable=True,
                minimum=15.0, maximum=35.0, scale=1000),
            'LOAD_DIS': ParameterFloat(
                'LOAD_SWITCHES_INHIBITED', writeable=True,
                minimum=0, maximum=1, scale=1),
            'FAN': ParameterFloat(
                'FAN_SPEED', writeable=True,
                minimum=0, maximum=100, scale=10),
            'AUX_RELAY': ParameterBoolean('AUX_CHARGE_RELAY', writeable=True),
            'CAN_PWR_EN': ParameterBoolean(
                'CAN_BUS_POWER_ENABLE', writeable=True),
            '3V3_EN': ParameterBoolean('3V3_ENABLE', writeable=True),
            'CAN_EN': ParameterBoolean('CAN_ENABLE', writeable=True),
            'LOAD_SET': ParameterFloat(
                'LOAD_SWITCH_STATE_0', writeable=True,
                minimum=0, maximum=0x0FFFFFFF, scale=1),
            'VOUT_OV': ParameterFloat(
                'CONVERTER_OVERVOLT', writeable=True,
                minimum=0, maximum=2, scale=1),
            'SET_MODE': ParameterFloat(
                'SLEEPMODE', writeable=True,
                minimum=0, maximum=3, scale=1),
            'SR_HW_VER': ParameterFloat(
                'SOLAR_REG_HW_VERS', writeable=True,
                scale=1),
            'SR_VSET': ParameterFloat(
                'SOLAR_REG_V', writeable=True,
                scale=1000),
            'SR_ISET': ParameterFloat(
                'SOLAR_REG_I', writeable=True,
                scale=1000),
            'SR_VCAL': ParameterFloat(
                'SOLAR_REG_CAL_V_OUT', writeable=True,
                scale=1000),
            'SR_ICAL': ParameterFloat(
                'SOLAR_REG_CAL_I_OUT', writeable=True,
                scale=1000),
            'SR_IOUT': ParameterFloat('SOLAR_REG_IOUT', scale=1000),
            'SR_DEL_CAL': ParameterBoolean(
                'SOLAR_REG_DEL_CAL', writeable=True),
            'SR_VIN': ParameterFloat('SOLAR_REG_VIN', scale=1000),
            'SR_VIN_CAL': ParameterFloat(
                'SOLAR_REG_CAL_V_IN', writeable=True,
                scale=1000),
            'SW_VER': ParameterString('SW-VERSION', read_format='{0}?'),
            'BATT_TYPE': ParameterFloat('BATTERY_TYPE_SWITCH', scale=1),
            'BATT_SWITCH': ParameterBoolean('BATTERY_ISOLATE_SWITCH'),
            'PRI_T': ParameterFloat('PRIMARY_TEMPERATURE', scale=10),
            'SEC_T': ParameterFloat('SECONDARY_TEMPERATURE', scale=10),
            'BATT_T': ParameterFloat('BATTERY_TEMPERATURE', scale=10),
            'BUS_V': ParameterFloat('BUS_VOLTS', scale=1000),
            'BUS_I': ParameterFloat('CONVERTER_CURRENT', scale=1000),
            'BUS_ICAL': ParameterFloat(
                'ICONV', writeable=True,    # an undocumented command...
                write_format='{0} "{1} CAL',
                scale=1000),
            'AUX_V': ParameterFloat('AUX_INPUT_VOLTS', scale=1000),
            'AUX_I': ParameterFloat('AUX_INPUT_CURRENT', scale=1000),
            'CAN_V': ParameterFloat('CAN_BUS_VOLTS_SENSE', scale=1000),
            'BATT_V': ParameterFloat('BATTERY_VOLTS', scale=1000),
            'BATT_I': ParameterFloat('BATTERY_CURRENT', scale=1000),
            'AC_F': ParameterFloat('AC_LINE_FREQUENCY', scale=1000),
            'AC_V': ParameterFloat('AC_LINE_VOLTS', scale=1),
            'I2C_FAULTS': ParameterFloat('I2C_FAULTS', scale=1),
            'SPI_FAULTS': ParameterFloat('SPI_FAULTS', scale=1),
            'SR_TEMP': ParameterFloat('SOLAR_REG_TEMP', scale=10),
            'SR_ALIVE': ParameterBoolean('SOLAR_REG_ALIVE'),
            'SR_ERROR': ParameterFloat('SOLAR_REG_ERRORCODE'),
            'SR_RELAY': ParameterFloat('SOLAR_REG_RELAY'),
            'OPERATING_MODE': ParameterHex('CHARGER_MODE'),
            'SER_ID': ParameterString(
                'SET-SERIAL-ID', writeable=True, readable=False,
                write_format='"{0} {1}'),
            'HW_VER': ParameterString(
                'SET-HW-VER', writeable=True, readable=False,
                write_format='{0[0]} {0[1]} "{0[2]} {1}'),
            'STATUS': ParameterHex(
                'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex(
                'STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=_CAN_BOUND),
            'CAN': ParameterString('CAN',
                writeable=True, write_format='"{0} {1}'),
            'CAN_STATS': ParameterHex('CANSTATS', read_format='{0}?'),
            'UNLOCK': ParameterBoolean('$DEADBEA7 UNLOCK',
                writeable=True, readable=False, write_format='{1}'),
            'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            }
        # Add in the 14 load switch current readings
        for i in range(1, 15):
            self.cmd_data['LOAD_{0}'.format(i)] = ParameterFloat(
                'LOAD_SWITCH_CURRENT_{0}'.format(i), scale=1000)

    def manual_mode(self):
        """Enter manual control mode."""
        self['SET_MODE'] = 3
        mode = 0
        while mode != 0x10000:      # Wait for the operating mode to change
            mode = self['OPERATING_MODE']
        self['VOUT'] = 12.8
        self['IOUT'] = 35.0
        self['VOUT_OV'] = 2     # OVP Latch reset

    def power_on(self):
        """Power ON the converter circuits."""
        self['PFC_EN'] = True
        time.sleep(0.5)
        self['DCDC_EN'] = True
        time.sleep(0.5)
        self['VOUT_OV'] = 2     # OVP Latch reset
        self['LOAD_DIS'] = False

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


    def solar_set(self, voltage, current):
        """Set the state of Solar Regulator.

        @param voltage Voltage setpoint
        @param current Current setpoint

        """
        self.action(
            '{0} {1} SOLAR-SETP-V-I'.format(
                int(voltage * 1000), int(current * 1000)))

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
