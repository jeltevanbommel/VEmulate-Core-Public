from .scenario import Scenario


class ArithmeticScenario(Scenario):
    """
    Scenario for calculating a value based on other field values.
    The value is evaluated using eval() so any Python functions or operators can be used.

    Example:
    - type: Arithmetic
      value: V * A
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        # this dict access of 'value' will break if you don't supply a value key to props.
        # however, it should never break if the config checker has
        # been used to verify that the config conforms to the specification.
        self.arithmetic_value = props['value']

    def _generate(self, field_values):
        try:
            self.value = eval(self.arithmetic_value, field_values.get_field_values())
        except MemoryError as e:
            self.logger.error("Values calculated in eval too large for memory.")

    def is_complete(self):
        return False
