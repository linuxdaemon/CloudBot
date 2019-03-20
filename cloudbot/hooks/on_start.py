from .hook import Hook


class OnStartHook(Hook):
    def __init__(self, plugin, on_start_hook):
        """
        :type plugin: Plugin
        :type on_start_hook: cloudbot.util.hook._On_startHook
        """
        super().__init__("on_start", plugin, on_start_hook)

    def __repr__(self):
        return "On_start[{}]".format(Hook.__repr__(self))

    def __str__(self):
        return "on_start {} from {}".format(self.function_name, self.plugin.file_name)
