import codecs
import math

from .parentscenario import ParentScenario
from ..util import hex


class BitBufferParentScenario(ParentScenario):
    """
    Scenario for composing a value by combining several bits together.

    Example:
    - type: BitBuffer
      values:
        - type: IntFixed
          value: 3
          bits: 5
        - type: IntFixed
          value: 8
          bits: 5
        - type: Mapping
          dict: { 'OFF': '0', 'ON': '1'}
          bits: 6

    This will result in the following output (shown below in binary):

    00011 01000 000001
    3     8     1 or 0

    which will be sent as 6657 using the text protocol or 1A01 (011A in little endian) using the hex protocol
    """

    def __init__(self, props={}, field_props={}):
        super().__init__(props=props, field_props=field_props)
        self.field_values = {}
        self.complete = False

    def _generate(self, field_values):
        value = 0
        bit_size = 0
        new_value = True  # Indicates if there is a new value available
        for field in self.children:
            if not field.is_complete():
                generated_value = field.generate_next(field_values)
                hex_value = hex.value_to_hex_string(generated_value, math.ceil(field.bits / 8), field.props.get('signed', False))
                value = (value << field.bits) + int(hex_value, 16)
                bit_size += field.bits
            else:
                new_value = False

        if not new_value:
            # We are done with value generations for this scenario
            self.value = None
            self.complete = True
        else:
            self.bits = bit_size
            self.value = value

    def is_complete(self):
        return super().is_complete() or self.complete

    def reset(self):
        super().reset()
        self.complete = False

    def get_hex_value(self):
        # We have to override the get_hex_value field since the subfields of the bitbuffer are already little endian
        # encoded, so the final value should not be little endian encoded again
        return codecs.encode(self.value.to_bytes(math.ceil(self.bits / 8), 'big'), 'hex').decode('utf-8').upper()
