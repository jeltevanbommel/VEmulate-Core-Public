import sys

from .scenario import Scenario


class IntRandomScenario(Scenario):
    """
    Scenario that returns a random integer, between certain values

    Example:
    - type: IntRandom
      min: 0
      max: 10
    """
    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.min = props.get('min', 0)
        self.max = props.get('max', 1)

    def _generate(self, field_values):
        self.value = self.rand.randint(self.min, self.max)

    def _fuzz(self, field_values):
        self.min = self.props.get('min', -sys.maxsize - 1)
        self.max = self.props.get('max', sys.maxsize)
        self.value = self.rand.randint(self.min, self.max)
