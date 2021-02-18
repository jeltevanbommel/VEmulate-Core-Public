from .scenario import Scenario
from ..util.regex import RegexToString


class RegexScenario(Scenario):
    """
    Scenario that generates values based on a (basic) regular expression

    Example:
    - type: Regex
      value: '^[0-9]{4}[a-zA-Z]{2}$'
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.regex = RegexToString(props.get('value', ""), self.seed)
        self.fuzzing_counter = -1

    def _generate(self, field_values):
        self.value = self.regex.create_valid_string()

    def _fuzz(self, field_values):
        # First one string of maximum possible length, then one with minimum possible length
        # To proceed with randomly generated ones
        self.fuzzing_counter += 1
        if self.fuzzing_counter == 0:
            self.value = self.regex.create_min_invalid_string()
        elif self.fuzzing_counter == 1:
            self.value = self.regex.create_max_invalid_string()
        else:
            self.value = self.regex.create_invalid_string()

    def reset(self):
        super().reset()
        self.fuzzing_counter = -1
