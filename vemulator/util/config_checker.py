import os
import re
from os.path import dirname, abspath, basename

from ..scenarios.gradient import predefined_gradient_types
from ..util.deserialize_scenario import scenarios, scenario_has_children
from ..util.yamlparser import load_yaml_with_lines


class ConfigException(Exception):
    def __init__(self, message):
        super().__init__(message)


def is_int(value):
    """
    Check if a value is an integer
    :param value: value to check
    :return: true if the value is an integer, false otherwise
    :rtype: bool
    """
    return isinstance(value, int)


def check_config_file(file):
    """
    Check a config file for syntax or value errors
    :param file: path to the file to check
    :type file: str
    :exception ConfigException if there is an error in the config file
    """
    with open(file, 'r') as config_yaml:
        config = load_yaml_with_lines(config_yaml)

        check_config_dict(config, file)

    return True


def check_config_dict(config, file=''):
    """
    Check a config dictionary for syntax or value errors
    :param config: config dictionary
    :type config: dict
    :param file: path of the file from which the config originates
    :type file: file name
    :exception ConfigException if there is an error in the config file
    """
    if 'device' not in config:
        raise ConfigException('Device not defined. Define a key `device` with the name of the emulated device.')

    if 'name' not in config:
        raise ConfigException('Test name not defined. Define a key `name` with the name of the test configuration.')

    if 'protocol' not in config:
        raise ConfigException('Protocol not defined. Define a key `protocol` with the name of the protocol.')
    elif config['protocol'] not in ['text', 'hex', 'text_hex']:
        raise ConfigException('Invalid protocol provided. Protocol should be one of `text`, `hex`, `text_hex`.')

    if 'preset' in config:
        if 'preset_fields' not in config and 'preset_hex_fields' not in config:
            raise ConfigException('No preset fields defined. Define a key `preset_fields` with a list of fields.')
        if not os.path.exists(os.path.join(dirname(abspath(__file__)), '..', '..', 'protocols', config['preset'])):
            raise ConfigException('No preset named ' + config['preset'] + ' exists.')

        if 'preset_fields' in config and not isinstance(config['preset_fields'], list):
            raise ConfigException(
                'Preset fields should be a list of dictionaries. Define a key `preset_fields` with a dictionary of fields.')

        if 'preset_hex_fields' in config and not isinstance(config['preset_hex_fields'], list):
            raise ConfigException(
                'Preset hex fields should be a list of dictionaries. Define a key `preset_hex_fields` with a dictionary of fields.')

        for field in config.get('preset_fields', []):
            check_preset_field(config['preset'], field)

        for field in config.get('preset_hex_fields', []):
            check_preset_hex_field(config['preset'], field)

    if config['protocol'] in ['hex', 'text_hex']:
        if 'version' not in config:
            raise ConfigException(
                'Version not provided while using hex protocol. Define a key `version` with the firmware version of the emulated device.')
        if not is_int(config['version']) or int(config['version']) < 0x0000 or int(config['version']) > 0xFFFF:
            raise ConfigException('Invalid version provided. The version should be between 0x0000 and 0xFFFF.')

        if 'product_id' not in config:
            raise ConfigException(
                'Product ID not provided while using hex protocol. Define a key `product_id` with the product ID of the emulated device.')
        if not is_int(config['product_id']) or int(config['product_id']) < 0x0000 or int(config['product_id']) > 0xFFFF:
            raise ConfigException('Invalid product ID provided. The product ID should be between 0x0000 and 0xFFFF.')

        if 'bootloader' in config and not is_int(config['bootloader']):
            raise ConfigException('Invalid bootloader payload defined. Payload should be provided as hex (0x...).')

        if config['protocol'] in ['text', 'text_hex']:
            if 'preset_fields' not in config and 'fields' not in config:
                raise ConfigException(
                    'Fields not provided while using text protocol. Define a key `fields` with a list of fields.')

            if 'fields' in config and not isinstance(config['fields'], list):
                raise ConfigException('Fields should be a list. Define a key `fields` with a list of fields.')

            for field in config.get('fields', []):
                check_config_text_field(basename(file), field)

        if config['protocol'] in ['hex', 'text_hex']:
            if 'preset_hex_fields' not in config and 'hex_fields' not in config:
                raise ConfigException(
                    'Hex fields not provided while using hex protocol. Define a key `hex_fields` with a list of fields.')

            if 'hex_fields' in config and not isinstance(config['hex_fields'], list):
                raise ConfigException('Hex fields should be a list. Define a key `hex_fields` with a list of fields.')

            for field in config.get('hex_fields', []):
                check_config_hex_field(basename(file), field)


