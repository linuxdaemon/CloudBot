from .hook import Hook


class CommandHook(Hook):
    """
    :type name: str
    :type aliases: list[str]
    :type doc: str
    :type auto_help: bool
    """

    def __init__(self, plugin, cmd_hook):
        """
        :type plugin: Plugin
        :type cmd_hook: cloudbot.util.hook._CommandHook
        """
        self.auto_help = cmd_hook.kwargs.pop("autohelp", True)

        self.name = cmd_hook.main_alias.lower()
        self.aliases = [alias.lower() for alias in cmd_hook.aliases]  # turn the set into a list
        self.aliases.remove(self.name)
        self.aliases.insert(0, self.name)  # make sure the name, or 'main alias' is in position 0
        self.doc = cmd_hook.doc

        super().__init__("command", plugin, cmd_hook)

    def __repr__(self):
        return "Command[name: {}, aliases: {}, {}]".format(self.name, self.aliases[1:], Hook.__repr__(self))

    def __str__(self):
        return "command {} from {}".format("/".join(self.aliases), self.plugin.file_name)
