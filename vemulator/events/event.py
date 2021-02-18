import datetime
from threading import Timer


class Event(Timer):
    """
    A class that represents an event which causes a task to execute at a defined length of time in the future.
    Events are stored in the EventQueue.
    """
    task = None

    def __init__(self, deadline=datetime.datetime.now()):
        """
        Create an Event which will try to execute a function as soon as possible after a specified deadline has passed.
        :param deadline: a point in time until which the event has to wait with execution
        :type deadline: datetime.datetime
        """
        delay = (deadline - datetime.datetime.now()).total_seconds()
        # delay can be negative, but that means that this event is created too late.
        # a Timer with a negative delay simply executes as soon as possible.
        super().__init__(delay, self._function)
        self.deadline = deadline
        self.start()

    def _function(self):
        """
        Function to execute when the deadline has passed.
        Subclasses should override this method for any core functionality
        """
        pass  # implement in subclasses to achieve any results
