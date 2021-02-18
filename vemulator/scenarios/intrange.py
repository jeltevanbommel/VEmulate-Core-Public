from .intboundary import IntBoundaryScenario
from .intrandom import IntRandomScenario
from .scenario import Scenario


class IntRangeScenario(Scenario):
    """
    Generalization of the IntRandom and IntBoundary scenarios

    Example:
    - type: IntRange
      min: 0
      max: 10
      generation: fuzzing # 'random' for IntRandom (default) and 'fuzzing' for IntBoundary
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.intrandom = IntRandomScenario(props, field_props)
        self.boundaryint = IntBoundaryScenario(props, field_props)

    def _generate(self, field_values):
        self.value = self.intrandom.generate_next(field_values)

    def _fuzz(self, field_values):
        self.value = self.boundaryint.generate_next(field_values)

    def is_complete(self):
        if self.fuzzing:
            return self.boundaryint.is_complete()
        return self.intrandom.is_complete()

    def reset(self):
        if self.fuzzing:
            return self.boundaryint.reset()
        return self.intrandom.reset()
