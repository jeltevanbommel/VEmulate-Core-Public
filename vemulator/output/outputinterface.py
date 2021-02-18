class OutputInterface:
    """
    Interface class for writing text and hex messages.
    """

    def available(self) -> bool:
        """
        Check if the output is available to write to
        :return: true if the input is available, false if it is not available
        :rtype: bool
        """
        raise NotImplementedError

    def write(self, data) -> bool:
        """
        Write bytes to the output
        :param data: data to write
        :type data: bytes
        :return: true if the data was successfully written, false otherwise
        :rtype: bool
        """
        raise NotImplementedError
