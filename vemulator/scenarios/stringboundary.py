from .boundary import BoundaryScenario
from ..util.parse_allowed_chars import parse_allowed_chars


class StringBoundaryScenario(BoundaryScenario):
    """
    Scenario that generates a random string based on a minimum and maximum string length and a list of characters
    It differs with StringRandom in that strings with lengths around the boundary will be generated when using fuzzing

    Example:
    - type: StringBoundary
      min_length: 10
      max_length: 30
      length: 30 # Only use while not using min_length and max_length
      strict: true # Default is true; if false, strings slightly longer than the max_length or slightly shorter than the min_length might be generated
      allowed_chars: ['abc', ['1', '9']] # Default is a-zA-Z0-9; see util.parse_allowed_chars.parse_allowed_chars() for list format
    """

    def __init__(self, props={}, field_props={}):
        self.min_length = props.get('min_length', props.get('length', 0))
        self.max_length = props.get('max_length', props.get('length', 10))
        props['min'] = self.min_length
        props['max'] = self.max_length
        super().__init__(props=props, field_props=field_props)
        self.allowed_chars = parse_allowed_chars(props.get('allowed_chars', [['A', 'Z'], ['a', 'z'], ['0', '9']]))

    def _generate(self, field_values):
        # note: length can be negative
        super()._generate(field_values)
        length = self.value  # int value generated by super class
        self.value = self.__generate_string(length)

    def _fuzz(self, field_values):
        super()._fuzz(field_values)
        length = self.value
        self.value = self.__generate_string(length)

    def __generate_string(self, length):
        """
        Generate a string with the specified length
        :param length: length of the string
        :type length: int
        :return: generated string
        :rtype: str
        """
        value = None
        if length is not None:
            value = ""
            for i in range(length):
                value += self.rand.choice(self.allowed_chars)
        return value
