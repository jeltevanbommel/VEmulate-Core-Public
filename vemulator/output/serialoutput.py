from serial import Serial
from serial.serialutil import SerialException

from .outputinterface import OutputInterface


class SerialOutput(OutputInterface):
    def __init__(self, port, baud_rate=19200):
        """
        Writes messages to a serial interface
        :param port: serial port to open and read from, such as COM0 or /dev/tty0
        :type port: str
        :param baud_rate: baud rate to write at; 19200 by default
        :type baud_rate: int
        """
        try:
            self.serial = Serial(port, baud_rate)
        except SerialException:
            self.serial = None

    def available(self) -> bool:
        return self.serial is not None

    def write(self, data) -> bool:
        try:
            result = bool(self.serial.write(data))
            self.serial.flush()
            return result
        except SerialException:
            return False