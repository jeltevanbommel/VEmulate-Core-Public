import sys

from .scenario import Scenario


class StringUnicodeScenario(Scenario):
    """
    Scenario that generates a random string based on a minimum and maximum string length
    using random (not necessarily ascii) characters in the unicode range

    - type: StringUnicode
      min_length: 10
      max_length: 30
      length: 30 # Only use while not using min_length and max_length
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.min_length = props.get('min_length', props.get('length', 0))
        self.max_length = props.get('max_length', props.get('length', 10))

    def _generate(self, field_values):
        length = self.rand.randint(self.min_length, self.max_length)
        value = ""
        for i in range(length):
            n = self.rand.randint(0, sys.maxunicode)
            value += chr(n)
        self.value = value

    def _fuzz(self, field_values):
        # Just use generated value
        pass