def check_preset_field(preset, field):
    """
    Check preset field for errors
    :param preset: name of the preset
    :type preset: string
    :param field: preset field
    :type field: dict
    """
    key = [k for k in field.keys() if k[:2] != '__'][0]
    value = field[key]

    if value not in ['default', 'fuzzing', 'random']:
        raise ConfigException('Invalid preset type for preset field at #{}. Type should be one of `default`, `fuzzing` or `random`.'.format(field.get('__line__', 'NaN')))

    preset_path = os.path.join(dirname(abspath(__file__)), '..', '..', 'protocols', preset, f'{key}.yaml')
    if not os.path.exists(preset_path):
        raise ConfigException('No preset file found for preset {}'.format(key))

    with open(preset_path, 'r') as preset_yaml:
        preset = load_yaml_with_lines(preset_yaml)
        check_config_text_field(f'{key}.yaml', preset)


def check_preset_hex_field(preset, field):
    """
    Check preset hex field for errors
    :param preset: name of the preset
    :type preset: string
    :param field: preset field
    :type field: dict
    """
    key = [k for k in field.keys() if k[:2] != '__'][0]
    value = field[key]

    if value not in ['default', 'fuzzing', 'random']:
        raise ConfigException('Invalid preset type for preset field at #{}. Type should be one of `default`, `fuzzing` or `random`.'.format(field.get('__line__', 'NaN')))

    preset_path = os.path.join(dirname(abspath(__file__)), '..', '..', 'protocols', preset, f'{key}.yaml')
    if not os.path.exists(preset_path):
        raise ConfigException('No preset file found for preset {}'.format(key))

    with open(preset_path, 'r') as preset_yaml:
        preset = load_yaml_with_lines(preset_yaml)
        check_config_hex_field(f'{key}.yaml', preset)


def check_config_text_field(filename, field):
    """
    Check a config field for value errors
    :param filename: name of the yaml file
    :type filename: str
    :param field: field to check
    :exception ConfigException if there is an error in the field
    """
    if 'name' not in field and 'names' not in field:
        raise ConfigException('No name defined for field at #{} in file {}. Define a key `name` with the human readable name of the field.'.format(field.get('__line__', 'NaN'), filename))

    if 'key' not in field and 'keys' not in field:
        raise ConfigException('No key defined for field at #{}. Define a key `key` with the key of the field.'.format(field.get('__line__', 'NaN')))

    if 'values' not in field:
        raise ConfigException('No values defined for field at #{} in file {}. Define a key `values` with a list of possible values of the field.'.format(field.get('__line__', 'NaN'), filename))
    if not isinstance(field['values'], list):
        raise ConfigException('Values is not a list for field at #{} in file {}. Define a key `values` with a list of possible values of the field.'.format(field.get('__line__', 'NaN'), filename))

    for value in field['values']:
        check_config_text_value(filename, value)


