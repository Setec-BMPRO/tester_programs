#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVMNx Console driver."""

import time

import attr

import share


class InvalidOutputError(Exception):

    """Attempt to set a non-existing output."""


@attr.s
class PinName:

    """Pin name mappings from index number."""

    # Key: Output index, Value: Schematic pin name
    _output = attr.ib(
        init=False,
        default={
            0: "HBRIDGE_1_extend",
            1: "HBRIDGE_1_retract",
            2: "HBRIDGE_2_extend",
            3: "HBRIDGE_2_retract",
            4: "HBRIDGE_3_extend",
            5: "HBRIDGE_3_retract",
            6: "HBRIDGE_4_extend",
            7: "HBRIDGE_4_retract",
            8: "HBRIDGE_5_extend",
            9: "HBRIDGE_5_retract",
            10: "HBRIDGE_6_extend",
            11: "HBRIDGE_6_retract",
            12: "HBRIDGE_7_extend",
            13: "HBRIDGE_7_retract",
            14: "HBRIDGE_8_extend",
            15: "HBRIDGE_8_retract",
            16: "HS_0A5_EN1",
            17: "HS_0A5_EN2",
            18: "HS_0A5_EN3",
            19: "HS_0A5_EN4",
            20: "HS_0A5_EN5",
            21: "HS_0A5_EN6",
            22: "HS_0A5_EN7",
            23: "HS_0A5_EN8",
            24: "HS_0A5_EN9",
            25: "HS_0A5_EN10",
            26: "HS_0A5_EN11",
            27: "HS_0A5_EN12",
            28: "HS_0A5_EN13",
            29: "HS_0A5_EN14",
            30: "HS_0A5_EN15",
            31: "HS_0A5_EN16",
            32: "HS_0A5_EN17",
            33: "HS_0A5_EN18",
            34: "LS_0A5_EN1",
            35: "LS_0A5_EN2",
            36: "LS_0A5_EN3",
            37: "LS_0A5_EN4",
            38: "OUT5A_EN0",
            39: "OUT5A_EN1",
            40: "OUT5A_EN2",
            41: "OUT5A_EN3",
            42: "OUT5A_EN4",
            43: "OUT5A_EN5",
            44: "OUT5A_PWM_EN6",
            45: "OUT5A_PWM_EN7",
            46: "OUT5A_PWM_EN8",
            47: "OUT5A_PWM_EN9",
            48: "OUT5A_PWM_EN10",
            49: "OUT5A_PWM_EN11",
            50: "OUT5A_PWM_EN12",
            51: "OUT5A_PWM_EN13",
            52: "OUT10A_1",
            53: "OUT10A_2",
            54: "OUT10A_3",
            55: "OUT10A_4",
        },
    )
    # Key: Input index, Value: Schematic pin name
    _input = attr.ib(
        init=False,
        default={
            0: "GEN_PUR_HS_SW1",
            1: "GEN_PUR_HS_SW2",
            2: "GEN_PUR_HS_SW3",
            3: "GEN_PUR_HS_SW4",
            4: "GEN_PUR_HS_SW5",
            5: "GEN_PUR_HS_SW6",
            6: "GEN_PUR_HS_SW7",
            7: "GEN_PUR_HS_SW8",
            8: "GEN_PUR_HS_SW9",
            9: "GEN_PUR_HS_SW10",
            10: "GEN_PUR_HS_SW11",
            11: "GEN_PUR_HS_SW12",
            12: "GEN_PUR_HS_SW13",
            13: "GEN_PUR_HS_SW14",
            14: "GEN_PUR_HS_SW15",
            15: "GEN_PUR_HS_SW16",
            16: "GEN_PUR_HS_SW17",
        },
    )
    # Key: Input index, Value: Schematic pin name
    _analog = attr.ib(
        init=False,
        default={
            0: "TANK 1",
            1: "TANK 2",
            2: "TANK 3",
            3: "TANK 4",
            4: "TANK 5",
            5: "TANK 6",
            6: "VOLTAGE 1",
            7: "VOLTAGE 2",
            8: "TEMP SENSOR 1",
            9: "TEMP SENSOR 2",
            10: "TEMP SENSOR 3",
            11: "TEMP SENSOR 4",
            12: "FUEL SENSOR 1",
            13: "FUEL SENSOR 2",
            14: "VOLTAGE SYS",
        },
    )

    def input_rename(self, names):
        """Rename input pins.

        @param names Dict{index: name}

        """
        for idx, value in names.items():
            self._input[idx] = value

    def output_rename(self, names):
        """Rename output pins.

        @param names Dict{index: name}

        """
        for idx, value in names.items():
            self._output[idx] = value

    def input(self, idx):
        """Input pin index to pin name.

        @param idx Pin index
        @return Pin name

        """
        return self._input[idx]

    def output(self, idx):
        """Output pin index to pin name.

        @param idx Pin index
        @return Pin name

        """
        return self._output[idx]

    def analog(self, idx):
        """Analog pin index to pin name.

        @param idx Pin index
        @return Pin name

        """
        return self._analog[idx]


