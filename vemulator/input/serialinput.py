from serial import Serial
from serial.serialutil import SerialException

from .inputinterface import InputInterface


class SerialInput(InputInterface):
    def __init__(self, port, baud_rate=19200):
        """
        Reads input from a serial interface
        :param port: serial port to open and read from, such as COM0 or /dev/tty0
        :type port: str
        :param baud_rate: baud rate to read at; 19200 by default
        :type baud_rate: int
        """
        try:
            self.serial = Serial(port, baud_rate)
        except SerialException:
            self.serial = None

    def available(self) -> bool:
        return self.serial is not None

    def has_data(self) -> bool:
        try:
            return self.available() and self.serial.in_waiting > 0
        except OSError:
            return False

    def readline(self) -> bytes:
        try:
            return self.serial.readline()
        except SerialException:
            return b''
