from .hook import Hook


class EventHook(Hook):
    """
    :type types: set[cloudbot.event.EventType]
    """

    def __init__(self, plugin, event_hook):
        """
        :type plugin: Plugin
        :type event_hook: cloudbot.util.hook._EventHook
        """
        super().__init__("event", plugin, event_hook)

        self.types = event_hook.types

    def __repr__(self):
        return "Event[types: {}, {}]".format(list(self.types), Hook.__repr__(self))

    def __str__(self):
        return "event {} ({}) from {}".format(self.function_name, ",".join(str(t) for t in self.types),
                                              self.plugin.file_name)
