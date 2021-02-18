from .outputinterface import OutputInterface


class FileOutput(OutputInterface):
    def __init__(self, file_path):
        """
        Output for writing messages to a file
        :param file_path: path of the file to write to
        """
        try:
            self.file = open(file_path, 'wb')
        except FileNotFoundError:
            self.file = None

    def available(self) -> bool:
        return self.file is not None

    def write(self, data) -> bool:
        result = self.file.write(data)
        self.file.flush()
        return result