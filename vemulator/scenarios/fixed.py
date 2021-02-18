from vemulator.scenarios.scenario import Scenario


class FixedScenario(Scenario):
    """
    Base class for IntFixed and StringFixed scenarios

    Example:
    - type: {Scenario name}
      value: {Value} # Fixed value
      {See Scenario for other properties}
    """

    def __init__(self, props={}, field_props={}, default_value=None):
        super().__init__(props=props, field_props=field_props)
        self.fixed_value = props.get('value', default_value)
        self.fixed_value_fuzzed = None

    def _generate(self, field_values):
        self.value = self.fixed_value

    def _fuzz(self, field_values):
        # It does not make sense to generate a different value than the fixed
        # value when fuzzing here
        pass