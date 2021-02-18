import math

from vemulator.scenarios.scenario import Scenario


class BoundaryScenario(Scenario):
    """
    Base class for IntBoundary and StringBoundary scenarios

    Example:
    - type: {Scenario name}
      strict: false # True by default, indicates if values can be below min or above max when fuzzing
      {See Scenario for other properties}
    """
    _x = 0

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.min = props.get('min', 0)
        self.max = props.get('max', 1)
        self.strict = props.get('strict', True)
        self.range = self._range()

    def _range(self):
        """
        Generate a list from which values will be picked during generation.
        :return: the union between two ranges of values. These two ranges are values within a radius of
        math.sqrt(self.max - self.min) around either self.min or self.max.
        :rtype: list
        """
        # take a radius
        radius = int(math.sqrt((self.max - self.min)) / 2)
        if self.strict:
            # union of [self.min, self.min + radius] and [self.max - radius, self.max]
            return list(set([n for n in range(self.min, self.min + radius + 1)] +
                            [n for n in range(self.max - radius, self.max + 1)]))
        else:
            # union of [self.min - radius, self.min + radius] and [self.max - radius, self.max + radius]
            return list(set([n for n in range(self.min - radius, self.min + radius + 1)] +
                            [n for n in range(self.max - radius, self.max + radius + 1)]))

    def _generate(self, field_values):
        self._x += 1
        self.value = self.rand.choice(self.range)

    def _fuzz(self, field_values):
        if (self._x - 1) >= len(self.range):
            self.value = self.rand.choice(self.range)
        else:
            self.value = self.range[self._x - 1]
