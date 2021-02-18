import functools
import sre_parse
from random import Random
from re import match, UNICODE
from sre_constants import NEGATE, LITERAL, RANGE, CATEGORY, CATEGORY_DIGIT, CATEGORY_NOT_DIGIT, CATEGORY_SPACE, \
    CATEGORY_NOT_SPACE, CATEGORY_WORD, CATEGORY_NOT_WORD, CATEGORY_LINEBREAK, CATEGORY_NOT_LINEBREAK, IN, ANY, \
    MAX_REPEAT, MIN_REPEAT, BRANCH, SUBPATTERN, AT, NOT_LITERAL, GROUPREF

from ..util.log import init_logger

CHARSET = [chr(x) for x in range(32, 123)]

# Only using the common metacharacters https://www3.ntu.edu.sg/home/ehchua/programming/howto/Regexe.html
METACHARACTERS = {
    CATEGORY_DIGIT: frozenset('0123456789'),
    CATEGORY_NOT_DIGIT: [chr(x) for x in range(256) if match('\D', chr(x), UNICODE)],
    CATEGORY_SPACE: [' '],
    # We exclude \n and tabs, since the text protocol is not happy if we generate those. If these can be included,
    # add ' \t\n\r\v\f' to the CATEGORY_SPACE set.
    CATEGORY_NOT_SPACE: [chr(x) for x in range(256) if match('\S', chr(x), UNICODE)],
    CATEGORY_WORD: [chr(x) for x in range(256) if match('\w', chr(x), UNICODE)],
    CATEGORY_NOT_WORD: [chr(x) for x in range(256) if match('\W', chr(x), UNICODE)],
    CATEGORY_LINEBREAK: ['\n'],
    CATEGORY_NOT_LINEBREAK: [chr(x) for x in range(256) if match('[^\n]', chr(x), UNICODE)]
}


