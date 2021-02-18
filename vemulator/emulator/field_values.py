from observable import Observable


class FieldValueList:
    """
    List of field values
    """

    field_values = dict()  # key is the normal field key
    hex_formatted_field_values = dict()  # key is the normal hex field key. no special formatting.
    observable = Observable()

    def put_field_value(self, key, value):
        """
        Put a new value in the text field values dictionary
        :param key: key of the field
        :type key: str
        :param value: value of the field
        :type value: str or int
        """
        old_value = self.field_values.get(key, None)
        self.field_values[key] = value
        self.observable.trigger('update_field_value', key, value, old_value)

    def put_hex_field_value(self, key, formatted_hex_value):
        """
        Put a new value in the hex field values dictionary
        :param key: key of the field
        :type: key: int
        :param formatted_hex_value: the hex string formatted value of the field
        :type formatted_hex_value: str
        """
        old_value = self.hex_formatted_field_values.get(key, None)
        self.hex_formatted_field_values[key] = formatted_hex_value
        self.observable.trigger('update_hex_field_value', key, formatted_hex_value, old_value)

    def get_field_value(self, key):
        """
        Get the value of a text field
        :param key: key of the field
        :type key: str
        :return: value of the field
        :rtype: str or int
        """
        return self.field_values.get(key, None)

    def get_hex_field_value(self, key):
        """
        Get the value of a text field
        :param key: key of the field
        :type key: int
        :return: the hex string formatted value of the field
        :rtype: str
        """
        return self.hex_formatted_field_values.get(key, None)

    def get_field_values(self):
        """
        Get all the text field values
        :return: all field values
        :rtype: dict
        """
        return self.field_values



