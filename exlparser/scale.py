#!/usr/bin/env python
#-*- coding=utf-8 -*-
# Author: Zhaoting Weng
# Created Time: Mon 22 Dec 2014 08:16:38 AM CET

import binascii

def dec_int_to_binary_real(num, length = None):
    """Convert decimal integer to binary with fixed bit length

    :param num: Decimal integer number.
    :param length: Expected bit length of the converted binary if presented.
                   Default is None, which reustls into the least suitable number of bytes.
    :return: Converted binary.

    >>> dec_int_to_binary_real(500, 32)
    '\\x00\\x00\\x01\\xf4'
    """
    if type(num) is not type(0):
        raise TypeError("Type of argumnet is not integer!")
    str_hex = hex(num)[2:]
    # Pad a leading 0 if str_hex is not even length
    if len(str_hex) % 2 == 1:
        str_hex = '0' + str_hex
    if length is not None:
        if type(length) is not type(0):
            raise TypeError("Type of argumnet is not integer!")
        if len(bin(num))-2 > length:
            raise ValueError("Expected bit length less than necessary bit length!!!")
        else:
            str_hex = str_hex.zfill(length/4)
    return binascii.a2b_hex(str_hex)

def binary_real_to_dec_int(bin_num):
    """Convert binary to decimal integer

    :param bin_num: Binary
    :return: Converted decimal integer

    >>> binary_real_to_dec_int('\x01\xf4')
    500
    """
    return int(binascii.b2a_hex(bin_num), 16)

def hex_int_to_dec_int(hex_num):
    """Convert hexdecimal integer to decimal integer

    :param hex_num: hexdecimal integer
    :return: decimal integer

    >>> hex_int_to_dec_int(10)
    16
    """
    if type(hex_num) is not type(0):
        raise TypeError("Input hexdecimal number is not integer")
    remainders = []
    while hex_num != 0:
        remainders.append(hex_num % 10)
        hex_num = hex_num / 10
    out = 0
    i = 0
    for r in remainders:
        out += 16**i * r
        i += 1
    return out

def binary_real_to_binary_repr(bin_num):
    """Convert binary to its representation

    :param bin_num: Binary
    :return: Binary representation

    >>> binary_real_to_binary_repr('\x7f')
    '1111111'
    >>> binary_real_to_binary_repr('\x01')
    '1'
    """
    return bin(int(binascii.b2a_hex(bin_num), 16))[2:]

def binary_repr_to_binary_real(bin_repr):
    """Convert binary representation to binary.

    :param bin_repr: Binary representation.
    :return: Binary

    >>> binary_repr_to_binary_real('1111111')
    '\\x7f'
    """
    return dec_int_to_binary_real(int(bin_repr,2))

def extend_string_to_fix_length(string, length):
    """Extend string to fix length(bit)

    :param string: Ascii string
    :param length: Expected bit length of string.
    :return: Extended string.

    >>> extend_string_to_fix_length('abc', 32)
    'abc\\x00'
    """
    if type(string) is not type(''):
        raise TypeError("Type of argumnet is not string!")
    if type(length) is not type(0):
        raise TypeError("Type of argumnet is not integer!")
    if len(string) * 8 > length:
        raise ValueError("Expected bit length less than necessary bit length!!!")
    diff = (length - len(string) * 8)   #(bit)
    if diff % 8 != 0:
        raise ValueError("Length is not 8's magnification")
    string =  string + '\x00' * (diff/8)
    return string

def int_repr_to_binary_real(num, length=None):
    """Convert integer which has the binary representation, to binary. With bit-length: length, if length is 1, return value is of 8 bits.

    :param num: Integer with binary representation.
    :param length: Expected binary length.
    :return: Binary with specific length.

    >>> int_repr_to_binary_real(1015, 32)
    '\\x00\\x00\\x10\\x15'
    >>> int_repr_to_binary_real(0, 32)
    '\\x00\\x00\\x00\\x00'
    >>> int_repr_to_binary_real(0)
    '\\x00'
    >>> int_repr_to_binary_real(1, 1)
    '\\x01'
    """
    if type(num) is not type(0):
        raise TypeError("Type of argument is not integer!")
    tmp = num
    if tmp == 0:
        l = [0]
    else:
        l = []
        while tmp > 0:
            l.append(tmp % 10)
            tmp = tmp / 10
    l.reverse()
    hex_str = ''.join([chr(ord('0')+i) for i in l])
    if len(hex_str) % 2 == 1:
        hex_str = '0' + hex_str
    if length is not None:
        if type(length) is not type(0):
            raise TypeError("Type of argumnet is not integer!")
        if length < len(bin(num))-2:
            raise ValueError("Expected bit length less than necessary bit length!!!")
        else:
            hex_str = hex_str.zfill(length/4)
    return binascii.a2b_hex(hex_str)

def twos_complement(num, bit_count):
    """Compute 2's complement.

    :param num: Integer.
    :param bit_count: Number of bit.

    >>> twos_complement(11, 8)
    245
    """
    return (1 << bit_count) - num
