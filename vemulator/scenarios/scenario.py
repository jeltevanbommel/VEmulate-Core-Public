import math
import string
import sys
from random import Random

from ..util import hex, log


class Scenario:
    """
    Base class for a test scenario

    Example:
    - type: {Scenario name}
      amount: 10 # Number of values to generate
      bits: 8 # Number of bits to use for the field in the hex protocol. This has to be a multiple of 8 except when the field is inside a bitbuffer scenario
      signed: true # Default is false; applies to integer fields in the hex protocol, and indicates whether the number is signed
      generation: fuzzing # Default is random; determines whether the focus should be on fuzzing (trying weird values to try to break a system) or normal random value generation
      async_interval: 1 # Default is null; sends this field every n seconds as an async hex message
      async_change: true # Default is false; sends this field as an async hex message when its value changes
      writable: true # Default is false; indicates if the field can be written to using the hex protocol
      interval: 2 # Default is 1; indicates the interval in seconds between the generation of new values. This property is only used when the emulator is run in timed mode.
      seed: 1234 # Default is 0; defines the seed that will be used for this scenario.
    """

    def __init__(self, props={}, field_props={}):
        """
        Create a Scenario
        :param props: properties that are defined specifically for this Scenario
        :param field_props: properties that are defined more generally across the Field to which this Scenario belongs.
            These field properties also apply to all other Scenarios that belong to that Field. If field_props contains a key that's also present in props, then the value in props will be used.
        """
        self.initial_props = props.copy()
        self.set_field_props(field_props)

    def generate_next(self, field_values):
        """
        Generate the next value in a sequence defined by this Scenario.
        :param field_values: values of other fields
        :type: FieldValueList
        :return: the new value
        :rtype: str or int
        """
        old_value = self.value
        # do while self.value is not valid, try 3 times.
        do = 0
        while do == 0 or not self.__valid() and do < 3:

            if self.amount is not None:
                self.amount -= 1
            self._generate(field_values)
            if self.fuzzing:
                # depending on the type of Scenario, self._fuzz() should change/alter the value
                #   in such a way that the result is invalid, unexpected or random.

                self._fuzz(field_values)
            do += 1

        if not self.__valid():
            # if still invalid, simply assume the previous value.
            self.logger.warning(f'could not generate valid value. Invalid value: {self.value}')
            self.value = old_value
        if self.protocol == 'text':
            field_values.put_field_value(self.key, self.value)
        elif self.protocol == 'hex':
            key_string = hex.int_to_hex_string(self.key, 2, little_endian=False)
            field_values.put_field_value('H0x' + key_string, self.value)
            field_values.put_hex_field_value(self.key, self.get_hex_value())
        return self.get_value()

    def set_field_props(self, field_props):
        """
        Set the field props
        :param field_props: field props
        :rtype field_props: dict
        """
        self.field_props = field_props
        props = self.initial_props
        for (key, value) in field_props.items():
            # Only set default if no value is already set
            # Always override key and protocol since they are not allowed to be manually defined in the scenario
            if key not in props or key in ['key', 'protocol']:
                props[key] = value

        self.__set_props(props)

    def __valid(self):
        """
        Check if a generated value is valid
        :return: true if the value is valid, false otherwise
        :rtype: bool
        """
        return self.invalid is None or self.value not in self.invalid

    def __set_props(self, props):
        """
        Set props
        :param props: props
        :type props: dict
        """
        self.props = props
        self.key = props.get('key', None)
        self.amount = props.get('amount', None)
        self.seed = props.get('seed', 0)
        self.bits = props.get('bits', None)
        self.signed = props.get('signed', False)
        self.fuzzing = (props.get('generation', 'random') == 'fuzzing')
        self.interval = props.get('interval', 1)  # default interval for timed generation
        self.async_interval = props.get('async_interval', None)
        self.async_change = props.get('async_change', False)
        self.writable = props.get('writable', False)
        self.rand = Random(self.seed)
        self.initial_amount = self.amount
        self.protocol = props.get('protocol', 'text')
        self.invalid = props.get('invalid', None)
        self.logger = log.init_logger(__name__)
        self.value = None

    def get_field_props(self):
        """
        Get all field props
        :return: field props
        :rtype: dict
        """
        return self.field_props

    def get_value(self):
        """
        Get the value of the field
        :return: value
        :rtype: str or int
        """
        return self.value

    def get_hex_value(self):
        """
        Get the value of the field as a hex string
        :return: hex encoded value
        :rtype: str
        """
        if self.bits == None:
            self.logger.warning("Bits was not defined for scenario with key {}, defaulted to 32 bits to process HEX GET".format(self.key))
            self.bits = 32
        return hex.value_to_hex_string(self.value, math.ceil(self.bits / 8),
                                       self.signed) if self.value is not None else None

    def _generate(self, field_values):
        """
        Internal method which should be implemented by sub classes.
        :param field_values: field values
        :type field_values: dict
        """
        pass

    def is_complete(self):
        """
        Check if the scenario is complete
        :return: true if it is complete, false otherwise
        :rtype: bool
        """
        return self.amount is not None and self.amount <= 0

    def reset(self):
        """
        Reset all 'stateful' Scenario properties to their original values.
        """
        self.amount = self.initial_amount
        # self.rand = Random(self.seed)  # this is probably not desirable, but if necessary, this can be reset.
        self.value = None

    def _fuzz(self, field_values):
        """
        Replace the value of the Scenario with a fuzzed value. Fuzzing includes values that are either
        invalid, unexpected, or random. Concretely, this means that the value generated by Scenario._generate
        is discarded and a different value is put in place.
        Currently, fuzzed values can be generated to replace values of type str or int.
        If other functionality is desirable in specific Scenarios, this method can simply be overridden in a
        subclass.
        :param field_values: values of other fields
        :type: FieldValueList
        """
        if isinstance(self.value, int):
            self.value = self.rand.randint(-sys.maxsize - 1, sys.maxsize)
        if isinstance(self.value, str):
            length = len(self.value)
            new_value = ""
            for i in range(length):
                new_value += self.rand.choice(string.printable)
            self.value = new_value
