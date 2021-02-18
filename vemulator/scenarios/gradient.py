from .scenario import Scenario

predefined_gradients = {
    'linear': 'x',
    'square': 'x ** 2',
    'cube': 'x ** 3',
    # you can define more functions here, but keep in mind that the only
    #  defined variable in these functions is currently "x".
    #  This means that parametric functions are not an option, currently.
}
predefined_gradient_types = predefined_gradients.keys()


class GradientScenario(Scenario):
    """
    Scenario that generates values based on a mathematical function of time

    Example:
    - type: Gradient
      gradient_type: 'x**2 + 5' # Can be a mathematical expression as a function of x or one of the predefined types 'linear', 'square', 'cube', 'parabolic'
      step_size: 2 # 1 by default; defines how much x should be incremented with each value generation
    """

    _x = 0

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.min = props.get('min', 0)  # must be an int
        self.max = props.get('max', 1)  # must be an int
        self.step_size = props.get('step_size', 1)  # must be an int
        self.gradient_type = props.get('gradient_type', 'linear')
        global predefined_gradient_types
        if self.gradient_type in predefined_gradient_types:
            self.gradient_type = predefined_gradients[self.gradient_type]

        if self.amount is None:
            self.amount = int((self.max - self.min) / self.step_size)

    def _generate(self, field_values):
        self._x += self.step_size
        self.value = eval(self.gradient_type, {'x': self._x - self.step_size})

    def reset(self):
        super().reset()
        self._x = 0
