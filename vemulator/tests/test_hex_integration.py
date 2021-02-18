import unittest
from unittest import mock

from vemulator.configuration.config import EmulatorConfig
from vemulator.emulator.emulator import Emulator
from vemulator.input.testinput import TestInput
from vemulator.output.outputinterface import OutputInterface


class HexIntegrationTestCase(unittest.TestCase):
    emulator_config = """
    device: Device
    name: HexTest
    protocol: text_hex
    version: 0x1234
    product_id: 0x5678
    fields: 
      - name: Voltage
        key: V
        unit: V
        values:
          - type: IntFixed
            amount: 1
            value: 1
    hex_fields: 
      - name: Voltage
        key: 0x1234
        unit: V
        values:
          - type: IntFixed
            amount: 2
            value: 0xF00F
            bits: 16
      - name: Amperage
        key: 0x1235
        unit: A
        writable: true
        values:
          - type: IntFixed
            amount: 2
            value: 0x0FF0
            bits: 16
      - name: VA
        key: 0x1236
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
    """

    def setUp(self) -> None:
        self.config = EmulatorConfig()
        self.config.set_config(self.emulator_config)
        self.config.set_delay(0)
        self.config.create_scenarios()

        self.input = TestInput()
        self.config.set_input(self.input)

        self.output = mock.create_autospec(OutputInterface)
        self.output.available.return_value = True
        self.config.set_output(self.output)

        self.emulator = Emulator(self.config)

    def test_boot(self):
        """
        Try sending a boot command
        """
        self.input.writeline(b':051FA51FA51FA51FA51FADE\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':4000051\n')

    def test_ping(self):
        """
        Try sending a ping
        """
        self.input.writeline(b':154\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':534120A\n')

    def test_version(self):
        """
        Try getting the firmware version
        """
        self.input.writeline(b':352\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':134120E\n')

    def test_product_id(self):
        """
        Try getting the product id
        """
        self.input.writeline(b':451\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':1785686\n')

    def test_get_exists(self):
        """
        Try getting an existing field
        """
        self.input.writeline(b':734120008\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':73412000FF009\n')

    def test_get_not_exists(self):
        """
        Try getting a non-existing field
        """
        self.input.writeline(b':712340008\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':712340107\n')

    def test_set_writable(self):
        """
        Try writing to a writable hex field
        """
        self.input.writeline(b':83512001234C0\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':83512001234C0\n')

    def test_set_not_writable(self):
        """
        Try writing to a read-only hex field
        """
        self.input.writeline(b':83412001234C1\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':83412020FF006\n')

    def test_set_not_exists(self):
        """
        Try writing a non-existing field
        """
        self.input.writeline(b':81234001234C1\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':812340106\n')

    def test_set_invalid_size(self):
        """
        Try setting a field with too many bytes
        """
        self.input.writeline(b':83512001234566A\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':8351204F00F03\n')

    def test_unknown_command(self):
        """
        Try sending an unknown command
        """
        self.input.writeline(b':253\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':3020050\n')

    def test_invalid_checksum(self):
        """
        Try sending a command with an invalid checksum
        """
        self.input.writeline(b':155\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':4AAAAFD\n')

    def test_bitbuffer(self):
        """
        Test the bitbuffer scenario
        """
        self.input.writeline(b':736120006\n')
        self.emulator.run()
        self.output.write.assert_any_call(b':73612000AFC\n')

    def test_preset_random_in_message(self):
        """
        Test the random hex preset
        """
        config = EmulatorConfig()
        config.set_config("""
            device: Device
            name: TextTest
            protocol: hex
            version: 0x1234
            product_id: 0x5678
            fields: 
              - name: Voltage
                key: V
                unit: V
                values:
                  - type: IntFixed
                    amount: 1
                    value: 1
            preset: test
            preset_hex_fields:
              - v_hex: random
            """)
        config.set_delay(0)
        config.create_scenarios()

        config.set_input(self.input)
        config.set_output(self.output)

        emulator = Emulator(config)

        self.input.writeline(b':734120008\n')
        emulator.run()
        self.output.write.assert_any_call(b':73412000FF009\n')