class _Console(share.console.Base):

    """Communications to RVMNx console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b"uart:~$ \x1b[m"
    ignore = (  # Tuple of strings to remove from responses
        "\x1b[m",  # Normal
        "\x1b[1;31m",  # Bold, Red
        "\x1b[1;32m",  # Bold, Green
    )
    # Console commands
    parameter = share.console.parameter
    cmd_data = {
        "SERIAL": parameter.String(
            "rvmn serial", read_format="{0}",
            writeable=True, write_format="{1} {0}"
        ),
        "PRODUCT-REV": parameter.String(
            "rvmn product-rev", read_format="{0}",
            writeable=True, write_format="{1} {0}"
        ),
        "HARDWARE-REV": parameter.String(
            "rvmn hw-rev", read_format="{0}",
            writeable=True, write_format="{1} {0}"
        ),
        "MAC": parameter.String("rvmn mac", read_format="{0}"),
        "OUTPUT": parameter.String(
            "rvmn output", readable=False, writeable=True, write_format="{1} {0}"
        ),
        "INPUT": parameter.Hex("rvmn input", read_format="{0}"),  # Read all at once
        # These names must match those in PinName._analog
        "TANK 1": parameter.Hex("rvmn analog 0", read_format="{0}"),
        "TANK 2": parameter.Hex("rvmn analog 1", read_format="{0}"),
        "TANK 3": parameter.Hex("rvmn analog 2", read_format="{0}"),
        "TANK 4": parameter.Hex("rvmn analog 3", read_format="{0}"),
        "TANK 5": parameter.Hex("rvmn analog 4", read_format="{0}"),
        "TANK 6": parameter.Hex("rvmn analog 5", read_format="{0}"),
        "VOLTAGE 1": parameter.Hex("rvmn analog 6", read_format="{0}"),
        "VOLTAGE 2": parameter.Hex("rvmn analog 7", read_format="{0}"),
        "TEMP SENSOR 1": parameter.Hex("rvmn analog 8", read_format="{0}"),
        "TEMP SENSOR 2": parameter.Hex("rvmn analog 9", read_format="{0}"),
        "TEMP SENSOR 3": parameter.Hex("rvmn analog 10", read_format="{0}"),
        "TEMP SENSOR 4": parameter.Hex("rvmn analog 11", read_format="{0}"),
        "FUEL SENSOR 1": parameter.Hex("rvmn analog 12", read_format="{0}"),
        "FUEL SENSOR 2": parameter.Hex("rvmn analog 13", read_format="{0}"),
        "VOLTAGE SYS": parameter.Hex("rvmn analog 14", read_format="{0}"),
    }
    banner_lines = 5

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        self.pin_name = PinName()
        max_output_index = 56
        self.hs_outputs = list(range(max_output_index))
        self.reversed_outputs = []
        self.output_remove(  # Remove the LS outputs from the HS outputs list
            {
                "LS_0A5_EN1": 34,
                "LS_0A5_EN2": 35,
                "LS_0A5_EN3": 36,
                "LS_0A5_EN4": 37,
            }
        )
        self.ls_outputs = [34, 35]
        max_input_index = 17
        self.digital_inputs = list(range(max_input_index))
        max_analog_index = 15
        self.analog_inputs = list(range(max_analog_index))

    def reset(self):
        """Pulse RESET using DTR of the BDA4 (both micros)."""
        self.port.dtr = True
        self.reset_input_buffer()
        time.sleep(0.1)
        self.port.dtr = False

    def brand(self, sernum, product_rev, hardware_rev):
        """Brand the unit with Serial Number.

        @param sernum SETEC Serial Number 'AYYWWLLNNNN'
        @param product_rev Product revision from ECO eg: '03A'
        @param hardware_rev Hardware revision from ECO eg: '03A'.

        """
        self.action(None, expected=self.banner_lines)
        self["SERIAL"] = sernum
        self["PRODUCT-REV"] = product_rev
        if hardware_rev:
            self["HARDWARE-REV"] = hardware_rev

    def hs_output(self, index, state=False):
        """Set a HS output state.

        @param index Index number of the output
        @param state True for ON, False for OFF

        """
        if not (index in self.hs_outputs or index in self.reversed_outputs):
            raise InvalidOutputError
        self["OUTPUT"] = "{0} {1}".format(index, 1 if state else 0)

    def ls_output(self, index, state=False):
        """Set a LS output state.

        @param index Index number of the output
        @param state True for ON, False for OFF

        """
        if index not in self.ls_outputs:
            raise InvalidOutputError
        self["OUTPUT"] = "{0} {1}".format(index, 1 if state else 0)

    def analog_pin_name(self, index):
        """Get the schematic name of an analog input pin.

        @param index Index number of the input

        """
        return self.pin_name.analog(index)

    def input_pin_name(self, index):
        """Get the schematic name of an input pin.

        @param index Index number of the input

        """
        return self.pin_name.input(index)

    def output_pin_name(self, index):
        """Get the schematic name of an output pin.

        @param index Index number of the output

        """
        return self.pin_name.output(index)

    def analog_remove(self, names):
        """Remove analog inputs from use.

        @param names Dict{name: index}

        """
        for idx in names.values():
            self.analog_inputs.remove(idx)

    def input_remove(self, names):
        """Remove digital inputs from use.

        @param names Dict{name: index}

        """
        for idx in names.values():
            self.digital_inputs.remove(idx)

    def output_remove(self, names):
        """Remove HS outputs from use.

        @param names Dict{name: index}

        """
        for idx in names.values():
            self.hs_outputs.remove(idx)

    def output_reversed(self, names):
        """Set reversed HS outputs.

        @param names Dict{name: index}

        """
        for idx in names.values():
            self.hs_outputs.remove(idx)
            self.reversed_outputs.append(idx)


class Console101A(_Console):

    """Communications to RVMN101A console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        self.input_remove(
            {
                "GEN_PUR_HS_SW9": 8,
                "GEN_PUR_HS_SW10": 9,
                "GEN_PUR_HS_SW11": 10,
                "GEN_PUR_HS_SW12": 11,
                "GEN_PUR_HS_SW13": 12,
                "GEN_PUR_HS_SW14": 13,
                "GEN_PUR_HS_SW15": 14,
                "GEN_PUR_HS_SW16": 15,
                "GEN_PUR_HS_SW17": 16,
            }
        )


