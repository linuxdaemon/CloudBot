from .hook import Hook


class RegexHook(Hook):
    """
    :type regexes: set[re.__Regex]
    """

    def __init__(self, plugin, regex_hook):
        """
        :type plugin: Plugin
        :type regex_hook: cloudbot.util.hook._RegexHook
        """
        self.run_on_cmd = regex_hook.kwargs.pop("run_on_cmd", False)
        self.only_no_match = regex_hook.kwargs.pop("only_no_match", False)

        self.regexes = regex_hook.regexes

        super().__init__("regex", plugin, regex_hook)

    def __repr__(self):
        return "Regex[regexes: [{}], {}]".format(", ".join(regex.pattern for regex in self.regexes),
                                                 Hook.__repr__(self))

    def __str__(self):
        return "regex {} from {}".format(self.function_name, self.plugin.file_name)
