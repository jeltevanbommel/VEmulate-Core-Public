import os
from os.path import dirname, abspath
from random import Random

from ..util import hex
from ..util import log
from ..util.config_checker import check_config_dict
from ..util.deserialize_scenario import deserialize_scenario, scenario_has_children
from ..util.yamlparser import load_yaml_with_lines, load_yaml


class InvalidPresetException(Exception):
    """
    This exception is thrown when a preset is invalid
    """
    pass


class EmulatorConfig:
    def __init__(self):
        """
        Instantiate a new config
        """
        self.logger = log.init_logger(__name__)
        self.text_scenarios = dict()
        self.hex_scenarios = dict()
        self.configuration = dict()
        self.input = None
        self.output = None
        self.delay = 1
        self.bit_error_rate = 0.0
        self.bit_error_checksum = False
        self.default_seed = 0
        self.timed = False
        self.stop_condition = 'text'

    ################
    # Initializers #
    ################
    def set_config_file(self, path):
        """
        Set a config file
        :param path: path to the yaml config file to parse
        :type path: str
        :return: true on success, false on failure
        :rtype: bool
        """
        with open(path, 'r') as stream:
            return self.set_config(stream)

    def set_config(self, config):
        """
        Set a config
        :param config: yaml string or text stream
        :type config: TextIO or str
        :return: true on success, false on failure
        :rtype: bool
        """
        config_dict = load_yaml_with_lines(config)
        if config_dict is not None:
            self.set_config_dict(config_dict)
        else:
            self.logger.error('An error occurred while loading the configuration file')
            return False

    def set_config_dict(self, config):
        """
        Set a config dict
        :param config: deserialized yaml config
        :type config: dict
        """
        check_config_dict(config)

        config = self.__remove_line_numbers(config)

        self.configuration = config

    def __remove_line_numbers(self, config):
        """
        Remove line number properties from the config dictionary
        :param config: config dictionary or part of the config
        :type config: list or dict or object
        :return: new config dict without line numbers
        :rtype: same as config parameter
        """
        if isinstance(config, list):
            return [self.__remove_line_numbers(item) for item in config]
        if isinstance(config, dict):
            return {key: self.__remove_line_numbers(value) for (key, value) in config.items() if key != '__line__'}
        else:
            return config

    def set_input(self, input):
        """
        Set the input to be used for receiving hex messages in the emulator
        :param input: input to be used
        :type input: input.inputinterface.InputInterface
        """
        self.input = input

    def set_output(self, output):
        """
        Set the output to send messages to during emulation
        :param output: output to be used
        :type output: output.outputinterface.OutputInterface
        """
        self.output = output

    def set_delay(self, delay=1):
        """
        Set the delay between two text messages
        :param delay: delay in seconds; 1 by default, set to 0 to emulate messages as fast as possible
        :type delay: int
        """
        self.delay = delay

    def set_bit_error_rate(self, bit_error_rate=0.0):
        """
        Set the bit error rate for a message.
        :param bit_error_rate: bit_error_rate is 0.0 by default, maximum value is 1.0. Example: Value of 0.6 indicates every
        .6 bits per bit are to be flipped.
        :type bit_error_rate: float
        """
        self.bit_error_rate = bit_error_rate

    def set_bit_error_checksum(self, bit_error_checksum=False):
        """
        Sets whether the checksum of the message may also be corrupted by a bit error, when a bit_error_rate is used.
        :param bit_error_checksum: bit_error_checksum is False by default. False indicates that the checksum will not be
        corrupted and that the checksum is still correct despite bit errors in other parts of the message,
        whereas True indicates that bit errors may occur in the checksum and the checksum is not necessarily correct.
        :type bit_error_checksum: bool
        """
        self.bit_error_checksum = bit_error_checksum

    def set_default_seed(self, default_seed=0):
        """
        Sets the default seed to be used for RNG when a field does not have a seed value
        NOTE: This should be set before calling `create_scenarios()`
        :param default_seed: the default seed to be used; 0 by default
        :type default_seed: int
        """
        self.default_seed = default_seed

    def set_timed(self, timed=False):
        """
        Set the timed flag for the generation of field values.
        :param timed: timed is False by default. False indicates that the emulator will generate new field_values every
        time a text message is sent, whereas True indicates that field values are generated asynchronously at certain
        intervals.
        :type timed: bool
        """
        self.timed = timed

    def set_stop_condition(self, stop_condition='text'):
        """
        Set the condition under which the emulator is supposed to terminate.
        :param stop_condition: must be one of 'text', 'hex', 'text-hex', or 'none'.
        :type stop_condition: str
        """
        self.stop_condition = stop_condition

    def create_scenarios(self):
        """
        Create scenarios for all the fields
        """
        # Create a RNG for the generation of seeds for fields, such that similar fields
        # do not always generate the same values
        seed_generator = Random(self.get_default_seed())

        if self.get_preset():
            # The config has presets, so load them first
            for emulated_parameter in self.get_preset_fields():  # for every preset text field in the configuration
                # If there are protocol fields, we create scenarios based on the presets for that protocol.
                try:
                    self.__create_field_scenarios(self.__load_from_preset(emulated_parameter), self.text_scenarios, 'text', seed_generator)
                except InvalidPresetException:
                    self.logger.warning(f'Not creating scenarios for field {emulated_parameter} due to an invalid preset.')
                    continue

            for emulated_parameter in self.get_preset_hex_fields():  # for every preset hex field in the configuration
                # If there are protocol fields, we create generators based on the presets for that protocol.
                try:
                    self.__create_field_scenarios(self.__load_from_preset(emulated_parameter), self.hex_scenarios, 'hex', seed_generator)
                except InvalidPresetException:
                    self.logger.warning(f'Not creating generator for field {emulated_parameter} due to an invalid preset.')
                    continue

        for emulated_parameter in self.get_fields():  # for every item in the configuration
            self.__create_field_scenarios(emulated_parameter, self.text_scenarios, 'text', seed_generator)

        for emulated_parameter in self.get_hex_fields():  # for every item in the configuration
            self.__create_field_scenarios(emulated_parameter, self.hex_scenarios, 'hex', seed_generator)

    def __load_from_preset(self, emulated_parameter):
        """
        Load a preset
        :param emulated_parameter: preset object
        :type emulated_parameter: dict
        :return: the preset field
        :rtype: dict
        """
        name = [key for key in emulated_parameter.keys() if key != 'override'][0]
        # Name contains the actual key of the field, which is also the filename(.yaml) stored in the preset directory
        file_location = os.path.join(dirname(abspath(__file__)), '..', '..', 'protocols', self.get_preset(), f'{name}.yaml')
        # The file location in which the preset for that key should be located
        if not os.path.exists(file_location):
            self.logger.warning(f'No preset was found in file_location {file_location}, the preset {name} is invalid.')
            raise InvalidPresetException()
        self.logger.debug(f'Loading preset from file_location {file_location}')
        # If the file location exists the YAML of the file is loaded into a dictionary
        with open(file_location, 'r') as stream:
            preset_config = load_yaml(stream)
            if preset_config is not None:
                # The values that are supplied in the configuration to override in the preset, are overridden
                if 'override' in emulated_parameter:
                    preset_config.update(emulated_parameter['override'])
                # There are three options for the generator of the preset
                if emulated_parameter[name] == 'default':
                    # First option is the default option, in which the scenario is simply a fixed value that is
                    # defined in the protocol to be default. This is a shorthand for a IntFixed or StringFixed scenario.
                    if 'default' not in preset_config:
                        self.logger.error(f'No default defined in preset configuration: {name}')
                        raise InvalidPresetException()
                    if isinstance(preset_config['default'], int):
                        preset_config.update({'values': [{'type': 'IntFixed', 'value':  preset_config['default']}]})
                        return preset_config
                    else:
                        preset_config.update({'values': [{'type': 'StringFixed', 'value':  preset_config['default']}]})
                        return preset_config
                elif emulated_parameter[name] == 'random' or emulated_parameter[name] == 'fuzzing':
                    # The second option is that the scenario will create random values, which are valid.
                    # The third option is that the scenario will create specific fuzzing values, which may be invalid data.
                    # This type is added to every single scenario in the preset as a 'generation' prop.
                    preset_config.update({'values': self.__apply_generation(preset_config['values'], emulated_parameter[name])})
                    return preset_config
                else:
                    self.logger.error(f'Unknown preset generation type: {emulated_parameter[name]}')
                    raise InvalidPresetException()
            else:
                self.logger.error(f'An error occurred while loading {name} preset')
                raise InvalidPresetException()
        return []

    def __apply_generation(self, scenarios, type):
        """
        Apply the generation type to this and all subsequent scenarios
        :param scenarios: list of scenarios
        :type scenarios: list
        :param type: one of 'random', 'fuzzing' or 'default'
        :type type: str
        :return: new scenarios with the type applied
        :rtype: list
        """
        for scenario in scenarios:
            if scenario_has_children(scenario['type']):
                scenario.update({'values': self.__apply_generation(scenario['values'], type)})
            if 'generation' not in scenario:
                scenario.update({'generation': type})
        return scenarios

    def on_create_field_scenarios(self, emulated_parameter, scenarios, protocol, seed_generator):
        """
        Custom override to hook into for the GUI.
        :param emulated_parameter: parameter or field to instantiate a scenario for
        :type emulated_parameter: dict
        :param scenarios: dict to save the scenario in
        :type scenarios: dict
        :param protocol: protocol for which the scenario is configured. Either 'hex' or 'text'
        :type protocol: str
        :param seed_generator: generator to generate the default seed from
        :type seed_generator: Random
        """
        pass

    def __create_field_scenarios(self, emulated_parameter, scenarios, protocol, seed_generator):
        """
        Create a scenario for a specified parameter
        :param emulated_parameter: parameter or field to instantiate a scenario for
        :type emulated_parameter: dict
        :param scenarios: dict to save the scenario in
        :type scenarios: dict
        :param protocol: protocol for which the scenario is configured. Either 'hex' or 'text'
        :type protocol: str
        :param seed_generator: generator to generate the default seed from
        :type seed_generator: Random
        """
        try:
            self.on_create_field_scenarios(emulated_parameter, scenarios, protocol, seed_generator)
            formatted_key = emulated_parameter['key'] if protocol == 'text' else '0x'+hex.int_to_hex_string(emulated_parameter['key'], 2, False, False)
            if 'values' in emulated_parameter:
                deserialized_scenario = deserialize_scenario(emulated_parameter['values'], {
                    'key': emulated_parameter['key'],
                    'protocol': protocol,
                    'interval': emulated_parameter.get('interval', 1),
                    'writable': emulated_parameter.get('writable', False),
                    'async_interval': emulated_parameter.get('async_interval', None),
                    'async_change': emulated_parameter.get('async_change', False),
                }, seed_generator)
                scenarios[emulated_parameter['key']] = deserialized_scenario
                self.logger.debug(f'Added scenario {formatted_key}')
            else:
                self.logger.warning(f'No values in parameter: {formatted_key}')
        except KeyError as e:
            self.logger.error(f'No key {e} exists')

    def is_initialized(self):
        """
        Check if all the required attributes are initialized. Any missing attributes will be logged as an error
        :return: true if all required attributes are initialized, false otherwise
        :rtype: bool
        """
        initialized = True
        if len(self.text_scenarios) == 0 and len(self.hex_scenarios) == 0:
            self.logger.error('No generators defined. Did you define fields in the config file and call `create_generators()`?')
            initialized = False
        if len(self.configuration) == 0:
            self.logger.error('No configuration file given. Did you call `set_config()`?')
            initialized = False
        if self.output is None:
            self.logger.error('No output given. Did you call `set_output()`?')
            initialized = False
        if self.input is None:
            # The emulator can run without an input, but we can still warn the user in case he forgot to set the input
            self.logger.warning('No input given. Did you call `set_input()`?')
        return initialized

    ###########
    # Getters #
    ###########

    def get_preset_fields(self):
        """
        Get the specific fields we want to select from the preset, and their specific override
        :return: list of string names of the preset fields, optionally can contain overrides for the preset
        :rtype: list
        """
        return self.configuration.get('preset_fields', [])

    def get_preset_hex_fields(self):
        """
        Get the specific fields we want to select from the preset, and their specific override
        :return: list of string names of the preset fields, optionally can contain overrides for the preset
        :rtype: list
        """
        return self.configuration.get('preset_hex_fields', [])

    def get_fields(self):
        """
        Get all the serialized text protocol fields in the config file
        :return: list of serialized fields
        :rtype: list
        """
        return self.configuration.get('fields', [])

    def get_hex_fields(self):
        """
        Get all the serialized hex protocol fields in the config file
        :return: list of serialized fields
        :rtype: list
        """
        return self.configuration.get('hex_fields', [])

    def get_device(self):
        """
        Get the name of the emulated device
        :return: name of the device
        :rtype: str
        """
        return self.configuration.get('device', '')

    def get_firmware_version(self):
        """
        Get the hex firmware version of the emulated device
        :return: firmware version
        :rtype: int
        """
        return self.configuration.get('version', 0)

    def get_product_id(self):
        """
        Get the hex product ID of the emulated device
        :return: product ID
        :rtype: int
        """
        return self.configuration.get('product_id', 0)

    def get_protocol(self):
        """
        Get the protocol to be used in the emulation
        :return: text, hex, text_hex
        :rtype: str
        """
        return self.configuration.get('protocol', 'text') if self.configuration.get('protocol', "") in ['text', 'hex', 'text_hex'] else 'text'

    def get_preset(self):
        """
        Get the preset (directory) name that can be used for generating selected fields in the emulation
        :return: preset name
        :rtype: str
        """
        return self.configuration.get('preset', "")

    def get_text_scenarios(self):
        """
        Get the dict containing all the text generators
        :return: dict of text generators
        :rtype: dict
        """
        return self.text_scenarios

    def get_hex_scenarios(self):
        """
        Get the dict containing all the hex generators
        :return: dict of hex generators
        :rtype: dict
        """
        return self.hex_scenarios

    def get_input(self):
        """
        Get the input for the emulator
        :return: input
        :rtype: input.inputinterface.InputInterface or None
        """
        return self.input

    def get_output(self):
        """
        Get the output for the emulator
        :return: output
        :rtype: output.outputinterface.OutputInterface
        """
        return self.output

    def get_delay(self):
        """
        Get the delay to be used between sending two text messages
        :return: delay in seconds; 1 by default, 0 if messages should be sent as fast as possible
        :rtype: int
        """
        return self.delay

    def get_bit_error_rate(self):
        """
        Get the bit error rate for a message.
        :return bit_error_rate is 0.0 by default, maximum value is 1.0. Example: Value of 0.6 indicates every
        .6 bits per bit are to be flipped.
        :rtype float
        """
        return self.bit_error_rate

    def get_bit_error_checksum(self):
        """
        Gets whether the checksum of the message may also be corrupted by a bit error, when a bit_error_rate is used.
        When using the hex protocol, this must be set to True in order to create bit errors in the hex messages.
        :return bit_error_checksum is False by default. False indicates that the checksum will not be
        corrupted, whereas True indicates that bit errors may occur in the checksum.
        :rtype bool
        """
        return self.bit_error_checksum

    def get_default_seed(self):
        """
        Gets the default seed to be used for RNG
        :return the default seed
        :rtype int
        """
        return self.default_seed

    def get_timed(self):
        """
        Get the timed flag for the generation of field values.
        :return: The timed flag is False by default. False indicates that the emulator will generate new field_values every
        time a text message is sent, whereas True indicates that field values are generated asynchronously
        at certain intervals.
        :rtype: bool
        """
        return self.timed

    def get_stop_condition(self):
        """
        Get the condition under which the emulator is supposed to terminate.
        :return: one of 'text', 'hex', 'text-hex', or 'none'
        :rtype: str
        """
        return self.stop_condition

    def get_name(self):
        """
        Get the name of the configuration yaml.
        :return then name as defined in the configuration file
        :rtype str
        """
        return self.configuration.get('name', 'unknown name')
