#!/usr/bin/env python
#-*- coding=utf-8 -*-
# Author: Zhaoting Weng
# Created Time: Thu 18 Dec 2014 01:52:00 PM CET

import os.path
import platform
import binascii
import re
from collections import OrderedDict

import xlrd
from utility import *
from scale import *


def binary_converter(key, length, value):
    """Convert as following format:
    |:KEY: (2 bytes) |:LENGTH: (2 bytes) |:VALUE: (determined by LENGTH)

    :param key: Key ID (cell obj)
    :param length: Key Length with unit bit(cell obj)
    :param value: Key Value(cell obj)

    :returns: list of three part of binary fragment
    """
    TYPE_MAP = {0: 'EMPTY', 1: 'TEXT', 2: 'NUMBER', 3: 'DATE', 4: 'BOOLEAN', 5: 'ERROR', 6: 'BLANK'}

    # <Key ID>
    if key.ctype is xlrd.XL_CELL_NUMBER:
        key_bin = int_repr_to_binary_real(int(key.value), 16)
    elif key.ctype is xlrd.XL_CELL_TEXT:
        key.value = key.value.encode("utf-8")
        dec_int = int(key.value, 16)
        key_bin= dec_int_to_binary_real(dec_int, 16)
    else:
        error_info = "'Key ID' type should not be %s" %TYPE_MAP[key.ctype]
        raise TypeError(error_info)

    # <Key Length>
    if length.ctype is xlrd.XL_CELL_NUMBER:
        length_bin = dec_int_to_binary_real(int(length.value), 16)
    else:
        error_info = "'Length' type should not be %s" %TYPE_MAP[length.ctype]
        raise TypeError(error_info)

    # <Key Value>
    if value.ctype is xlrd.XL_CELL_NUMBER:
        # Number
        value_bin = int_repr_to_binary_real(int(value.value), int(length.value))
    elif value.ctype is xlrd.XL_CELL_TEXT:
        # TEXT
        value.value = value.value.encode('utf8')
        if value.value.startswith('"'):
            # String start with '"'are real representation as real binary, except length
            value_bin = extend_string_to_fix_length(value.value[1:-1], int(length.value))
        else:
            # hex integer represents binary
            dec_int = int(value.value, 16)
            value_bin = dec_int_to_binary_real(dec_int, int(length.value))
    else:
        # OTHERS
        error_info = "'Value' type should not be %s" %TYPE_MAP[value.ctype]
        raise TypeError(error_info)

    # <Fragment>
    fragment = [key_bin, length_bin, value_bin]
    return fragment

def fill_header(fragments):
    """Manipulate the 1st fragment(Striping length & keyid infos, fill in checksum).

    :param fragments: List of fragment.
    :return: None
    """
    # 1. Strip 1st fragment's length & keyid infos
    fragments[0] = ['', '', fragments[0][2]]

    # 2. Checksum
    values = ''.join([''.join(f) for f in fragments])[2:]      # Exclude 2-byte value of "checksum"
    length = len(values)
    if length % 2 != 0:
        raise ValueError("length of contents for checksum is not even")
    pairs = [values[i*2]+values[i*2+1] for i in range(length/2)]
    # Calculate checksum
    check_sum = checksum(pairs)
    # fill in checksum
    fragments[0][2] = check_sum + fragments[0][2][2:]
    return  None

def preprocess(cali, length, name):
    """Preprocess for fragment.
    1. Check then convert Calibration character to encoded character, replacing illegal characters to '_';
    2. Check then convert KeyLength to int;
    3. Check then convert KeyName to encoded character.

    :param cali: calibration cell.
    :param length: keylength cell.
    :param name: keyname cell.
    :return: Converted fragment.
    """
    TYPE_MAP = {0: 'EMPTY', 1: 'TEXT', 2: 'NUMBER', 3: 'DATE', 4: 'BOOLEAN', 5: 'ERROR', 6: 'BLANK'}
    # 1
    if cali.ctype is not xlrd.XL_CELL_TEXT:
        error_info = "Type of calibration cell should not be %s" %(TYPE_MAP[cali.ctype])
        raise TypeError(error_info)
    else:
        cali_convert = cali.value.encode("utf-8")
        p = re.compile(r"^\d|\W+")
        cali_convert = p.sub("_", cali_convert)
    # 2
    if length.ctype is not xlrd.XL_CELL_NUMBER:
        error_info = "Type of keyLength cell should not be %s" %(TYPE_MAP[length.ctype])
        raise TypeError(error_info)
    else:
        length_convert = length.value
    # 3
    if name.ctype is xlrd.XL_CELL_TEXT:
        name.value = name.value.encode("utf-8")
        #name_convert = name.value[len("ERG_SGM358_"):]
        name_convert = name.value
    elif name.ctype is xlrd.XL_CELL_EMPTY:
        name_convert = ''
    else:
        error_info = "Type of KeyName cell should not be %s" %(TYPE_MAP[name.ctype])
        raise TypeError(error_info)
    return [cali_convert, length_convert, name_convert]

