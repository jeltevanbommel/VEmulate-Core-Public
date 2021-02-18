from .inputinterface import InputInterface


class TestInput(InputInterface):
    def __init__(self, lines=[]):
        """
        Input that can be used in unit tests.
        :param lines: lines of text
        :type lines: [str]
        """
        try:
            self.lines = lines
        except FileNotFoundError:
            self.file = None

    def available(self) -> bool:
        return True

    def has_data(self) -> bool:
        return len(self.lines) > 0

    def writeline(self, line):
        """
        Write a new line to the internal lines buffer, which can later be read by `readline`
        :param line: line of text
        :type line: str
        """
        self.lines.append(line)

    def readline(self) -> bytes:
        return self.lines.pop(0)
