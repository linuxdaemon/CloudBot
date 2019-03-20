from .hook import Hook


class OnConnectHook(Hook):
    def __init__(self, plugin, sieve_hook):
        """
        :type plugin: Plugin
        :type sieve_hook: cloudbot.util.hook._Hook
        """
        super().__init__("on_connect", plugin, sieve_hook)

    def __repr__(self):
        return "{name}[{base!r}]".format(name=self.type, base=super())

    def __str__(self):
        return "{name} {func} from {file}".format(name=self.type, func=self.function_name, file=self.plugin.file_name)
