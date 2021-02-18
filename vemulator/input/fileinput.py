from .inputinterface import InputInterface


class FileInput(InputInterface):
    def __init__(self, file_path):
        """
        Reads input from a file.
        New text can be written to the file while the emulator is running,
        it will process any new lines as soon as they are written.
        :param file_path: path of the file to read from
        :type file_path: str
        """
        try:
            self.file = open(file_path, 'rb')
        except FileNotFoundError:
            self.file = None

    def available(self) -> bool:
        return self.file is not None

    def has_data(self) -> bool:
        if not self.available():
            return False

        cursor = self.file.tell()
        has_line = bool(self.file.readline())
        self.file.seek(cursor)
        return has_line

    def readline(self) -> bytes:
        return self.file.readline()
