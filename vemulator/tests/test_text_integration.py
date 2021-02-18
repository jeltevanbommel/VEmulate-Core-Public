import unittest
from unittest import mock

from vemulator.configuration.config import EmulatorConfig
from vemulator.emulator.emulator import Emulator
from vemulator.output.outputinterface import OutputInterface
from vemulator.util.text import check_checksum


class TextIntegrationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EmulatorConfig()
        self.config.set_delay(0)

        self.output = mock.create_autospec(OutputInterface)
        self.output.available.return_value = True
        self.config.set_output(self.output)

    def test_int_fixed_in_message(self):
        """
        Test the IntFixed scenario in an integration test
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                values:
                  - type: IntFixed
                    amount: 2
                    value: 1
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_occurrences = 0
        for message in self.__get_outputted_messages():
            if b'\r\nV\t1' in message:
                message_occurrences += 1
        self.assertEqual(message_occurrences, 2)

    def test_string_fixed_in_message(self):
        """
        Test the StringFixed scenario in an integration test
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                values:
                  - type: StringFixed
                    amount: 2
                    value: ---
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_occurrences = 0
        for message in self.__get_outputted_messages():
            if b'\r\nV\t---' in message:
                message_occurrences += 1
        self.assertEqual(message_occurrences, 2)

    def test_loop_in_message(self):
        """
        Test the Loop scenario in an integration test
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                values:
                  - type: Loop
                    amount: 2
                    values:
                      - type: IntFixed
                        amount: 2
                        value: 1
                      - type: IntFixed
                        amount: 2
                        value: 2
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_values = []
        for message in self.__get_outputted_messages():
            if b'\r\nV\t1' in message:
                message_values.append(1)
            elif b'\r\nV\t2' in message:
                message_values.append(2)
        self.assertEqual(message_values, [1, 1, 2, 2, 1, 1, 2, 2])

    def test_arithmetic_in_message(self):
        """
        Test the Arithmetic scenario in an integration test
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                values:
                  - type: IntFixed
                    amount: 2
                    value: 2
              - name: Amperage
                key: A
                values:
                  - type: IntFixed
                    amount: 3
                    value: 3
              - name: Power
                key: W
                values:
                  - type: Arithmetic
                    value: V * A
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_occurrences = 0
        for message in self.__get_outputted_messages():
            if b'\r\nW\t6' in message:
                message_occurrences += 1
        self.assertEqual(message_occurrences, 3)

    def test_bitbuffer_in_message(self):
        """
        Test the Bitbuffer scenario in an integration test
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                values:
                  - type: BitBuffer
                    values:
                      - type: IntFixed
                        bits: 5
                        amount: 2
                        value: 1
                      - type: IntFixed
                        bits: 3
                        amount: 3
                        value: 2
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_occurrences = 0
        for message in self.__get_outputted_messages():
            if b'\r\nV\t10' in message:  # 10 = (1 << 3) + 2
                message_occurrences += 1
        self.assertEqual(message_occurrences, 2)

    def test_mapping_in_message(self):
        """
        Test the Mapping scenario in an integration test
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Enabled
                key: E
                values:
                  - type: Mapping
                    amount: 2
                    dict: { 'OFF': 'OFF', 'ON': 'ON' }
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_occurrences = 0
        for message in self.__get_outputted_messages():
            if b'\r\nE\tOFF' in message or b'\r\nE\tON' in message:  # 10 = (1 << 3) + 2
                message_occurrences += 1
        self.assertEqual(message_occurrences, 2)

    def test_preset_random_in_message(self):
        """
        Test the random preset
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            preset: test
            preset_fields:
              - v: random
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        message_occurrences = 0
        for message in self.__get_outputted_messages():
            if b'\r\nV\t1' in message:
                message_occurrences += 1
        self.assertEqual(message_occurrences, 1)

    def test_checksum_in_message(self):
        """
        Check that a checksum is added to the message and that it is valid
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                unit: V
                values:
                  - type: IntFixed
                    amount: 2
                    value: 1
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        checksums_valid = True
        for message in self.__get_outputted_messages():
            checksums_valid = message.count(b'Checksum') == 1  # Only one Checksum per message
            checksums_valid = checksums_valid and check_checksum(message)  # Checksum is valid
            if not checksums_valid:
                break
        self.assertTrue(checksums_valid)

    def test_not_split_message(self):
        """
        Check that a message is not split if it is not too long
        """
        fields = []
        for i in range(0, 21):
            fields.append({
                'name': chr(65 + i),
                'key': chr(65 + i),
                'values': [
                    {
                        'type': 'IntFixed',
                        'amount': 1,
                        'value': 1
                    }
                ]
            })

        self.config.set_config_dict({
            'device': 'Device',
            'name': 'TextTest',
            'protocol': 'text',
            'fields': fields
        })
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        messages = self.__get_outputted_messages()

        self.assertEqual(len(messages), 1)

    def test_split_message(self):
        """
        Check that a message that is too long is split into multiple messages
        """
        fields = []
        for i in range(0, 22):
            fields.append({
                'name': chr(65 + i),
                'key': chr(65 + i),
                'values': [
                    {
                        'type': 'IntFixed',
                        'amount': 1,
                        'value': 1
                    }
                ]
            })

        self.config.set_config_dict({
            'device': 'Device',
            'name': 'TextTest',
            'protocol': 'text',
            'fields': fields
        })
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        messages = self.__get_outputted_messages()

        self.assertEqual(len(messages), 2)

        messages_fields = []

        for message in messages:
            message_fields = []
            for line in message.split(b'\r\n'):
                field = line.split(b'\t')
                if len(field) == 2:
                    message_fields.append(field[0])
            messages_fields.append(message_fields)

        for message_fields in messages_fields:
            # Message has at most 22 fields
            self.assertLessEqual(len(message_fields), 22)

        # Verify that all fields are only sent once, apart from the Checksum, which should be in every message
        self.assertEqual([b'Checksum'], [field for field in messages_fields[0] if field in messages_fields[1]])

    def test_bit_error(self):
        """
        Test if adding bit errors works properly
        We can unfortunately not unit test for corrupting the checksum since there is still a small chance that
        the checksum is still correct after adding bit errors
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                unit: V
                values:
                  - type: IntFixed
                    amount: 2
                    value: 1
            """)
        self.config.create_scenarios()
        self.config.set_bit_error_rate(0.5)
        self.config.set_bit_error_checksum(False)
        emulator = Emulator(self.config)
        emulator.run()

        for message in self.__get_outputted_messages():
            self.assertNotEqual(b'\r\nV\t1\r\nChecksum\t\x06', message)  # Check if the message is corrupted
            self.assertTrue(check_checksum(message))  # Check if the checksum is still correct

    def test_determinism(self):
        """
        Test that the emulator is deterministic
        """
        self.config.set_config("""
            device: Device
            name: TextTest
            protocol: text
            fields: 
              - name: Voltage
                key: V
                unit: V
                values:
                  - type: IntRandom
                    amount: 100
                    min: -1000
                    max: 1000
            """)
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        first_run_messages = self.__get_outputted_messages()

        # Reset output
        self.output = mock.create_autospec(OutputInterface)
        self.output.available.return_value = True
        self.config.set_output(self.output)

        # Do a second run
        self.config.create_scenarios()
        emulator = Emulator(self.config)
        emulator.run()

        second_run_messages = self.__get_outputted_messages()

        self.assertEqual(first_run_messages, second_run_messages)

    def __get_outputted_messages(self):
        """
        Get a list of messages that was written to the output
        :return: list of messages
        :rtype: list[bytes]
        """
        return [args.args[0] for args in self.output.write.call_args_list]

