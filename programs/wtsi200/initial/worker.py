#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydispatch import dispatcher
import shlex
import logging
import signals


class Worker(object):
    """Converts a hex file into a header file."""
    def __init__(self):
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        dispatcher.connect(
            self._load_program,
            sender=signals.Thread.gui,
            signal=signals.MySignal.controller_load_program)

    def _load_program(self, data):
        self.text_string = ''
        self.filename = data
        try:
            self._get_hex_file()
            self._make_program_file()
            self._message(
                'Header file complete. Program size: {} bytes\n'
                'Upload the sketch to the Arduino board.\n'
                ''.format(self.program_size))
        except Exception as err:
            self._message(str(err) + '\n')

    def _get_hex_file(self):
        input_file = open(self.filename, 'r')
        body = input_file.read()
        lexer = shlex.shlex(body)
        #Considers ':' to be whitespace and not a token
        lexer.whitespace += ':'
        #Put all data bytes of the program into a text string
        for item in lexer:
            item = item[8:-2]
            self.text_string += item
        self._logger.debug('Byte string> %s', self.text_string)
        input_file.close()

    def _make_program_file(self):
        output_file = open('wtsi200/myprogram.h', 'w')
        self.program_size = int(len(self.text_string) >> 1)
        size = (
            'int program_size = {}; //Bytes ({})\n'
            ''.format(self.program_size, self.filename))
        self._logger.debug(size)
        output_file.write(size)

        count = 0
        self.byte_list = []
        for i in range(self.program_size):
            #Get a byte (2 characters)
            x = self.text_string[count] + self.text_string[count+1]
            #Convert to hex notation and append to a list
            y = hex(bytes.fromhex(x)[0])
            self.byte_list.append(y)
            count += 2
        self._logger.debug('byte_list> %s', self.byte_list)
        program_array = 'const PROGMEM char mycode[] = {\n'
        count = 0
        for item in self.byte_list:
            program_array += item + ', '
            count += 1
            if count == 16:
                count = 0
                program_array += '\n'

        program_array += '};'
        self._logger.debug('Program> %s', program_array)
        self._logger.debug('Program size> %s', self.program_size)
        output_file.write(program_array)
        output_file.close()

    def _find_data(self, addr):
        """
        Debugging tool to find bytes within the text string and byte list.
        """
        x = self.text_string[addr*2] + self.text_string[(addr*2) + 1]
        y = self.byte_list[addr]
        self._logger.debug('Text> %s, Byte> %s', x, y)

    def _message(self, msg):
        dispatcher.send(
            sender=signals.Thread.gui,
            signal=signals.MySignal.worker_message,
            data=msg)
