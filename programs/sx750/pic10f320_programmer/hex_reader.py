#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hex file reader for TE Programmer PIC10F320.

Produces output that is suitable for use as an Arduino header file to
embed the PIC firmware images into the flash memory of the Arduino.

PIC10F320 devices are programmed in blocks of 16 x 14-bit words, so we read
the hex file into unsigned variables.

"""

from intelhex import IntelHex       # pip3 install IntelHex


_FILE_DATA = (
    ('pwrsw', '../sx750_picPwrSw_2.hex'),
    ('v5sb', '../sx750_pic5Vsb_1.hex'),
    )

_MASK = 0x3FFF                      # PIC devices use a 14-bit word

for name, filename in _FILE_DATA:
    ih = IntelHex()
    ih.fromfile(filename, format='hex')

    # Output the configuration word
    print('\n// START of software image from file: "{!s}"\n'.format(filename))
    config = 'const unsigned {}_config = 0x{:04X};\n'.format(
        name,
        (ih[0x400E] + (ih[0x400F] << 8)) & _MASK)
    print(config)

    # Count how many rows (of 16 words) of 0xFFFF can be removed from the
    # end of the image. There is no need to program blank rows.
    row_count = 16      # 16 rows of 32 bytes = 512 bytes
    trimming = True
    while trimming:     # Check if the last row is all 0xFF
        for idx in range(32):
            if ih[(row_count - 1 ) * 32 + idx] != 0xFF:
                trimming = False
                break;
        if trimming:
            row_count -= 1  # The entire row was 0xFF
    # Output the image size in words
    print('const unsigned {}_rows = {};\n'.format(name, row_count))

    # Output the firmware image as an array of unsigned integers
    data = 'const PROGMEM unsigned {}_data[] = {{\n'.format(name)
    for i in range(row_count):
        for j in range(0, 32, 2):
            idx = 32 * i + j
            data += '0x{:04X}'.format(
                (ih[idx] + (ih[idx + 1] << 8)) & _MASK)
            if not (i == row_count - 1 and j == 30):
                data += ','
        data += '\n'
    data += '};'
    print(data)
