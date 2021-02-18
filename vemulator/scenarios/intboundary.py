from .boundary import BoundaryScenario


class IntBoundaryScenario(BoundaryScenario):
    """
    Scenario for generating numbers within a certain boundary
    It differs from IntRandom in that values around the boundary will be generated when using fuzzing

    Example:
    - type: IntBoundary
      min: 0
      max: 10
      strict: true # Default is true; if false, ints slightly larger than the max or slightly smaller than the min might be generated
    """
    # For now, this is no different from the default implementation of BoundaryScenario.
    pass
