from .parentscenario import ParentScenario


class SelectRandomParentScenario(ParentScenario):
    """
    Scenario that selects a child value at random and generates a value for this scenario

    Example:
    - type: SelectRandom
      loop: true # Keep generating values indefinitely; resets the child scenario when it has generated all its values
      values:
        - type: StringFixed
          value: '---'
        - type: IntRange
          min: 0
          max: 10
    """
    last_generator = None

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.props = props
        self.loop = props.get('loop', False)

    def _generate(self, field_values):
        generator = self.rand.choice(self.children)
        result = generator.generate_next(field_values)
        if generator.is_complete() and self.loop:
            generator.reset()
        elif generator.is_complete():
            self.children.pop(self.children.index(generator))
        self.last_generator = generator
        self.value = result

    def is_complete(self):
        return super().is_complete() or len(self.children) == 0

    def _fuzz(self, field_values):
        return self.last_generator._fuzz(field_values)

