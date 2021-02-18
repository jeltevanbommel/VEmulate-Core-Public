import unittest

from vemulator.emulator.field_values import FieldValueList
from vemulator.scenarios.arithmetic import ArithmeticScenario
from vemulator.scenarios.gradient import GradientScenario
from vemulator.scenarios.intboundary import IntBoundaryScenario
from vemulator.scenarios.intchoice import IntChoiceScenario
from vemulator.scenarios.intfixed import IntFixedScenario
from vemulator.scenarios.intrandom import IntRandomScenario
from vemulator.scenarios.intrange import IntRangeScenario
from vemulator.scenarios.mapping import MappingScenario
from vemulator.scenarios.regex import RegexScenario
from vemulator.scenarios.selectrandom import SelectRandomParentScenario
from vemulator.scenarios.stringboundary import StringBoundaryScenario
from vemulator.scenarios.stringchoice import StringChoiceScenario
from vemulator.scenarios.stringfixed import StringFixedScenario
from vemulator.scenarios.stringrandom import StringRandomScenario
from vemulator.scenarios.stringunicode import StringUnicodeScenario


class ScenarioTester(unittest.TestCase):
    def test_int_fixed_scenario(self):
        """
        Test the IntFixed scenario
        """
        field_values = FieldValueList()
        scenario = IntFixedScenario({'value': 10, 'amount': 10, 'bits': 8})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertEqual(scenario.get_value(), 10)
            self.assertEqual(scenario.get_hex_value(), '0A')

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = IntFixedScenario({'value': 10, 'amount': 10, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 10):
            values.append(scenario.generate_next(field_values))
        self.assertEqual({10}, set(values))  # Validate that fuzzing a fixed value still returns a fixed value

    def test_int_random_scenario(self):
        """
        Test the IntRandom scenario
        """
        field_values = FieldValueList()
        scenario = IntRandomScenario({'min': 1, 'max': 10, 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertTrue(1 <= scenario.get_value() <= 10)

        self.assertTrue(scenario.is_complete())

    def test_int_range_scenario(self):
        """
        Test the IntRange scenario
        """
        field_values = FieldValueList()
        scenario = IntRangeScenario({'min': 1, 'max': 10, 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertTrue(1 <= scenario.get_value() <= 10)

        self.assertTrue(scenario.is_complete())

    def test_int_choice_scenario(self):
        """
        Test the IntChoice scenario
        """
        field_values = FieldValueList()
        scenario = IntChoiceScenario({'choices': [2, 4, 6], 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [2, 4, 6])

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = IntChoiceScenario({'choices': [2, 4, 6], 'amount': 10, 'generation': 'fuzzing'})
        for i in range(0, 10):
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [2, 4, 6])

    def test_int_boundary_scenario(self):
        """
        Test the IntBoundary scenario
        """
        field_values = FieldValueList()
        scenario = IntBoundaryScenario({'min': 1, 'max': 10, 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertTrue(1 <= scenario.get_value() <= 10)

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = IntBoundaryScenario({'min': 0, 'max': 10, 'amount': 10, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 4):
            values.append(scenario.generate_next(field_values))
        self.assertEqual({0, 1, 9, 10}, set(values))  # Validate that values just inside boundary are generated

        scenario = IntBoundaryScenario({'min': 0, 'max': 10, 'amount': 10, 'strict': False, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 6):
            values.append(scenario.generate_next(field_values))
        self.assertEqual({-1, 0, 1, 9, 10, 11}, set(values))  # Validate that values around boundary are generated

    def test_arithmetic_scenario(self):
        """
        Test the Arithmetic scenario
        """
        field_values = FieldValueList()
        field_values.put_field_value('V', 5)
        field_values.put_field_value('A', 3)
        scenario = ArithmeticScenario({'value': 'V * A'})
        scenario.generate_next(field_values)
        self.assertEqual(scenario.get_value(), 15)

    def test_gradient_scenario(self):
        """
        Test the Gradient scenario
        """
        field_values = FieldValueList()
        scenario = GradientScenario({'gradient_type': 'square', 'amount': 4})
        for i in range(0, 4):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertEqual(scenario.get_value(), i**2)
        self.assertTrue(scenario.is_complete())

        scenario = GradientScenario({'gradient_type': 'x**3', 'amount': 4})
        for i in range(0, 4):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertEqual(scenario.get_value(), i**3)
        self.assertTrue(scenario.is_complete())

    def test_mapping_scenario(self):
        """
        Test the Mapping scenario
        """
        field_values = FieldValueList()
        scenario = MappingScenario({'dict': {'A': 1, 'B': 2, 'C': 3, 'D': 4}, 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [1, 2, 3, 4])

        # Fuzzing
        scenario = MappingScenario({'dict': {'A': 1, 'B': 2, 'C': 3, 'D': 4}, 'amount': 10, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 4):
            values.append(scenario.generate_next(field_values))

        self.assertEqual({1, 2, 3, 4}, set(values))

    def test_regex_scenario(self):
        """
        Test the Regex scenario
        """
        field_values = FieldValueList()
        regex = '[0-9a-zA-Z]*'
        scenario = RegexScenario({'value': regex, 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertRegex(scenario.get_value(), regex)

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        field_values = FieldValueList()
        scenario = RegexScenario({'value': '[0-9a-zA-Z]{5,15}', 'amount': 10, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 2):
            values.append(scenario.generate_next(field_values))

        self.assertEqual({5, 15}, {len(value) for value in values})

    def test_select_random_scenario(self):
        """
        Test the SelectRandom scenario
        """
        field_values = FieldValueList()
        scenario = SelectRandomParentScenario({'values': [
            IntFixedScenario({'value': 1, 'amount': 1}),
            StringFixedScenario({'value': '---', 'amount': 1})
        ], 'loop': True, 'amount': 10})

        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [1, '---'])

        self.assertTrue(scenario.is_complete())

        scenario.reset()
        scenario.loop = False

        for i in range(0, 2):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [1, '---'])

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = SelectRandomParentScenario({'values': [
            IntFixedScenario({'value': 1, 'amount': 1}),
            StringFixedScenario({'value': '---', 'amount': 1})
        ], 'loop': True, 'amount': 10, 'generation': 'fuzzing'})
        for i in range(0, 10):
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [1, '---'])

    def test_string_fixed_scenario(self):
        """
        Test the StringFixed scenario
        """
        field_values = FieldValueList()
        scenario = StringFixedScenario({'value': 'Test', 'amount': 10, 'bits': 8})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertEqual(scenario.get_value(), 'Test')
            self.assertEqual(scenario.get_hex_value(), '54657374')  # 54657374 = ASCII 'Test' hex encoded

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = IntFixedScenario({'value': 'Test', 'amount': 10, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 10):
            values.append(scenario.generate_next(field_values))
        self.assertEqual({'Test'}, set(values))  # Validate that fuzzing a fixed value still returns a fixed value

    def test_string_boundary_scenario(self):
        """
        Test the StringBoundary scenario
        """
        field_values = FieldValueList()
        scenario = StringBoundaryScenario({'min_length': 0, 'max_length': 10, 'amount': 10, 'allowed_chars': [['a', 'd'], 'xy']})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertTrue(0 <= len(scenario.get_value()) <= 10)
            for char in scenario.get_value():
                self.assertIn(char, 'abcdxy')

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = StringBoundaryScenario({'min_length': 5, 'max_length': 10, 'amount': 10, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 4):
            values.append(scenario.generate_next(field_values))
        self.assertEqual({5, 6, 9, 10}, {len(value) for value in values})  # Validate that values just inside boundary are generated

        scenario = StringBoundaryScenario({'min_length': 5, 'max_length': 10, 'amount': 10, 'strict': False, 'generation': 'fuzzing'})
        values = []
        for i in range(0, 6):
            values.append(scenario.generate_next(field_values))
        self.assertEqual({4, 5, 6, 9, 10, 11}, {len(value) for value in values})  # Validate that values around boundary are generated

    def test_string_choice_scenario(self):
        """
        Test the StringChoice scenario
        """
        field_values = FieldValueList()
        scenario = StringChoiceScenario({'choices': [chr(65+i) for i in range(0, 10)], 'amount': 10})
        for i in range(0, 10):
            self.assertFalse(scenario.is_complete())
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [chr(65+i) for i in range(0, 10)])

        self.assertTrue(scenario.is_complete())

        # Fuzzing
        scenario = StringChoiceScenario({'choices': [chr(65+i) for i in range(0, 10)], 'amount': 10, 'generation': 'fuzzing'})
        for i in range(0, 10):
            scenario.generate_next(field_values)
            self.assertIn(scenario.get_value(), [chr(65+i) for i in range(0, 10)])

    def test_string_random_scenario(self):
        """
        Test the StringRandom scenario
        """
        field_values = FieldValueList()
        scenario = StringRandomScenario({'min_length': 1, 'max_length': 10, 'amount': 10})
        for i in range(0, 10):
            scenario.generate_next(field_values)
            self.assertTrue(1 <= len(scenario.get_value()) <= 10)

        self.assertTrue(scenario.is_complete())

    def test_string_unicode_scenario(self):
        """
        Test the StringUnicode scenario
        """
        field_values = FieldValueList()
        scenario = StringUnicodeScenario({'min_length': 1, 'max_length': 10, 'amount': 10})
        for i in range(0, 10):
            scenario.generate_next(field_values)
            self.assertTrue(1 <= len(scenario.get_value()) <= 10)

        self.assertTrue(scenario.is_complete())

    def test_gradient_scenario_result_invalidity(self):
        """
        Test that no values in the invalid list are generated, using the Gradient scenario
        """
        field_values = FieldValueList()
        min = 0
        max = 10
        step_size = 1
        invalid = [1]
        scenario1 = GradientScenario({'gradient_type': 'linear', 'step_size': step_size, 'min': min, 'max': max, 'invalid': invalid})
        scenario2 = GradientScenario({'gradient_type': 'linear', 'step_size': step_size, 'min': min, 'max': max})
        results1 = []
        results2 = []
        for i in range(int((max-min)/step_size)):
            scenario1.generate_next(field_values)
            scenario2.generate_next(field_values)
            results1.append(scenario1.get_value())
            results2.append(scenario2.get_value())

        self.assertTrue(not any([r in invalid for r in results1]))
        self.assertTrue(any([r in invalid for r in results2]))