class Console101B(_Console):

    """Communications to RVMN101B console."""

    # Firmware 2.5.8 dropped "\x1b[m" from the prompt tail
    cmd_prompt = b"uart:~$ "

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        self.output_remove(
            {
                "HBRIDGE 3 EXTEND": 4,
                "HBRIDGE 3 RETRACT": 5,
                "HBRIDGE 4 EXTEND": 6,
                "HBRIDGE 4 RETRACT": 7,
                "HBRIDGE 5 EXTEND": 8,
                "HBRIDGE 5 RETRACT": 9,
                "HS_0A5_EN5": 20,
                "HS_0A5_EN13": 28,
                "HS_0A5_EN14": 29,  # Implemented in Rev 14
                "HS_0A5_EN15": 30,  # Implemented in Rev 14
                "HS_0A5_EN18": 33,
                "OUT5A_PWM_13": 51,
            }
        )
        self.pin_name.output_rename(
            {
                52: "OUT10AMP_1",
                53: "OUT10AMP_2",
                54: "OUT10AMP_3",
                55: "OUT10AMP_4",
            }
        )
        self.input_remove(
            {
                "GEN_PUR_HS_SW7": 6,
                "GEN_PUR_HS_SW8": 7,
                "GEN_PUR_HS_SW12": 11,
                "GEN_PUR_HS_SW13": 12,
                "GEN_PUR_HS_SW14": 13,
                "GEN_PUR_HS_SW15": 14,
                "GEN_PUR_HS_SW16": 15,
                "GEN_PUR_HS_SW17": 16,
            }
        )
        self.pin_name.input_rename(
            {
                0: "GEN_PUR_LS_SW1",
                1: "GEN_PUR_LS_SW2",
                2: "GEN_PUR_LS_SW3",
                3: "GEN_PUR_LS_SW4",
                9: "GEN_PUR_LS_SW10",
            }
        )
        self.analog_remove(
            {
                "TANK 2": 1,
                "TANK 6": 5,
                "TEMP SENSOR 2": 9,
                "TEMP SENSOR 4": 11,
                "FUEL SENSOR 2": 13,
            }
        )


