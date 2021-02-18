import unittest

from vemulator.util import text


class TextTestCase(unittest.TestCase):
    def test_add_checksum(self):
        """
        Test the text.add_checksum function
        """
        self.assertEqual(text.add_checksum(b'\r\nField\tValue'), b'\r\nField\tValue\r\nChecksum\t\xAC')

    def test_check_checksum(self):
        """
        Test the text.check_checksum function
        """
        self.assertTrue(text.check_checksum(b'\r\nField\tValue\r\nChecksum\t\xAC'))
        self.assertFalse(text.check_checksum(b'\r\nField\tValue\r\nChecksum\t0'))
