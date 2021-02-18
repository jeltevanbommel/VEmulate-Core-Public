def parse_allowed_chars(allowed_chars):
    """
    Convert a list structure of allowed characters to a list of characters
    :param allowed_chars: list of characters, list items can be either a string or a list of length two
    with as items two characters indicating a range of characters
    :type allowed_chars: list
    :return: list of characters
    :rtype: [str]
    """
    result = []
    for e in allowed_chars:
        if type(e) is list:
            char_range = e
            if len(e) != 2:
                raise ValueError()
            for n in range(ord(char_range[0]), ord(char_range[1]) + 1):
                result.append(chr(n))
        elif type(e) is str:
            for c in e:
                result.append(c)
        else:
            raise TypeError()
    return result
