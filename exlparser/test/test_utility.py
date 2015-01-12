#!/usr/bin/env python
# -*- coding: utf-8 -*-

#########################################################################
# Author: Zhaoting Weng
# Created Time: Mon 22 Dec 2014 10:45:18 PM CST
# File Name: test_exchanger.py
# Description:
#########################################################################

import unittest
from exlparser.utility import merge_fragment, merge_bit_pool, checksum, gen_bf_structure

class TestExchanger(unittest.TestCase):

    def setUp(self):
        pass

    def test_merge_fragment(self):
        frags = [['\x00\x01','\x00\x10','\x7f'],
                 ['\x00\x01','\x00\x01','\x01'],['\x00\x01','\x00\x01','\x00'],
                 ['\x00\x01','\x00\x01','\x01'],['\x00\x01','\x00\x01','\x00'],
                 ['\x00\x01','\x00\x01','\x01'],['\x00\x01','\x00\x01','\x00'],
                 ['\x00\x01','\x00\x01','\x01'],['\x00\x01','\x00\x01','\x00'],
                 ['\x00\x01','\x00\x10','\x7f'],
                 ['\x00\x02','\x00\x10','\x7f']]
        merge_fragment(frags)
        self.assertEqual(frags,[['\x00\x01', '\x00\x28', '\x7f\xAA\x7f'],['\x00\x02','\x00\x10','\x7f']])

    def test_merge_bit_pool(self):
        bit_pool = ['\x01', '\x00', '\x01', '\x01', '\x00', '\x00', '\x00', '\x01',
                    '\x01', '\x01', '\x01', '\x01', '\x00', '\x00', '\x00', '\x00']
        self.assertEqual(merge_bit_pool(bit_pool), '\xb1\xf0')

    def test_checksum(self):
        self.assertEqual(checksum(['\x12\x34', '\x77\x88']), 'vD')

    def test_gen_bf_structure(self):
        pool = [["Bit_7", 1.0, "myKeyName"],
                ["Bit_6", 1.0, "myKeyName"],
                ["Bit_5", 1.0, "myKeyName"],
                ["Bit_4", 1.0, "myKeyName"],
                ["Bit_3", 1.0, "myKeyName"],
                ["Bit_2", 1.0, "myKeyName"],
                ["Bit_1", 1.0, "myKeyName"],
                ["Bit_0", 1.0, "myKeyName"]]
        byte_counter = 5
        self.assertEqual(gen_bf_structure(pool, 5), '\tstruct s_myKeyNameBYTE5\n\t{\n\t\tchar Bit_7: 1;\n\t\tchar Bit_6: 1;\n\t\tchar Bit_5: 1;\n\t\tchar Bit_4: 1;\n\t\tchar Bit_3: 1;\n\t\tchar Bit_2: 1;\n\t\tchar Bit_1: 1;\n\t\tchar Bit_0: 1;\n\t} myKeyNameBYTE5;\n\n')


if __name__ == "__main__":
    unittest.main()
