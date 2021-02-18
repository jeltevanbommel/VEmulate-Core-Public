import unittest

from vemulator.emulator.field_values import FieldValueList


class FieldValueListTestCase(unittest.TestCase):
    def test_field_value_list(self):
        """
        Test the functionality of the FieldValueList class
        """
        values = FieldValueList()
        self.assertEqual({}, values.get_field_values())
        self.assertEqual(None, values.get_field_value('A'))
        self.assertEqual(None, values.get_hex_field_value('0A'))

        values.put_field_value('A', 1)
        self.assertEqual({'A': 1}, values.get_field_values())
        self.assertEqual(1, values.get_field_value('A'))

        values.put_hex_field_value('A', '0A')
        self.assertEqual('0A', values.get_hex_field_value('A'))
