import sys

from .outputinterface import OutputInterface


class StandardOutput(OutputInterface):
    def __init__(self):
        """
        Write messages to the standard output (stdout)
        """
        pass

    def available(self) -> bool:
        return sys.stdout.buffer.writable()

    def write(self, data) -> bool:
        result = bool(sys.stdout.buffer.write(data))
        sys.stdout.buffer.flush()
        return result