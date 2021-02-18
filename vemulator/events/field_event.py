from vemulator.events.interval_event import IntervalEvent


class FieldEvent(IntervalEvent):
    """
    A type of IntervalEvent that is intended to executed based on delays as specified in the configuration of the field
     to which this event belongs.
    """

    def __init__(self, field, base_time, event_queue, field_key):
        """
        Create a FieldEvent
        :param field: the field to which this event belongs
        :param base_time: see IntervalEvent.base_time
        :param event_queue: see IntervalEvent.event_queue
        :param field_key: field key from the emulator with which this field event and its corresponding field can identified.
        """
        self.scenario = field[0]
        super().__init__(
            interval=self.scenario.interval,
            base_time=base_time,
            event_queue=event_queue,
            key=field_key)
        self.field = field
        self.event_queue = event_queue

    def _function(self):
        """
        See Event._function()
        """
        with self.event_queue.lock:
            if self._generation_needed():
                self.scenario.generate_next(self.event_queue.emulator.field_values)
                if self.scenario.is_complete():
                    self.field.pop(0)
                    if len(self.field) == 0:
                        self.event_queue.logger.debug('field finished successfully!')
                self.event_queue.emulator.logger.debug(
                    f'generated new value {self.scenario.get_value()} for scenario {self.key} of type {self.scenario.__class__}')
                super()._function()
            else:
                self.event_queue.emulator.logger.debug(
                    f'Scenario {self.scenario} is no longer first in {self.field}')
                # field has been modified externally, probably by the emulator.
                #   the observable pattern takes care of the rest, but this scenario
                #   event should not repeat itself nor generate any more values

    def _next_event(self):
        """
        See IntervalEvent._next_event()
        """
        return FieldEvent(field=self.field, base_time=self.deadline, event_queue=self.event_queue, field_key=self.key)

    def _next_event_needed(self):
        """
        See IntervalEvent._next_event_needed()
        """
        return not (self.scenario.is_complete() and len(self.field) == 0)

    def _generation_needed(self):
        """
        Check if the generation of the next field value is needed.
        :return: true if generation is needed, false otherwise
        :rtype: bool
        """
        return self.field[0] == self.scenario  # if False, this means that the field has been overwritten by the emulator.
