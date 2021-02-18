from .fixed import FixedScenario


class StringFixedScenario(FixedScenario):
    """
    Scenario that returns a fixed string value

    Example:
    - type: StringFixed
      value: Hello world
    """
    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props, default_value='')
