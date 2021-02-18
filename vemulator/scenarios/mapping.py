from .scenario import Scenario


class MappingScenario(Scenario):
    """
    Scenario similar to the choice scenarios, in that a list of values can be provided
    from which values will be chosen at random. However, the mapping scenario uses a dictionary
    to map a describing name to a value, such that values can be displayed more descriptively in the GUI

    Example:
    - type: Mapping
      dict: {'Option one': 1, 'Option two': 2}
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.dict = list(props.get('dict', {}).values())
        if self.fuzzing:
            self.rand.shuffle(self.dict)
        self.fuzzing_index = -1

    def _generate(self, field_values):
        self.value = self.rand.choice(self.dict)

    def _fuzz(self, field_values):
        self.fuzzing_index += 1
        if self.fuzzing_index < len(self.dict):
            self.value = self.dict[self.fuzzing_index]
        else:
            self.value = self.rand.choice(self.dict)

    def reset(self):
        super().reset()
        self.fuzzing_index = -1
