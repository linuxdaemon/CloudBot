from .hook import Hook


class IrcOutHook(Hook):
    def __init__(self, plugin, out_hook):
        super().__init__("irc_out", plugin, out_hook)

    def __repr__(self):
        return "Irc_Out[{}]".format(Hook.__repr__(self))

    def __str__(self):
        return "irc_out {} from {}".format(self.function_name, self.plugin.file_name)