class Console101C(Console101A):

    """Communications to RVMN101C console."""

    banner_lines = None  # A non-int will ignore number of lines


class Console200A(Console101A):

    """Communications to RVMN200A console."""

    banner_lines = None  # A non-int will ignore number of lines


class _Console5x(_Console):

    """Communications to RVMN5x console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        self.output_remove(
            {
                "HBRIDGE 3 EXTEND": 4,
                "HBRIDGE 3 RETRACT": 5,
                "HBRIDGE 8 EXTEND": 14,
                "HBRIDGE 8 RETRACT": 15,
                "HS_0A5_EN7": 22,
                "HS_0A5_EN13": 28,
                "HS_0A5_EN14": 29,
                "HS_0A5_EN15": 30,
                "HS_0A5_EN16": 31,
                "HS_0A5_EN17": 32,
                "HS_0A5_EN18": 33,
                "OUT5A_EN0": 38,
                "OUT5A_EN1": 39,
                "OUT5A_EN2": 40,
                "OUT5A_EN3": 41,
                "OUT5A_EN4": 42,
                "OUT5A_EN5": 43,
                "OUT5A_PWM_EN6": 44,
                "OUT5A_PWM_EN7": 45,
                "OUT5A_PWM_EN8": 46,
                "OUT10A_2": 53,
                "OUT10A_3": 54,
                "OUT10A_4": 55,
            }
        )

    def output_pin_name(self, index):
        """Get the schematic name of an output pin.

        RVMN5x HBridge outputs have Extend/Retract swapped relative to the RVMN101x
        It is easier to hack the returned names here than it is to rename them
        using self.pin_name.output_rename().

        @param index Index number of the output

        """
        name = super().output_pin_name(index)
        if name.startswith("HBRIDGE"):
            if name.endswith("extend"):
                name = name.replace("extend", "retract")
            else:
                name = name.replace("retract", "extend")
        return name


class Console50(_Console5x):

    """Communications to RVMN50 console."""

    def __init__(self, port):
        """Initialise communications.

        @param port Serial instance to use

        """
        super().__init__(port)
        self.output_remove(
            {
                "HBRIDGE 2 EXTEND": 2,
                "HBRIDGE 2 RETRACT": 3,
                "HBRIDGE 7 EXTEND": 12,
                "HBRIDGE 7 RETRACT": 13,
            }
        )


class Console55(_Console5x):

    """Communications to RVMN55 console."""


class Console60(Console50):

    """Communications to RVMN60 console."""

    banner_lines = None  # A non-int will ignore number of lines


class Console65(Console55):

    """Communications to RVMN65 console."""

    banner_lines = None  # A non-int will ignore number of lines
