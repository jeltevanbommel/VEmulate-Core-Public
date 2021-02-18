class InputInterface:
    """
    Interface class for reading hex commands.
    """

    def available(self) -> bool:
        """
        Check if the input is available to be read from
        :return: true if the input is available, false if it is not available
        :rtype: bool
        """
        raise NotImplementedError

    def has_data(self) -> bool:
        """
        Check if there is any data available to be read from the buffer
        :return: true if there is data available, false otherwise
        :rtype: bool
        """
        raise NotImplementedError

    def readline(self) -> bytes:
        """
        Read line as binary data from the input
        :return: read data
        :rtype: bytes
        """
        raise NotImplementedError