def check_config_hex_field(filename, field):
    """
    Check a config hex field for value errors
    :param filename: name of the yaml file
    :type filename: str
    :param field: hex field to check
    :exception ConfigException if there is an error in the hex field
    """
    if 'name' not in field:
        raise ConfigException('No name defined for hex field at #{} in file {}. Define a key `name` with the human readable name of the field.'.format(field.get('__line__', 'NaN'), filename))

    if 'key' not in field:
        raise ConfigException('No key defined for hex field at #{} in file {}. Define a key `key` with the key of the field.'.format(field.get('__line__', 'NaN'), filename))
    if not is_int(field['key']) or int(field['key']) < 0x0000 or int(field['key']) > 0xFFFF:
        raise ConfigException('Invalid field key provided for hex field at #{} in file {}. The product ID should be between 0x0000 and 0xFFFF.'.format(field.get('__line__', 'NaN'), filename))

    if 'values' not in field:
        raise ConfigException('No values defined for hex field at #{} in file {}. Define a key `values` with a list of possible values of the field.'.format(field.get('__line__', 'NaN'), filename))
    if not isinstance(field['values'], list):
        raise ConfigException('Values is not a list for hex field at #{} in file {}. Define a key `values` with a list of possible values of the field.'.format(field.get('__line__', 'NaN'), filename))

    for value in field['values']:
        check_config_hex_value(filename, value)


