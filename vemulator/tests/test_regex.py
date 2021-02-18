import unittest

from vemulator.util.regex import RegexToString


class RegexTestCase(unittest.TestCase):

    def test_regex_valid_string_generation(self):
        """
        Test the RegexToString.create_valid_string function
        """
        regexes = [
            '[0-9a-zA-Z]*',
            '([0-9]{4})|([a-z]{2})*.[^a]',
            '^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$',
            '^[A-Z]{2}\d{2} (?:\d{4} ){3}\d{4}(?: \d\d?)?$',
            '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
        ]
        for regex in regexes:
            self.assertRegex(RegexToString(regex).create_valid_string(), regex)

    def test_regex_min_length(self):
        """
        Test if RegexToString correctly determines the minimum length of a string
        """
        self.assertEqual(len(RegexToString('[0-9]{5,15}').create_min_invalid_string()), 5)

    def test_regex_max_length(self):
        """
        Test if RegexToString correctly determines the maximum length of a string
        """
        self.assertEqual(len(RegexToString('[0-9]{5,15}').create_max_invalid_string()), 15)
