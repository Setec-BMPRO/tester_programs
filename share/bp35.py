#!/usr/bin/env python3
"""BP35 ARM processor console driver."""

import share.arm_gen1

# Expose arm_gen1.Sensor as bp35.Sensor
Sensor = share.arm_gen1.Sensor

# Some easier to use short names
ArmConsoleGen1 = share.arm_gen1.ArmConsoleGen1
ParameterBoolean = share.arm_gen1.ParameterBoolean
ParameterFloat = share.arm_gen1.ParameterFloat
ParameterHex = share.arm_gen1.ParameterHex
ParameterCAN = share.arm_gen1.ParameterCAN


class Console(ArmConsoleGen1):

    """Communications to BP35 console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self.cmd_data = {
            # Read-Write values
            'PFC_EN': ParameterBoolean('PFC_ENABLE', writeable=True),
            'DCDC_EN': ParameterBoolean('CONVERTER_ENABLE', writeable=True),
            'VOUT': ParameterFloat('CONVERTER_VOLTS_SETPOINT', writeable=True,
                minimum=0.0, maximum=14.0, scale=0.001),
            'IOUT': ParameterFloat('CONVERTER_CURRENT_SETPOINT',
                writeable=True, minimum=15.0, maximum=35.0, scale=0.001),
            'FAN': ParameterFloat('FAN_SPEED', writeable=True,
                minimum=0, maximum=100, scale=0.1),
            'AUX_RELAY': ParameterBoolean('AUX_CHARGE_RELAY', writeable=True),
            'CAN_EN': ParameterBoolean('CAN_BUS_POWER_ENABLE', writeable=True),
            '3V3_EN': ParameterBoolean('3V3_ENABLE', writeable=True),
            'CAN_EN': ParameterBoolean('CAN_ENABLE', writeable=True),
            'LOAD_SET': ParameterFloat('LOAD_SWITCH_STATE', writeable=True,
                minimum=0, maximum=0x0FFFFFFF, scale=1),
            'BUS_OV': ParameterFloat('CONVERTER_OVERVOLT', writeable=True,
                minimum=0, maximum=2, scale=1),
            'MODE': ParameterFloat('SLEEPMODE', writeable=True,
                minimum=0, maximum=3, scale=1),
            # Read-only values
            'BATT_TYPE': ParameterFloat('BATTERY_TYPE_SWITCH', scale=1),
            'BATT_SWITCH': ParameterBoolean('BATTERY_ISOLATE_SWITCH'),
            'PRI_T': ParameterFloat('PRIMARY_TEMPERATURE', scale=0.1),
            'SEC_T': ParameterFloat('SECONDARY_TEMPERATURE', scale=0.1),
            'BATT_T': ParameterFloat('BATTERY_TEMPERATURE', scale=0.1),
            'BUS_V': ParameterFloat('BUS_VOLTS', scale=0.001),
            'BUS_I': ParameterFloat('CONVERTER_CURRENT', scale=0.001),
            'AUX_V': ParameterFloat('AUX_INPUT_VOLTS', scale=0.001),
            'AUX_I': ParameterFloat('AUX_INPUT_CURRENT', scale=0.001),
            'CAN_V': ParameterFloat('CAN_BUS_VOLTS_SENSE', scale=0.001),
            'BATT_V': ParameterFloat('BATTERY_VOLTS', scale=0.001),
            'BATT_I': ParameterFloat('BATTERY_CURRENT', scale=0.001),
            'AC_F': ParameterFloat('AC_LINE_FREQUENCY', scale=0.001),
            'AC_V': ParameterFloat('AC_LINE_VOLTS', scale=1),
            'LOAD_1': ParameterFloat('LOAD_SWITCH_CURRENT_1', scale=0.001),
            'LOAD_2': ParameterFloat('LOAD_SWITCH_CURRENT_2', scale=0.001),
            'LOAD_3': ParameterFloat('LOAD_SWITCH_CURRENT_3', scale=0.001),
            'LOAD_4': ParameterFloat('LOAD_SWITCH_CURRENT_4', scale=0.001),
            'LOAD_5': ParameterFloat('LOAD_SWITCH_CURRENT_5', scale=0.001),
            'LOAD_6': ParameterFloat('LOAD_SWITCH_CURRENT_6', scale=0.001),
            'LOAD_7': ParameterFloat('LOAD_SWITCH_CURRENT_7', scale=0.001),
            'LOAD_8': ParameterFloat('LOAD_SWITCH_CURRENT_8', scale=0.001),
            'LOAD_9': ParameterFloat('LOAD_SWITCH_CURRENT_9', scale=0.001),
            'LOAD_10': ParameterFloat('LOAD_SWITCH_CURRENT_10', scale=0.001),
            'LOAD_11': ParameterFloat('LOAD_SWITCH_CURRENT_11', scale=0.001),
            'LOAD_12': ParameterFloat('LOAD_SWITCH_CURRENT_12', scale=0.001),
            'LOAD_13': ParameterFloat('LOAD_SWITCH_CURRENT_13', scale=0.001),
            'LOAD_14': ParameterFloat('LOAD_SWITCH_CURRENT_14', scale=0.001),
            'I2C_FAULTS': ParameterFloat('I2C_FAULTS', scale=1),
            'SPI_FAULTS': ParameterFloat('SPI_FAULTS', scale=1),
            'CAN_ID': ParameterCAN('TQQ,32,0'),
            }

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
