import inspect
import sys

from ..scenarios.arithmetic import ArithmeticScenario
from ..scenarios.bitbuffer import BitBufferParentScenario
from ..scenarios.gradient import GradientScenario
from ..scenarios.intboundary import IntBoundaryScenario
from ..scenarios.intchoice import IntChoiceScenario
from ..scenarios.intfixed import IntFixedScenario
from ..scenarios.intrandom import IntRandomScenario
from ..scenarios.intrange import IntRangeScenario
from ..scenarios.loop import LoopParentScenario
from ..scenarios.mapping import MappingScenario
from ..scenarios.parentscenario import ParentScenario
from ..scenarios.regex import RegexScenario
from ..scenarios.selectrandom import SelectRandomParentScenario
from ..scenarios.stringboundary import StringBoundaryScenario
from ..scenarios.stringchoice import StringChoiceScenario
from ..scenarios.stringfixed import StringFixedScenario
from ..scenarios.stringrandom import StringRandomScenario
from ..scenarios.stringunicode import StringUnicodeScenario

# Dict that maps a config field type to a class to instantiate for this type
scenarios = {
    'Arithmetic': ArithmeticScenario,
    'BitBuffer': BitBufferParentScenario,
    'Gradient': GradientScenario,
    'IntBoundary': IntBoundaryScenario,
    'IntChoice': IntChoiceScenario,
    'IntFixed': IntFixedScenario,
    'IntRandom': IntRandomScenario,
    'IntRange': IntRangeScenario,
    'Loop': LoopParentScenario,
    'Regex': RegexScenario,
    'Mapping': MappingScenario,
    'StringFixed': StringFixedScenario,
    'SelectRandom': SelectRandomParentScenario,
    'StringBoundary': StringBoundaryScenario,
    'StringChoice': StringChoiceScenario,
    'StringRandom': StringRandomScenario,
    'StringUnicode': StringUnicodeScenario,
}


def scenario_has_children(scenario_type):
    """
    Checks if the scenario is a scenario with child scenarios
    :param scenario_type: scenario type name
    :type scenario_type: str
    :return: true if scenario has child scenarios, false otherwise
    :rtype: bool
    """
    return issubclass(scenarios[scenario_type], ParentScenario)


def deserialize_scenario(serialized_scenarios, field_props, seed_generator):
    """
    Deserialize a testing scenario from the config file
    :param serialized_scenarios: list of scenarios from the config file
    :param field_props: dictionary of properties that should be added to every field
    :type field_props: dict
    :param seed_generator: generator to generate the default seed from
    :type seed_generator: Random
    :return: list of deserialized scenarios
    :rtype: list
    """

    deserialized_scenarios = list()
    for scenario_item in serialized_scenarios:
        scenario_type = scenario_item['type']

        if scenario_type not in scenarios:
            # Scenario type not found, this should have been caught by the config checker
            raise Exception(f'Unknown scenario {scenario_type} found')

        # Generate the default seed for this field
        field_props['seed'] = seed_generator.randint(-sys.maxsize - 1, sys.maxsize)

        if scenario_has_children(scenario_type):
            # Deserialize child scenarios
            scenario_item['values'] = deserialize_scenario(scenario_item['values'], field_props, seed_generator)

        scenario_object = scenarios[scenario_type]

        # Find the class corresponding to the given type and instantiate it
        argspec = inspect.getfullargspec(scenario_object.__init__).args
        args = {x: scenario_item[x] for x in scenario_item if x in argspec}

        # Add all given parameters as an argument
        args['props'] = scenario_item
        args['field_props'] = field_props

        scenario = scenario_object(*[], **args)
        deserialized_scenarios.append(scenario)

    return deserialized_scenarios
