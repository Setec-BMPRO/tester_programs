#!/usr/bin/env python3
"""BP35 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as bp35.Sensor
Sensor = share.arm_gen1.Sensor


class _Parameter():

    """Parameter base class."""

    def __init__(self, command, writeable=False):
        """Remember the command verb and writeable state."""
        self._cmd = command
        self._writeable = writeable

    def write_cmd(self, value):
        """Generate the write command string.

        @param value Data value.
        @return Command string.

        """
        if not self._writeable:
            raise ValueError('Parameter is read-only')
        return '{} "{} XN!'.format(value, self._cmd)

    def read_cmd(self, value):
        """Generate the read command string.

        @param value Data value.
        @return Command string.

        """
        return '"{} XN?'.format(self._cmd)


class ParameterBoolean(_Parameter):

    """Boolean parameter type."""

    def write_cmd(self, value):
        """Generate the write command string.

        @param value Data value to be validated.
        @return Command string.

        """
        if not isinstance(value, bool):
            raise ValueError('value "{}" must be boolean'.format(value))
        return super().write_cmd(int(value))

    def read_val(self, value):
        """Convert the data value read from the unit.

        @param value Data value from the unit.
        @return Boolean data value.

        """
        return bool(value)


class ParameterFloat(_Parameter):

    """Float parameter type."""

    def __init__(self, command, writeable=False,
                       minimum=0, maximum=1000, scale=1):
        """Remember the scaling and data limits."""
        super().__init__(command, writeable)
        self._min = minimum
        self._max = maximum
        self._scale = scale

    def write_cmd(self, value):
        """Generate the write command string.

        @param value Data value to be validated.
        @return Command string.

        """
        if value < self._min or value > self._max:
            raise ValueError(
                'Value out of range {} - {}'.format(self._min, self._max))
        return super().write_cmd(int(value * self._scale))

    def read_val(self, value):
        """Convert the data value read from the unit.

        @param value Data value from the unit.
        @return Float data value.

        """
        return value / self._scale


_BP35_DATA = {
    'FAN': ParameterFloat('FAN_SPEED', writeable=True,
                          minimum=0, maximum=100, scale=0.1),
    'VOUT': ParameterFloat('CONVERTER_VOLTS_SETPOINT', writeable=True,
                           minimum=0.0, maximum=14.0, scale=0.001),
    'IOUT': ParameterFloat('CONVERTER_CURRENT_SETPOINT', writeable=True,
                           minimum=15.0, maximum=35.0, scale=0.001),
    'PFC_EN': ParameterBoolean('PFC_ENABLE', writeable=True),
    'DCDC_EN': ParameterBoolean('CONVERTER_ENABLE', writeable=True),
    'AUX_RELAY': ParameterBoolean('AUX_CHARGE_RELAY', writeable=True),
    'CAN_POWER_EN': ParameterBoolean('CAN_BUS_POWER_ENABLE', writeable=True),
    '3V3_EN': ParameterBoolean('3V3_ENABLE', writeable=True),
    'CAN_EN': ParameterBoolean('CAN_ENABLE', writeable=True),
    # FIXME: Is this a float, or something else?
    'LOAD_SWITCH_STATE': ParameterFloat('LOAD_SWITCH_STATE', writeable=True,
                                        minimum=0, maximum=999999, scale=1),
    'SLEEPMODE': ParameterFloat('SLEEPMODE', writeable=True,
                                minimum=0, maximum=3, scale=1),
# Read-only values
    'BATT_TYPE': ParameterFloat('BATTERY_TYPE_SWITCH',
                                          minimum=0, maximum=9, scale=1),
    'BATT_SWITCH': ParameterBoolean('BATTERY_ISOLATE_SWITCH'),
    }

#'CONVERTER_OVERVOLT'
#'PRIMARY_TEMPERATURE'
#'SECONDARY_TEMPERATURE'
#'BATTERY_TEMPERATURE'
#'BUS_VOLTS'
#'CONVERTER_CURRENT'
#'AUX_INPUT_VOLTS'
#'AUX_INPUT_CURRENT'
#'CAN_BUS_VOLTS_SENSE'
#'BATTERY_VOLTS'
#'BATTERY_CURRENT'
#'AC_LINE_FREQUENCY'
#'AC_LINE_VOLTS'
#'LOAD_SWITCH_CURRENT_1'
#'LOAD_SWITCH_CURRENT_2'
#'LOAD_SWITCH_CURRENT_3'
#'LOAD_SWITCH_CURRENT_4'
#'LOAD_SWITCH_CURRENT_5'
#'LOAD_SWITCH_CURRENT_6'
#'LOAD_SWITCH_CURRENT_7'
#'LOAD_SWITCH_CURRENT_8'
#'LOAD_SWITCH_CURRENT_9'
#'LOAD_SWITCH_CURRENT_10'
#'LOAD_SWITCH_CURRENT_11'
#'LOAD_SWITCH_CURRENT_12'
#'LOAD_SWITCH_CURRENT_13'
#'LOAD_SWITCH_CURRENT_14'
#'I2C_FAULTS'
#'SPI_FAULTS'


class Console(share.arm_gen1.ArmConsoleGen1):

    """Communications to ARM console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self._read_cmd = None
        # Data readings: Name -> (function, parameter)
        self.cmd_data = {
            'CAN_ID': (self.can_id, None),
            }

    def __getitem__(self, key):
        """Read a value from the BP35.

        @return Reading ID

        """
        pass

    def __setitem__(self, key, value):
        """Write a value to the BP35.

        @param key Reading ID
        @param value Data value.

        """
        pass

    def sleepmode(self, state):
        """Enable or disable Test Mode"""
        self._logger.debug('Test Mode = %s', state)
        value = 3 if state else 0
        cmd = '{} "SLEEPMODE XN!'.format(value)
        self.action(cmd)

    def fanspeed(self, value):
        """Set the fan speed"""
        cmd = '{} "FAN_SPEED XN!'.format(value)
        self.action(cmd)

    def can_id(self, dummy):
        """Simple CAN check by sending an ID request to the Trek2.

        @param dummy Unused parameter.
        @return The response string from the target device.

        """
        try:
            reply = self.action('"TQQ,32,0 CAN', expected=2)[1]
        except share.arm_gen1.ArmError:
            reply = ''
        return reply
