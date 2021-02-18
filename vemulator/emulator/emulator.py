import re
import time
from random import Random

from observable import Observable

from .field_values import FieldValueList
from ..events.event_queue import EventQueue
from ..scenarios.arithmetic import ArithmeticScenario
from ..util import hex
from ..util import text
from ..util.log import init_logger


class Emulator:
    logger = None
    run_time = 0  # Time in seconds the emulator is running

    def __init__(self, config):
        """
        Instantiate a new emulator
        :param config: config to use
        :type config: configuration.config.EmulatorConfig
        """
        self.logger = init_logger(__name__)

        if not config.is_initialized():
            self.logger.error('Config is not properly initialized, exiting emulator')
            raise Exception('Config is not properly initialized')

        self.config = config
        self.text_scenarios = config.get_text_scenarios()
        self.hex_scenarios = config.get_hex_scenarios()
        self.overwritten_text_scenarios = dict()
        self.overwritten_hex_scenarios = dict()
        self.input = config.get_input()
        self.output = config.get_output()
        self.keys = list(self.text_scenarios.keys())
        self.field_values = FieldValueList()
        self.paused = False
        self.stopped = False
        self.status = 'initialized'
        self.bit_error_random = Random(config.get_default_seed())
        self.observable = Observable()
        self.timed = self.config.get_timed()
        self.stop_condition = self.config.get_stop_condition()
        if self.timed:
            self.event_queue = EventQueue(self)

    def __send_message(self, message):
        """
        Send a text message
        :param message: dict of message fields
        :type message: dict
        """
        message_max_len = 21 # Max length is 22 including Checksum
        if len(message) > message_max_len:
            # We need to split up the message
            # First we check if we can just move the H fields to a new message
            h_message = {}
            non_h_message = {}
            h_pattern = re.compile('^H[0-9]+$')
            for key, value in message.items():
                if h_pattern.match(key):
                    h_message[key] = value
                else:
                    non_h_message[key] = value

            if 0 < len(h_message) < message_max_len:
                self.logger.debug('Splitting message into part with non H and H fields')
                self.__send_message(non_h_message)
                self.__send_message(h_message)
            else:
                # Removing the H messages does not help, just split evenly
                self.logger.debug('Splitting message into two halves')
                split_index = len(message) // 2
                dict_items = list(message.items())
                self.__send_message(dict(dict_items[:split_index]))
                self.__send_message(dict(dict_items[split_index:]))

        else:
            text_message = b''
            for key, value in message.items():
                text_message = text_message + b'\r\n' + bytes(str(key), 'utf-8') + b'\t' + bytes(str(value), 'utf-8')

            if self.config.get_bit_error_rate() > 0.0 and self.config.get_bit_error_checksum() is False:
                # Add bit errors, but do not add errors to the checksum
                text_message = text.bit_error(text_message, self.config.get_bit_error_rate(), self.bit_error_random)

            text_message = text.add_checksum(text_message)
            if text.check_checksum(text_message):
                # Write message to output without bit errors
                self.__print_bytes(text_message)
            else:
                self.logger.error('Something went wrong, the checksum is not correct')

    def __print_bytes(self, message):
        """
        Write a generated message to to the correct output
        :param message: message to send
        :type message: bytes
        """
        self.logger.log(15, message)
        if self.config.get_bit_error_rate() > 0.0 and self.config.get_bit_error_checksum() is True:
            message = text.bit_error(message, self.config.get_bit_error_rate(), self.bit_error_random)
        if self.output.available():
            self.output.write(message)
        else:
            self.logger.error('Could not write message to output, it is not available')

    def stop(self):
        """
        Stop the emulator. Please note that it may take some time to stop the emulator. When the emulator is stopped, get_status() will return 'stopped'
        """
        self.stopped = True
        self.status = 'stopping'

    def pause(self):
        """
        Pause the emulator. Please note that it may take some time to pause the emulator. When the emulator is paused, get_status() will return 'paused'
        """
        self.paused = True
        self.status = 'pausing'

    def resume(self):
        """
        When the emulator is paused, resume it
        """
        if self.status == 'pausing' or self.status == 'paused':
            self.paused = False
            self.status = 'resuming'

    def get_status(self):
        """
        Current status of the emulator
        :return: current status, can be one of [running, stopping, stopped, pausing, paused, resuming, initialized]
        """
        return self.status

    def __done(self):
        """
        Check if the emulator is done and should stop looping
        :return: true if it is done, false otherwise
        :rtype: bool
        """
        def __scenarios_done(scenarios):
            """
            Check if all scenarios in a list are done
            :param scenarios: list of scenarios
            :type scenarios: list
            :return: true if all scenarios are complete, false otherwise
            :rtype: bool
            """
            return all([len(s) == 0 or isinstance(s[0], ArithmeticScenario) for s in scenarios])

        def __text_done():
            """
            Check if all text scenarios are done
            :return: true if all scenarios are complete, false otherwise
            :rtype: bool
            """
            return __scenarios_done(list(self.text_scenarios.values()) + list(self.overwritten_text_scenarios.values()))

        def __hex_done():
            """
            Check if all hex scenarios are done
            :return: true if all scenarios are complete, false otherwise
            :rtype: bool
            """
            return __scenarios_done(list(self.hex_scenarios.values()) + list(self.overwritten_hex_scenarios.values()))

        if self.stop_condition == 'text':
            return self.stopped or __text_done()
        elif self.stop_condition == 'hex':
            return self.stopped or __hex_done()
        elif self.stop_condition == 'text-hex':
            return self.stopped or __text_done() and __hex_done()
        elif self.stop_condition == 'none':
            return self.stopped

    def run(self):
        """
        Start the emulation process
        """
        # Set listener for sending async hex messages on field change
        self.field_values.observable.on('put_hex_field_value', self.__send_async_hex_change)
        if self.timed:
            self.event_queue.start()
        while not self.__done():
            while self.paused:
                # Wait until unpaused
                self.status = 'paused'
                time.sleep(0.1)

            self.status = 'running'
            # Generate hex messages
            if self.config.get_protocol() != 'text':
                self.__read_incoming_hex_messages()
                self.__generate_async_hex_messages()
            # Generate text messages
            self.__generate_text_messages()

            # Wait a certain delay before sending the next message
            if self.config.get_delay() > 0:
                time.sleep(self.config.get_delay())
                self.run_time += self.config.get_delay()
            else:
                # Still increase the passed time for async hex messages
                self.run_time += 1

        self.status = 'stopped'

    def __generate_next(self, protocol, field_key):
        """
        Generate the next value of a field using the specified generator list
        :param protocol: either 'text' or 'hex'
        :type protocol: str
        :param field_key: field to get the value of
        :type field_key: str or int
        :return: pair of string or int value of the field and the field itself if available, (None, None) otherwise
        :rtype: (str, dict) or (int, dict) or (None, None)
        """

        def __clean_scenarios(scenarios):
            if field_key not in scenarios:
                return

            while len(scenarios[field_key]) > 0 and scenarios[field_key][0].is_complete():
                # If the current generator is done we can remove it
                scenarios[field_key].pop(0)

            # if len(generators[field_key]) == 0:
            #     # If there are no more generators for this field we can remove the field
            #     generators.pop(field_key)

        def __generate_next(scenarios):
            __clean_scenarios(scenarios)

            if field_key not in scenarios or len(scenarios[field_key]) == 0:
                # There is no generator available for this field
                return None, None

            next_value = scenarios[field_key][0].generate_next(self.field_values), scenarios[field_key][0]

            __clean_scenarios(scenarios)

            return next_value

        (value, field) = __generate_next(
            self.overwritten_hex_scenarios if protocol == 'hex' else self.overwritten_text_scenarios)
        if value is None:
            return __generate_next(self.hex_scenarios if protocol == 'hex' else self.text_scenarios)
        else:
            return value, field

    def __read_incoming_hex_messages(self):
        """
        Check if any hex messages have been received, and if so, process and respond to them
        """
        # Handle any incoming messages on input
        if self.input is not None:
            self.logger.debug('Checking for new input')

            # Check if there is anything to be read at the input
            while self.input.has_data() != 0:
                message = self.input.readline()
                message = message.replace(b'\x00', b'')

                if len(message) > 0:
                    self.logger.debug('New input received')

                    self.logger.debug(message)
                    if message[0] == ord(':'):
                        # Hex message
                        self.__process_hex_message(message)

    def __generate_async_hex_messages(self):
        """
        Generate asynchronous hex messages on interval where necessary
        """
        # Send async hex messages
        for field_key in self.__list_union_unique(self.hex_scenarios, self.overwritten_hex_scenarios):
            field = self.overwritten_hex_scenarios[field_key] if field_key in self.overwritten_hex_scenarios else \
                self.hex_scenarios[field_key]
            if len(field) > 0:
                scenario = field[0]
                # TODO make sure that the 'async_interval' functionality works well.
                #   Currently, self.run_time MUST be a multiple of 'async_interval'!
                #   This requirement is not really desirable, and can easily be violated
                #   and is quite obscure when it comes to explaining the issue to the user
                #   who wrote the configuration.
                if scenario.async_interval is not None and self.run_time % scenario.async_interval == 0:
                    # Send async message with value of field
                    if self.timed:
                        hex_value = self.field_values.get_hex_field_value(field_key)
                    else:
                        self.__generate_next('hex', field_key)
                        hex_value = self.field_values.get_hex_field_value(field_key)
                    if hex_value is not None:
                        hex_key = hex.int_to_hex_string(field_key, 2)
                        self.__print_bytes(
                            hex.create_message('A', hex_key + '00' + hex_value))

    def __generate_text_messages(self):
        """
        Generate one or more text messages based on all the fields in the scenarios list
        """
        # Generate text messages
        arithmetic_only = True
        for field in list(self.text_scenarios.values()) + list(self.overwritten_text_scenarios.values()):
            for value in field:
                if not isinstance(value, ArithmeticScenario):
                    arithmetic_only = False
                    break
            if not arithmetic_only:
                break
        if arithmetic_only:
            # If we only have arithmetic fields left there is no need to continue the emulation
            # since the arithmetic fields depend on other fields
            return

        # Generate values for each field
        if not self.timed:
            for field_key in self.__list_union_unique(self.text_scenarios, self.overwritten_text_scenarios):
                (value, _) = self.__generate_next('text', field_key)
                if value is not None:
                    self.logger.debug(f'New emulation for {field_key}: {value}')

        # Add values to the message
        message = {}  # Message to be sent
        for field_key in self.keys:
            field_value = self.field_values.get_field_value(field_key)
            if field_value is not None:
                message[str(field_key)] = str(field_value)

        # Generate a checksum and send the message
        self.__send_message(message)

    def __send_async_hex_change(self, key, value, old_value):
        """
        Sends an asynchronous hex message for a changed hex field
        :param key: field key
        :type key: int
        :param value: current hex value
        :type value: str
        :param old_value: old hex value
        :type old_value: str
        """
        if value != old_value:
            field = self.overwritten_hex_scenarios[
                key] if key in self.overwritten_hex_scenarios else self.hex_scenarios.get(key, None)
            if field is not None and field.async_change:
                hex_key = hex.int_to_hex_string(key, 2)
                self.__print_bytes(hex.create_message('A', hex_key + '00' + value))

    def __process_hex_message(self, message):
        """
        Process an incoming hex message and respond back with the correct response message
        :param message: incoming hex message
        :type message: bytes
        """
        # Filter out all non-hex characters
        message = ''.join([c for c in message[1:].decode('ascii', 'ignore').strip().upper() if c in '0123456789ABCDEF'])

        self.logger.debug(f'New hex message received: {message}')

        # Check checksum
        checksum_valid = hex.check_checksum(message)
        if not checksum_valid:
            self.__print_bytes(hex.create_message(4, 'AAAA'))
            return

        # Check command
        command = message[0:1]
        if command == '0':
            # Enter boot
            self.__print_bytes(hex.create_message(4, '0000'))  # Not supported in emulator

        elif command == '1':
            # Ping
            version = hex.int_to_hex_string(self.config.get_firmware_version(), 2)
            self.__print_bytes(hex.create_message(5, version))

        elif command == '3':
            # App version
            version = hex.int_to_hex_string(self.config.get_firmware_version(), 2)
            self.__print_bytes(hex.create_message(1, version))

        elif command == '4':
            # Product Id
            id = hex.int_to_hex_string(self.config.get_product_id(), 2)
            self.__print_bytes(hex.create_message(1, id))

        elif command == '6':
            # Restart
            pass  # The device restarts without a response

        elif command == '7':
            # Get
            id = message[3:5] + message[1:3]  # The id a uint16 saved in little endian format so switch around the bytes
            hex_id = int(id, 16)
            if self.timed:
                (value, field) = (self.field_values[hex_id], self.get_field_scenarios(hex_id)[0])
            else:
                (value, field) = self.__generate_next('hex', hex_id)

            if value is not None:
                self.__print_bytes(
                    hex.create_message(7, message[1:5] + '00' + self.field_values.get_hex_field_value(hex_id)))
            else:
                # Send a flag that indicates that the field is not valid
                self.__print_bytes(hex.create_message(7, message[1:5] + '01'))

        elif command == '8':
            # Set
            id = message[3:5] + message[1:3]  # The id is saved in little endian format so switch around the bytes
            hex_id = int(id, 16)

            if hex_id in self.hex_scenarios or hex_id in self.overwritten_hex_scenarios:
                field = self.overwritten_hex_scenarios[hex_id][0] if hex_id in self.overwritten_hex_scenarios else \
                    self.hex_scenarios[hex_id][0]
                id_writable = field.writable
                if id_writable is True:
                    value = message[7:-2]
                    bits_size = field.bits
                    if bits_size is not None:
                        # Check if the new value is not longer than the field size
                        value_valid = bits_size >= len(value) * 4  # 4 bits per hex character
                    else:
                        value_valid = True
                    if value_valid:
                        # Send the new value
                        self.__print_bytes(hex.create_message(8, message[1:5] + '00' + value))
                    else:
                        # Send a flag that indicates that the field value is not valid
                        if not self.timed:
                            self.__generate_next('hex', hex_id)
                        hex_value = self.field_values.get_hex_field_value(hex_id)
                        self.__print_bytes(hex.create_message(8, message[1:5] + '04' + hex_value))

                else:
                    # Send a flag that indicates that the field is not writable
                    if not self.timed:
                        self.__generate_next('hex', hex_id)
                    hex_value = self.field_values.get_hex_field_value(hex_id)
                    self.__print_bytes(hex.create_message(8, message[1:5] + '02' + hex_value))
            else:
                # Send a flag that indicates that the field is not valid
                self.__print_bytes(hex.create_message(8, message[1:5] + '01'))

        elif command == 'A':
            # Async
            pass  # The device does not seem to respond with an error when sending this command to a device, so we just ignore it here too
        else:
            # Unknown command
            self.__print_bytes(hex.create_message(3, f'0{command}00'))

    def overwrite_text_scenarios(self, field, scenarios):
        """
        Overwrite a scenario for a specific field
        :param field: field key of the field to overwrite
        :type field: str
        :param scenarios: scenario or list of scenarios
        :type scenarios: list
        """
        if not isinstance(scenarios, list):
            scenarios = list(scenarios)

        if field in self.text_scenarios and len(self.text_scenarios[field]) > 0:
            for scenario in scenarios:
                scenario.set_field_props(self.text_scenarios[field][0].get_field_props())
        self.overwritten_text_scenarios[field] = scenarios
        self.observable.trigger('overwrite_generators', field)

    def overwrite_hex_scenarios(self, field, scenarios):
        """
        Overwrite a scenario for a specific hex field
        :param field: field key of the field to overwrite
        :type field: int
        :param scenarios: scenario or list of scenarios
        :type scenarios: list
        """
        if not isinstance(scenarios, list):
            scenarios = list(scenarios)

        if field in self.hex_scenarios and len(self.hex_scenarios[field]) > 0:
            for scenario in scenarios:
                scenario.set_field_props(self.hex_scenarios[field][0].get_field_props())
        self.overwritten_hex_scenarios[field] = scenarios
        self.observable.trigger('overwrite_hex_scenarios', field)

    def __list_union_unique(self, *lists):
        """
        Combine multiple lists and remove duplicates while keeping list item order
        :param lists: lists to combine
        :return: combined list
        :rtype: list
        """
        result = []
        for list in lists:
            for elem in list:
                if elem not in result:
                    result.append(elem)

        return result

    def get_field_scenarios(self, key):
        """
        Get the list of scenarios for value generation of a specific field
        :param key: field key
        :type key: str or int
        :return: list of scenarios
        :rtype: list
        """
        if key in self.overwritten_text_scenarios:
            return self.overwritten_text_scenarios[key]
        elif key in self.overwritten_hex_scenarios:
            return self.overwritten_hex_scenarios[key]
        elif key in self.text_scenarios:
            return self.text_scenarios[key]
        elif key in self.hex_scenarios:
            return self.hex_scenarios[key]
        return None

    def get_scenario_keys(self):
        """
        Get all the keys that exist in scenarios
        :return: a list of keys
        :rtype: list
        """
        return self.__list_union_unique(self.text_scenarios, self.hex_scenarios,
                                        self.overwritten_text_scenarios, self.overwritten_hex_scenarios)
