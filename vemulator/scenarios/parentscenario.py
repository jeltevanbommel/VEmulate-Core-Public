from .scenario import Scenario


class ParentScenario(Scenario):
    """
    Base class for a test scenario that has child scenarios

    Example:
    - type: {Scenario name}
      values:
        - {List of other scenarios}
      {See Scenario for other properties}
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.children = props.get('values', [])
        self.initial_children = self.children.copy()

    def reset(self):
        super().reset()
        for scenario in self.initial_children:
            scenario.reset()
        self.children = self.initial_children.copy()
        
    def _fuzz(self, field_values):
        pass  # No need for fuzzing since the child scenarios already employ fuzzing.
