from .hook import Hook


class PermHook(Hook):
    def __init__(self, plugin, perm_hook):
        self.perms = perm_hook.perms
        super().__init__("perm_check", plugin, perm_hook)

    def __repr__(self):
        return "PermHook[{}]".format(Hook.__repr__(self))

    def __str__(self):
        return "perm hook {} from {}".format(self.function_name, self.plugin.file_name)
