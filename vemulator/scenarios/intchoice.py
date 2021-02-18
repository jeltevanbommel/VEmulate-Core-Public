from .scenario import Scenario


class IntChoiceScenario(Scenario):
    """
    Scenario that chooses values from a list of integers

    Example:
    - type: IntChoice
      choices: [0, 5, 10]
    """
    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.choices = props.get('choices', [0])

    def _generate(self, field_values):
        self.value = self.rand.choice(self.choices)

    def _fuzz(self, field_values):
        # Just pick a value from the choices using _generate
        pass