from .parentscenario import ParentScenario


class LoopParentScenario(ParentScenario):
    """
    Scenario for looping through a list of other scenarios multiple times

    Example:
    - type: Loop
      amount: 10
      values:
        - type: IntFixed
          value: 1
        - type: IntFixed
          value: 2
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.current_idx = 0
        self.loop_amount = self.initial_amount

    def _generate(self, field_values):
        if self.is_complete():
            self.value = None
            return

        result = self.children[self.current_idx].generate_next(field_values)
        if self.children[self.current_idx].is_complete():
            self.children[self.current_idx].reset()
            self.current_idx += 1

        if self.current_idx == len(self.children):
            if self.loop_amount is not None:
                self.loop_amount -=1
            self.current_idx = 0

        self.value = result

    def is_complete(self):
        return self.loop_amount is not None and self.loop_amount <= 0

    def reset(self):
        super().reset()
        self.loop_amount = self.initial_amount
        self.current_idx = 0