def check_config_value(filename, value):
    """
    Check a config value for value errors
    :param filename: name of the yaml file
    :type filename: str
    :param value: value to check
    :exception ConfigException if there is an error in the value
    """
    if 'type' not in value:
        raise ConfigException('No type defined for value at #{} in file {}. Define a key `type` with the type of the field.'.format(value.get('__line__', 'NaN'), filename))
    if value['type'] not in scenarios.keys():
        raise ConfigException('Invalid type provided for value at #{} in file {}.'.format(value.get('__line__', 'NaN'), filename))

    if 'seed' in value and not is_int(value['seed']):
        raise ConfigException('Invalid seed provided for value at #{} in file {}. Seed should be an integer.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'Arithmetic':
        if 'value' not in value:
            raise ConfigException('No value defined for arithmetic value at #{} in file {}. Define a key `value` with the arithmetic expression of the value.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'BitBuffer':
        if 'values' not in value:
            raise ConfigException('No values defined for bitbuffer at #{} in file {}. Define a key `values` with a list of possible values.'.format(value.get('__line__', 'NaN'), filename))
        bit_size = 0
        for v in value['values']:
            if 'bits' not in v:
                raise ConfigException('No bit size defined for bitbuffer field at #{} in file {}. Define a key `bits` with the bit size of the field'.format(value.get('__line__', 'NaN'), filename))
            elif not isinstance(v['bits'], int) or v['bits'] <= 0:
                raise ConfigException('Invalid value as bit size for bitbuffer field at #{} in file {}. Bit size should be an integer > 0'.format(value.get('__line__', 'NaN'), filename))
            bit_size += v['bits']
        if bit_size % 8 != 0:
            raise ConfigException('Invalid total bit size of bitbuffer field at #{} in file {}. Total bit size should be a multiple of 8 but the actual bit size is {}.'.format(value.get('__line__', 'NaN'), filename, bit_size))

    if value['type'] == 'Gradient':
        if 'gradient_type' in value and value['gradient_type'] not in predefined_gradient_types:
            raise ConfigException('Invalid gradient type supplied for gradient at #{} in file {}. Gradient type must be one of `linear`, `sqare` or `cube`.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] in ['IntBoundary', 'IntRandom', 'IntRanged']:
        if 'min' in value and not is_int(value['min']):
            raise ConfigException('Invalid minimum provided for value at #{} in file {}. Minimum should be an integer.'.format(value.get('__line__', 'NaN'), filename))

        if 'max' in value and not is_int(value['max']):
            raise ConfigException('Invalid maximum provided for value at #{} in file {}. Maximum should be an integer.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] in ['IntRandom', 'StringRandom', 'StringUnicode']:
        if 'amount' in value and not is_int(value['amount']):
            raise ConfigException('Invalid amount provided for value at #{} in file {}. Amount should be an integer.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'IntFixed':
        if 'value' not in value:
            raise ConfigException('No value provided for int value at #{} in file {}. Define a key `value` with value of the integer.'.format(value.get('__line__', 'NaN'), filename))
        if not is_int(value['value']):
            raise ConfigException('Invalid value provided for int value at #{} in file {}. Value should be an integer.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'IntChoice':
        if 'choices' not in value:
            raise ConfigException('No choices provided for int choice value at #{} in file {}. Define a key `choices` with a list of possible integer values.'.format(value.get('__line__', 'NaN'), filename))
        choices_valid = isinstance(value['choices'], list)
        if choices_valid:
            for choice in value['choices']:
                choices_valid = choices_valid and is_int(choice)
                if not choices_valid:
                    break
        if not choices_valid:
            raise ConfigException('Invalid choices provided for int choice value at #{} in file {}. Choices should be a list of integers.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'Loop':
        if not is_int(value['amount']) or not (value['amount'] == -1 or value['amount'] > 0):
            raise ConfigException('Invalid amount provided for loop value at #{} in file {}. Amount should be -1 or greater than 0'.format(value.get('__line__', 'NaN'), filename))

        if 'values' not in value:
            raise ConfigException('No values defined for loop value at #{} in file {}. Define a key `values` with a list of possible values of the loop.'.format(value.get('__line__', 'NaN'), filename))
        if not isinstance(value['values'], list):
            raise ConfigException('Values is not a list for loop value at #{} in file {}. Define a key `values` with a list of possible values of the loop.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'Regex':
        try:
            re.compile(value['value'])
        except re.error:
            raise ConfigException('Value of regex value at #{} in file {} is not a valid regex.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'Mapping':
        if 'dict' not in value:
            raise ConfigException('No dictionary supplied for mapping at #{} in file {}. Define a key `dict` with a dictionary of possible values of the mapping.'.format(value.get('__line__', 'NaN'), filename))
        if not isinstance(value['dict'], dict):
            raise ConfigException('Invalid dictionary value supplied for mapping at #{} in file {}. The value should be a dictionary of possible values of the mapping.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'StringFixed':
        if 'value' not in value:
            raise ConfigException('No value provided for string value at #{} in file {}. Define a key `value` with value of the string.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] in ['StringBoundary', 'StringRandom', 'StringUnicode']:
        if 'min_length' in value and not is_int(value['min_length']):
            raise ConfigException('Invalid minimum length provided for string value at #{} in file {}. Minimum length should be an integer.'.format(value.get('__line__', 'NaN'), filename))

        if 'max_length' in value and not is_int(value['max_length']):
            raise ConfigException('Invalid maximum length provided for string value at #{} in file {}. Maximum length should be an integer.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] in ['StringBoundary', 'StringRandom']:
        if 'allowed_chars' in value:
            valid = isinstance(value['allowed_chars'], list)
            if valid:
                for chars in value['allowed_chars']:
                    if not isinstance(chars, list):
                        valid = len(chars) == 2
                    elif not isinstance(chars, str):
                        valid = False
                    if not valid:
                        break
            if not valid:
                raise ConfigException('Invalid allowed characters provided for value at #{} in file {}. Allowed characters should be a list with as items strings, or character ranges as a list with two strings.'.format(value.get('__line__', 'NaN'), filename))

    if value['type'] == 'StringChoice':
        if 'choices' not in value:
            raise ConfigException('No choices provided for string choice value at #{} in file {}. Define a key `choices` with a list of possible integer values.'.format(value.get('__line__', 'NaN'), filename))
        if not isinstance(value['choices'], list):
            raise ConfigException('Invalid choices provided for string choice value at #{} in file {}. Choices should be a list of strings.'.format(value.get('__line__', 'NaN'), filename))


def check_config_text_value(filename, value):
    """
    Check a config text value for value errors
    :param filename: name of the yaml file
    :type filename: str
    :param value: text value to check
    :exception ConfigException if there is an error in the hex value
    """
    check_config_value(filename, value)

    if scenario_has_children(value['type']):
        for value in value.get('values', []):
            check_config_text_value(filename, value)


def check_config_hex_value(filename, value):
    """
    Check a config hex value for value errors
    :param filename: name of the yaml file
    :type filename: str
    :param value: hex value to check
    :exception ConfigException if there is an error in the hex value
    """
    check_config_value(filename, value)

    if scenario_has_children(value['type']):
        for value in value.get('values', []):
            check_config_hex_value(filename, value)
