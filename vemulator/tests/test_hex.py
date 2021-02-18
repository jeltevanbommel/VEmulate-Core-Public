import unittest

from vemulator.util import hex


class HexTestCase(unittest.TestCase):
    def test_calculate_checksum(self):
        """
        Test the hex.calculate_checksum function
        """
        checksum = int(hex.calculate_checksum('{:02x}'.format(0x1234)), 16)
        self.assertEqual(0x12 + 0x34 + checksum & 0xFF, 0x55)

    def test_check_checksum(self):
        """
        Test the hex.check_checksum function
        """
        self.assertTrue(hex.check_checksum('12340F'))
        self.assertFalse(hex.check_checksum('12340E'))

    def test_create_message(self):
        """
        Test the hex.create_message function
        """
        # Test with int as command
        self.assertEqual(
            hex.create_message(1, '1234'),
            bytes(':11234'+hex.calculate_checksum('11234')+'\n', 'ascii')
        )
        # Test with string as command
        self.assertEqual(
            hex.create_message('A', '1234'),
            bytes(':A1234'+hex.calculate_checksum('A1234')+'\n', 'ascii')
        )

    def test_int_to_hex_string(self):
        """
        Test the hex.int_to_hex_string function
        """
        self.assertEqual(hex.int_to_hex_string(0xAB12, 2), '12AB')
        self.assertEqual(hex.int_to_hex_string(0xAB12, 4), '12AB0000')

    def test_string_to_hex_string(self):
        """
        Test the hex.string_to_hex_string function
        """
        self.assertEqual(hex.string_to_hex_string('Test'), '54657374')
        self.assertEqual(hex.string_to_hex_string('Test', 6), '546573740000')