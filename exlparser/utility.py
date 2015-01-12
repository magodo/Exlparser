#!/usr/bin/env python
#-*- coding=utf-8 -*-
# Author: Zhaoting Weng
# Created Time: Fri 9 Jua 2015 04:30:38 PM CET

from scale import *
from collections import OrderedDict

def merge_bit_pool(bit_pool):
    """Merge 1-valid-bit byte to bytes

    :param bit_pool: List of 1-bit byte
    :return: Merged byte(s)
    """
    if len(bit_pool) % 8 != 0:
        raise ValueError("1-bit length item number is not 8 or 8's multiple")
    byte_count = len(bit_pool) / 8
    output = []
    for i in range(byte_count):
        output.append(''.join([binary_real_to_binary_repr(binary) for binary in bit_pool[i*8: (i+1)*8]]))
    return ''.join([binary_repr_to_binary_real(i) for i in output])

def merge_fragment(fragments):
    """Merge fragments with same id to one fragment internally.

    :param fragments: List includes all fragments.
    :return: Number of merged cells.
    """
    count = 0

    # Since there're multiple fragments in fragments with same keyid
    keyid_set = list(OrderedDict.fromkeys([frg[0] for frg in fragments]))

    for keyid in keyid_set:
        keyid_list = [frg[0] for frg in fragments]
        start_idx = keyid_list.index(keyid)
        end_idx = len(keyid_list) - keyid_list[::-1].index(keyid) - 1
        count += end_idx - start_idx + 1

        new_fragment = [keyid]
        bit_pool = []
        last_is_one_bit = False
        length_sum = 0   #(bit)
        value_sum = ''

        for frg in fragments[start_idx: end_idx+1]:
            # 1. Merge length
            length_sum += binary_real_to_dec_int(frg[1])
            # 2. Merge value
            if frg[1] == '\x00\x01':
                # 1-bit width and not the end
                last_is_one_bit = True
                bit_pool.append(frg[2])
            else:
                if last_is_one_bit:
                    last_is_one_bit = False
                    # Process bit pool
                    value_sum += merge_bit_pool(bit_pool)
                    # Empty bit_pool
                    bit_pool = []
                value_sum += frg[2]
        # Till last item still 1-bit width value
        if bit_pool:
                value_sum += merge_bit_pool(bit_pool)
                # Empty bit_pool
                bit_pool = []

        # Merge same keyid fragments to one new fragment
        new_fragment.append(dec_int_to_binary_real(length_sum, 16))
        new_fragment.append(value_sum)
        # Doing change internally
        fragments[start_idx: end_idx+1] = [new_fragment]
    return count


def checksum(seq):
    """ Calculate checksum.

    :param seq: List of 2-byte binary.
    :return: Binary checksum
    """
    seq = map(lambda x: int(binascii.b2a_hex(x), 16), seq)
    return dec_int_to_binary_real(twos_complement(sum(seq) % (2 ** 16), 16), 16)

def gen_bf_structure(pool, byte_counter):
    """Generate string representing a structure from list-pool

    :param pool: List of fragment each with following format:
                [cali(char), keyLength(float)(== 1.0), keyName(char)]
    :param byte_counter: The "byte_counter"th bit_field structure

    :return: String representing structure
    """
    content = "\tstruct s_%sBYTE%d\n\t{\n" %(pool[0][2], byte_counter)
    for fragment in pool:
        content += "\t\tchar %s: 1;\n" %fragment[0]
    content += "\t} %sBYTE%d;\n\n" %(pool[0][2], byte_counter)
    return content