def gen_header(fragments):
    """Generate header file.

    :param fragments: List of lists with content [cali(char), keyLength(float), keyName(char)].
    :return: String to be writen to file.
    """
    # Exclude header-info entires
    non_include_item_num = len([frg for frg in fragments if frg[2] == ''])
    fragments = fragments[non_include_item_num:]

    content = ""
    pool = []
    last_is_one_bit = False
    byte_counter = 0
    length_sum = 0
    currentName = fragments[0][2]
    # Generate first header
    content += "typedef struct s_%s\n{\n" %currentName
    for fragment in fragments:
        cali, keyLength, keyName =  fragment
        # Check if Calibration has illegal character
        if keyName != currentName:
            # Generate last structure's tail
            content += "} %s;\n\n" %currentName
            # Generate Union
            if length_sum % 8 != 0:
                error_info = "Bit-length of each structure is not 8's multiple"
                raise KeyError(error_info)
            content += "union u_%s\n{\n\tchar buffer[%d];\n\t%s map;\n}\n\n" %(currentName, length_sum/8, currentName)
            # Reset length_sum
            length_sum = 0
            # Set current keyName to the new keyName
            currentName = keyName
            # Generate current structure's header
            content += "typedef struct s_%s\n{\n" %currentName
        if keyLength == 1.0:
            last_is_one_bit = True
            # Throw into pool
            pool.append(fragment)
            if len(pool) == 8:
                # process pool
                content += gen_bf_structure(pool, byte_counter)
                byte_counter += 1
                pool = []
                length_sum += 8
        else:
            if last_is_one_bit and len(pool) != 0:
            # Since if last is one bit length fragment, then if all the 8 ones are processed, the pool length should be 0 cause it is reset to empty list
                raise KeyError("Not last continuous 8 entires with 1 bit length!!!")
            if keyLength % 8 != 0:
                raise ValueError("Length of Key is not 8's multiple!")
            last_is_one_bit = False
            byte_counter = 0
            length_sum += keyLength
            content += "\tchar %s[%d];\n" %(cali.strip(), int(keyLength / 8))
    # Generate last structure's tail
    content += "} %s;\n\n" %currentName
    # Generate last union
    if length_sum % 8 != 0:
        error_info = "Bit-length of each structure is not 8's multiple"
        raise KeyError(error_info)
    content += "union u_%s\n{\n\tchar buffer[%d];\n\t%s map;\n}\n\n" %(currentName, length_sum/8, currentName)

    return content



#def is_merged_cell(row, col, sheet):
#    """Check if the cell is merged
#
#    :param row: row number
#    :param length_index: col number
#    :param sheet: current sheet
#    :return: True if this cell is merged, else Flase
#    """
#    for area in sheet.merged_cells:
#        if (col,col+1) == area[2:]:
#            if row in range(area[0]+1, area[1]):
#                return True
#    return False

#-----------------------------------
#               Main
#-----------------------------------
if __name__ == "__main__":
    # Define path name
    if platform.system() == "Linux":
        INPUT_DIR_NAME = '../input/'
        OUTPUT_DIR_NAME = '../output/'
    elif platform.system() == "Windows":
        INPUT_DIR_NAME = "..\\input\\"
        OUTPUT_DIR_NAME = "..\\output\\"
    HEADER_FILE_NAME = "header.h"

    # Iterate over input excels
    excels = os.listdir(INPUT_DIR_NAME)
    excels = [excel for excel in excels if (excel.endswith(".xlsx") or excel.endswith(".xls"))]
    for excel in excels:
        print "************************\nProcessing Excel: %s\n************************" %(excel)
        # Read input excel
        excel_file = os.path.abspath(INPUT_DIR_NAME+excel)
        book = xlrd.open_workbook(excel_file)
        sheet = book.sheet_by_index(0)
        # Get the column index of each field
        key_idx = sheet.row_values(1).index('Key ID')
        value_idx = sheet.row_values(1).index('Factory Default (N-Value) Hex')
        length_idx = sheet.row_values(1).index('Item length')
        cali_idx = sheet.row_values(1).index('Calibration Name')
        name_idx = sheet.row_values(1).index('Key Name')
        # Get the end line number
        end_line = len(sheet.col(cali_idx))

        # Create binary file
        with open(OUTPUT_DIR_NAME+excel[:excel.index('.')]+'.bin', 'wb') as f:
            print "Generation %s.bin..." %(excel[:excel.index('.')])
            # Iterate over each row
            output = []
            for row_count in range(2, end_line-1):
                row = sheet.row(row_count)
                if row[key_idx].ctype is not xlrd.XL_CELL_EMPTY:                 # If every row has consistent format, just check if it is empty
                    # Input: [1(keyid), 16(length), '7'(value)]
                    fragment = binary_converter(row[key_idx], row[length_idx],row[value_idx])
                    # Output: ['\x0001'(keyid), '\x00\x10'(length), '\x00\x07'(value)]
                    output.append(fragment)

            # Merge fragments with same id to one fragment
            merge_fragment(output)
            # Manipulate the 1st fragment(Striping length & keyid infos, fill in checksum)
            fill_header(output)
            # Write to binary file
            output = [''.join(fragment) for fragment in output]
            output = ''.join(output)
            f.write(output)

        # Create header file
        with open(OUTPUT_DIR_NAME+HEADER_FILE_NAME, 'wa') as f:
            #print "Generation %s.h..." %(excel[:excel.index('.')])
            print "Generation/Appending %s...\n" %(HEADER_FILE_NAME)
            # Iterate over each row
            output = []
            for row_count in range(2, end_line-1):
                row = sheet.row(row_count)
                if row[key_idx].ctype is not xlrd.XL_CELL_EMPTY:
                    # Input: Calibration, Keylength, KeyName
                    fragment = preprocess(row[cali_idx], row[length_idx], row[name_idx])
                    output.append(fragment)
            # generate header
            content = gen_header(output)
            f.write(content)

