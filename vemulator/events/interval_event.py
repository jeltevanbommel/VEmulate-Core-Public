import datetime

from vemulator.events.event import Event


class IntervalEvent(Event):
    """
    An event that is intended to be repeated at a specified interval.
    That is, every x seconds a new IntervalEvent will be created to
    replace its preceding IntervalEvent in the EventQueue
    """

    def __init__(self, interval, base_time, event_queue, key):
        """
        Create an IntervalEvent
        :param interval: time in seconds between occurrences of this event.
        :param base_time: the time in seconds from which the deadline is calculated by adding interval.
        :param event_queue: event queue of which this event will be a part.
        :param key: key from the event queue with which this event can be identified
        """
        super().__init__(deadline=base_time + datetime.timedelta(seconds=interval))
        self.interval = interval  # seconds
        self.event_queue = event_queue
        self.key = key

    def _function(self):
        """
        See Event._function()
        """
        with self.event_queue.lock:
            self.event_queue.remove_event(self.key, self)
            self._repeat()

    def _next_event(self):
        """
        Create a new event
        :return: a new event
        :rtype: IntervalEvent
        """
        return IntervalEvent(self.interval, self.deadline, self.event_queue, self.key)

    def _next_event_needed(self):
        """
        Check any conditions that may apply to the repetition of the interval event
        :return: True if all conditions for repetition are satisfied
        :rtype: bool
        """
        return True

    def _repeat(self):
        """
        Repeat the event
        """
        if self._next_event_needed():
            self.event_queue.add_event(self.key, self._next_event())
