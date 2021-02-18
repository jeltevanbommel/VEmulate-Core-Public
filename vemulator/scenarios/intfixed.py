from .fixed import FixedScenario


class IntFixedScenario(FixedScenario):
    """
    Scenario that returns a fixed integer value

    Example:
    - type: IntFixed
      value: 5
    """
    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props, default_value=0)
