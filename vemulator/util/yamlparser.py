import yaml
from yaml.composer import Composer
from yaml.constructor import Constructor


def load_yaml(config):
    """
    Loads a yaml file
    :param config: configuration file stream or string
    :type config: TextIO or str
    :return: deserialized version of the yaml config or None if deserialization failed
    :rtype: dict or None
    """
    try:
        return yaml.safe_load(config)
    except yaml.YAMLError as e:
        raise Exception('Error occurred while parsing YAML: {}'.format(e))

def load_yaml_with_lines(config):
    """
    Loads a yaml file and adds line numbers to the objects
    :param config: configuration file stream or string
    :type config: TextIO or str
    :return: deserialized version of the yaml config or None if deserialization failed
    :rtype: dict or None
    """
    try:
        # Source: https://stackoverflow.com/a/13319530
        loader = yaml.Loader(config)

        def compose_node(parent, index):
            # the line number where the previous token has ended (plus empty lines)
            line = loader.line
            node = Composer.compose_node(loader, parent, index)
            node.__line__ = line + 1
            return node

        def construct_mapping(node, deep=False):
            mapping = Constructor.construct_mapping(loader, node, deep=deep)
            mapping['__line__'] = node.__line__
            return mapping

        loader.compose_node = compose_node
        loader.construct_mapping = construct_mapping
        return loader.get_single_data()
    except yaml.YAMLError as e:
        raise Exception('Error occurred while parsing YAML: {}'.format(e))
