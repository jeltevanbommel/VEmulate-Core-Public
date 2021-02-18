import datetime
from threading import Thread, RLock

from vemulator.events.field_event import FieldEvent
from vemulator.util.log import init_logger


class EventQueue(Thread):
    """
    A class that represents a time based event queue.
    An EventQueue is typically bound to an Emulator for which it will create and start events that will
    asynchronously generate and update values for the fields/generators present in the Emulator.
    """
    events = {}
    lock = RLock()
    logger = None

    def __init__(self, emulator):
        """
        Create an event queue that is tied to a specific emulator.
        :param emulator: The emulator used to launch the first few events.
        :type emulator: Emulator
        """
        super().__init__()
        self.emulator = emulator
        self.emulator.observable.on('overwrite_generators', self.refresh_event)
        self.emulator.observable.on('overwrite_hex_generators', self.refresh_event)
        self.logger = init_logger(__name__)
        self.generate_first_values()  # generate a first value for every key in the emulator

    def run(self):
        """
        Start event queue by adding one event for all generators.
        """
        self.logger.debug(f'running event_queue')
        with self.lock:
            for k in self.emulator.get_scenario_keys():
                event = self.new_field_event(k)
                self.add_event(k, event)
                self.emulator.logger.debug(f'adding event {event}')

    def add_event(self, key, event):
        """
        Add an event to the event queue
        :param key: key that corresponds to a key in the emulator. The event to be added is supposed to be related
        to that key.
        :type key: str or int
        :param event: event to be added to the event queue
        :type event: Event
        """
        if event is not None:
            with self.lock:
                self.events[key] = event

    def remove_event(self, key, event):
        """
        Remove an event from the event queue
        :param key: key that corresponds to a key in the emulator. The event to be added is supposed to be related
        to that key.
        :type key: str or int
        :param event: event to be removed from the event queue
        :type event: Event
        """
        if event is not None:
            with self.lock:
                current_event = self.events.get(self, key)
                if current_event == event:
                    self.events.pop(key).cancel()

    def refresh_event(self, key):
        """
        Refresh an event when something is updated about its corresponding field_key in the emulator.
        If an old event exists for the field_key, it is cancelled and removed from the queue.
        A new event will be added to the event queue to replace the old event.
        :param key: the field_key for which to refresh the event
        :type key: str or int
        """
        with self.lock:
            event = self.events.get(key, None)
            if event is not None:
                event.cancel()
            new_event = self.new_field_event(key)
            if new_event is not None:
                self.add_event(key, new_event)

    def new_field_event(self, field_key):
        """
        Create a new event for this key.
        :param field_key: emulator key for which an event will be created.
        :type field_key: str or int
        :return: a newly created event
        :rtype: ScenarioEvent
        """
        generator = self.emulator.get_field_scenarios(field_key)
        if generator is not None:
            return FieldEvent(field=generator, base_time=datetime.datetime.now(),
                              event_queue=self, field_key=field_key)
        else:
            return

    def generate_first_values(self):
        """
        Generate the first value for every key in the emulator.
        """
        for k in self.emulator.get_scenario_keys():
            scenarios = self.emulator.get_field_scenarios(k)
            scenarios[0].generate_next(self.emulator.get_field_values())