class RegexToString:
    """
    Class used to convert a regex pattern to a string that matches the regex
    """
    def __init__(self, regex, seed=0):
        """
        Create a regex to string generator
        :param regex: regular expression to base the string generation on
        :type regex: str
        :param seed: seed to use for the random generator
        :type seed: int
        """
        self.randgen = Random(seed)
        self.logger = init_logger(__name__)
        self.tokens = self.__parse(regex)
        self.min_length = self.__length_regex(self.tokens, minimum=True)[0]
        self.max_length = self.__length_regex(self.tokens, minimum=False)[0]

    def create_valid_string(self):
        """
        Generate a string that matches the regex
        :return: a generated string that matches the regex
        :rtype: str
        """
        return self.__create_valid_string(self.tokens)

    def __create_valid_string(self, tokens, groups=None):
        """
        Generate a string that matches the regex
        :param tokens: tokenized regex
        :type tokens: list
        :param groups: regex groups
        :type groups: dict or None
        :return: a generated string that matches the regex
        :rtype: str
        """
        if groups is None:
            groups = {}

        valid_string = ""
        for op in tokens:
            if op[0] == LITERAL:
                # The literal defined in the operation is added to the string.
                valid_string += chr(op[1])
            elif op[0] == NOT_LITERAL:
                # A symbol from the character set that is not the literal defined in the operation is added to the
                # string
                valid_string += self.randgen.choice([x for x in CHARSET if x != chr(op[1])])
            elif op[0] == ANY:
                # Any symbol from our pre-defined charset is added to the string.
                valid_string += self.randgen.choice(CHARSET)
            elif op[0] == CATEGORY:
                # A symbol from a specific (built-in RegEx) category is added to the string.
                valid_string += self.randgen.choice(METACHARACTERS.get(op[1], ['']))
            elif op[0] == IN:
                # A symbol is added to the string that is in a given set. The set is generated in the __in_symbols
                # function.
                valid_string += self.randgen.choice(self.__in_symbols(op[1]))
            elif op[0] == BRANCH:
                # So if we branch, we can immediately say which branch we take, and do not have to generate both
                # of the possible branch values. Therefore (recursively) create a string for a choice of branch.
                valid_string += self.__create_valid_string(self.randgen.choice(op[1][1]), groups)
            elif op[0] == SUBPATTERN:
                # Parentheses indicate that we have a subpattern, evaluate the subpattern's pattern with
                # create_valid_string
                subpattern = self.__create_valid_string(op[1][3], groups)
                valid_string += subpattern  # append it to the valid string
                groups[op[1][0]] = subpattern  # and save the subpattern as a group in the group dictionary.
                # op[1][0] contains the group number.
            elif op[0] == GROUPREF:
                # We referenced a prior group with \1 or any other digit, in the regex. Every group in the substring
                # is added to a group dictionary when parentheses are encountered. Therefore it can easily be retrieved
                # from the dictionary.
                valid_string += groups[op[1]]
            elif op[0] == MAX_REPEAT or op[0] == MIN_REPEAT:
                # A repeat contains a minimum and a maximum amount to repeat. It may be the case that a range exceeds
                # 20 iterations. In that case the value is likely too long for the text protocol and therefore
                # generation will not include ranges longer than 20.
                min_range, max_range = op[1][0], op[1][1]
                if max_range - min_range > 20:
                    max_range = min_range + 20
                # Append valid string a random amount of times (between min_range and max_range)
                for _ in range(self.randgen.randint(min_range, max_range)):
                    valid_string += self.__create_valid_string(list(op[1][2]), groups)
            elif op[0] == AT:
                pass
            else:
                self.logger.error(f'RegEx operation {op} is not supported. Generated value from RegEx may be invalid.')
        return valid_string

    def create_invalid_string(self):
        """
        Generate a string that LIKELY does not match the regex, with a length such that it could match the regex
        :return: a generated string that MIGHT not match the regex
        :rtype: str
        """
        # Need to do this, instead of creating a valid string and taking the length of that
        # Because in that case we might infinitely create wrongly marked invalid strings
        # in the case of a regex of the sort: ([a-Z0-9]{24}|[0-9]{0,23}). Where a valid
        # string is chosen with length 24.
        return ''.join(self.randgen.choices(CHARSET, k=self.randgen.randint(self.min_length, self.max_length)))

    def create_min_invalid_string(self):
        """
        Generate a string that LIKELY does not match the regex, with the minimum length such that it could match the regex
        :return: a generated string that MIGHT not match the regex
        :rtype: str
        """
        return ''.join(self.randgen.choices(CHARSET, k=self.min_length))

    def create_max_invalid_string(self):
        """
        Generate a string that LIKELY does not match the regex, with the maximum length such that it could match the regex
        :return: a generated string that MIGHT not match the regex
        :rtype: str
        """
        return ''.join(self.randgen.choices(CHARSET, k=self.max_length))

    @staticmethod
    def __parse(regex):
        """
        Tokenize the regex
        :param regex: regex to tokenize
        :type regex: str
        :return: tokenized regex
        :rtype: list
        """
        return list(sre_parse.parse(regex))

    @staticmethod
    def __length_regex(tokens, groups=None, minimum=True):
        """
        Get the string length of the regex
        :param tokens: tokenized regex
        :type tokens: list
        :param groups: regex groups
        :type groups: dict
        :param minimum: indicates whether the function should return the shortest or longest possible length,
        set to True to return the length of the shortest possible string that matches the regex and False for
        the length of the longest possible string
        :type minimum: bool
        :return: the length of the shortest/longest possible string that matches the regex and
        """
        if groups is None:
            groups = {}
        length = 0
        for op in tokens:
            if op[0] == LITERAL or op[0] == NOT_LITERAL or op[0] == ANY or op[0] == CATEGORY or op[0] == IN:
                length += 1
            elif op[0] == BRANCH:
                branches = list(
                    map(functools.partial(RegexToString.__length_regex, groups=groups.copy(), minimum=minimum), list(op[1][1])))
                if len(branches) > 0:
                    length += min(branches, key=(lambda k: k[0]))[0] if minimum else \
                    max(branches, key=(lambda k: k[0]))[0]
            elif op[0] == SUBPATTERN:
                subpattern_length = RegexToString.__length_regex(op[1][3], groups, minimum)
                length += subpattern_length[0]
                groups[len(groups)+1] = subpattern_length[0]
            elif op[0] == GROUPREF:
                length += groups[op[1]]
            elif op[0] == MAX_REPEAT or op[0] == MIN_REPEAT:
                multiplier = op[1][0] if minimum else min(20, op[1][1])
                branch_length = RegexToString.__length_regex(list(op[1][2]), groups, minimum)[0]
                length += branch_length * multiplier
        return length, groups

    @staticmethod
    def __in_symbols(tokens):
        """
        Generates a list of possible characters that are allowed according to the regex
        :param tokens: tokenized regex
        :type tokens: list
        :return: list of valid symbols/characters
        :rtype: list
        """
        valid_symbols = []
        negation = False  # By default no negation
        for op in tokens:
            # We have different behavior depending on whether we have seen a negation symbol, or not
            # If the negation opcode is seen, store this.
            if op[0] == NEGATE:
                valid_symbols = CHARSET  #
                negation = True
            else:  # if the negation opcode is not yet seen
                if negation and op[0] == LITERAL and chr(op[1]) in valid_symbols:
                    # Remove the literal char from the valid_symbols
                    valid_symbols.remove(chr(op[1]))
                elif op[0] == LITERAL:  # Add the literal char to the valid_symbols
                    valid_symbols.append(chr(op[1]))
                elif negation and op[0] == RANGE:  # Remove a range of ascii characters from the valid_symbols
                    valid_symbols = [x for x in valid_symbols if x not in map(chr, range(op[1][0], op[1][1] + 1))]
                elif op[0] == RANGE:  # Add a range of ascii characters to the valid_symbols
                    valid_symbols.extend(map(chr, range(op[1][0], op[1][1] + 1)))
                elif negation and op[0] == CATEGORY:  # Remove a category of characters from the valid_symbols
                    valid_symbols = [x for x in valid_symbols if x not in METACHARACTERS.get(op[1], [''])]
                elif op[0] == CATEGORY:  # Add a category of characters from the valid_symbols
                    valid_symbols.extend(METACHARACTERS.get(op[1], ['']))
        return valid_symbols
