from .scenario import Scenario


class StringChoiceScenario(Scenario):
    """
    Scenario that gets a random value from a list of strings

    Example:
    - type: StringChoice
      choices: ['one', 'two', 'three']
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.choices = props.get('choices', [''])

    def _generate(self, field_values):
        self.value = self.rand.choice(self.choices)

    def _fuzz(self, field_values):
        # Just pick a value from the choices using _generate
        pass
