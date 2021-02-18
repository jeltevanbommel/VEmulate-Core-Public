from .scenario import Scenario
from ..util.parse_allowed_chars import parse_allowed_chars


class StringRandomScenario(Scenario):
    """
    Scenario that generates a random string based on a minimum and maximum string length and a list of characters

    - type: StringRandom
      min_length: 10
      max_length: 30
      length: 30 # Only use while not using min_length and max_length
      allowed_chars: ['abc', ['1', '9']] # Default is a-zA-Z0-9; see scenarios.stringboundary.parse_allowed_chars() for list format
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.min_length = props.get('min_length', props.get('length', 0))
        self.max_length = props.get('max_length', props.get('length', 10))
        self.allowed_chars = parse_allowed_chars(props.get('allowed_chars', [['A', 'Z'], ['a', 'z'], ['0', '9']]))

    def _generate(self, field_values):
        length = self.rand.randint(self.min_length, self.max_length)
        value = ""
        for i in range(length):
            value += self.rand.choice(self.allowed_chars)
        self.value = value
