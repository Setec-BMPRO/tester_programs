#!/usr/bin/env python3
"""BP35 ARM processor console driver."""

import time

import share.arm_gen1

# Expose arm_gen1.Sensor as bp35.Sensor
Sensor = share.arm_gen1.Sensor

# Some easier to use short names
ArmConsoleGen1 = share.arm_gen1.ArmConsoleGen1
ParameterBoolean = share.arm_gen1.ParameterBoolean
ParameterFloat = share.arm_gen1.ParameterFloat
ParameterHex = share.arm_gen1.ParameterHex
ParameterCAN = share.arm_gen1.ParameterCAN
ParameterRaw = share.arm_gen1.ParameterRaw

# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF


class Console(ArmConsoleGen1):

    """Communications to BP35 console."""

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port, dialect=1)
        self.cmd_data = {
            # Read-Write values
            'PFC_EN': ParameterBoolean('PFC_ENABLE', writeable=True),
            'DCDC_EN': ParameterBoolean('CONVERTER_ENABLE', writeable=True),
            'VOUT': ParameterFloat('CONVERTER_VOLTS_SETPOINT', writeable=True,
                minimum=0.0, maximum=14.0, scale=1000),
            'IOUT': ParameterFloat('CONVERTER_CURRENT_SETPOINT',
                writeable=True, minimum=15.0, maximum=35.0, scale=1000),
            'LOAD_DIS': ParameterFloat('LOAD_SWITCHES_INHIBITED',
                writeable=True, minimum=0, maximum=1, scale=1),
            'FAN': ParameterFloat('FAN_SPEED', writeable=True,
                minimum=0, maximum=100, scale=10),
            'AUX_RELAY': ParameterBoolean('AUX_CHARGE_RELAY', writeable=True),
            'CAN_EN': ParameterBoolean('CAN_BUS_POWER_ENABLE', writeable=True),
            '3V3_EN': ParameterBoolean('3V3_ENABLE', writeable=True),
            'CAN_EN': ParameterBoolean('CAN_ENABLE', writeable=True),
            'LOAD_SET': ParameterFloat('LOAD_SWITCH_STATE_0', writeable=True,
                minimum=0, maximum=0x0FFFFFFF, scale=1),
            'VOUT_OV': ParameterFloat('CONVERTER_OVERVOLT', writeable=True,
                minimum=0, maximum=2, scale=1),
            'MODE': ParameterFloat('SLEEPMODE', writeable=True,
                minimum=0, maximum=3, scale=1),
            # Read-only values
            'BATT_TYPE': ParameterFloat('BATTERY_TYPE_SWITCH', scale=1),
            'BATT_SWITCH': ParameterBoolean('BATTERY_ISOLATE_SWITCH'),
            'PRI_T': ParameterFloat('PRIMARY_TEMPERATURE', scale=10),
            'SEC_T': ParameterFloat('SECONDARY_TEMPERATURE', scale=10),
            'BATT_T': ParameterFloat('BATTERY_TEMPERATURE', scale=10),
            'BUS_V': ParameterFloat('BUS_VOLTS', scale=1000),
            'BUS_I': ParameterFloat('CONVERTER_CURRENT', scale=1000),
            'AUX_V': ParameterFloat('AUX_INPUT_VOLTS', scale=1000),
            'AUX_I': ParameterFloat('AUX_INPUT_CURRENT', scale=1000),
            'CAN_V': ParameterFloat('CAN_BUS_VOLTS_SENSE', scale=1000),
            'BATT_V': ParameterFloat('BATTERY_VOLTS', scale=1000),
            'BATT_I': ParameterFloat('BATTERY_CURRENT', scale=1000),
            'AC_F': ParameterFloat('AC_LINE_FREQUENCY', scale=1000),
            'AC_V': ParameterFloat('AC_LINE_VOLTS', scale=1),
            'I2C_FAULTS': ParameterFloat('I2C_FAULTS', scale=1),
            'SPI_FAULTS': ParameterFloat('SPI_FAULTS', scale=1),
            # Other items
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=(1 << 28)),
            'CAN_ID': ParameterCAN('TQQ,32,0'),
            'CAN_STATS': ParameterRaw('', func=self.canstats),
            'SwVer': ParameterRaw('', func=self.version),
            'SR_HW_VER': ParameterFloat('SOLAR_REG_HW_VERS', writeable=True,
                scale=1),
            'SR_VSET': ParameterFloat('SOLAR_REG_V', writeable=True,
                scale=1000),
            'SR_ISET': ParameterFloat('SOLAR_REG_I', writeable=True,
                scale=1000),
            'SR_VCAL': ParameterFloat('SOLAR_REG_CAL_V_OUT', writeable=True,
                scale=1000),
            }
        # Add in the 14 load switch current readings
        for i in range(1, 15):
            self.cmd_data['LOAD_{}'.format(i)] = ParameterFloat(
                'LOAD_SWITCH_CURRENT_{}'.format(i), scale=1000)

    def manual_mode(self):
        """Enter manual control mode."""
        self['MODE'] = 3
        time.sleep(2)           # Takes 1.0 - 2.0 sec to enter the mode
        self['VOUT'] = 12.8
        self['IOUT'] = 35.0
        self['VOUT_OV'] = 2     # OVP Latch reset

    def power_on(self):
        """Power ON the converter circuits."""
        self['PFC_EN'] = True
        time.sleep(1)
        self['DCDC_EN'] = True
        time.sleep(1)
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

    def can_mode(self, state):
        """Enable or disable CAN Communications Mode."""
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = _CAN_ON | reply
        else:
            value = _CAN_OFF & reply
        self['STATUS'] = value

    def canstats(self):
        """Read CAN Status Data."""
        self.action('CANSTATS?', expected=1)
        return '0'
