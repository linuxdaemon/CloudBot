from .hook import Hook


class CapHook(Hook):
    def __init__(self, _type, plugin, base_hook):
        self.caps = base_hook.caps
        super().__init__("on_cap_{}".format(_type), plugin, base_hook)

    def __repr__(self):
        return "{name}[{caps} {base!r}]".format(name=self.type, caps=self.caps, base=super())

    def __str__(self):
        return "{name} {func} from {file}".format(name=self.type, func=self.function_name, file=self.plugin.file_name)


class OnCapAvaliableHook(CapHook):
    def __init__(self, plugin, base_hook):
        super().__init__("available", plugin, base_hook)


class OnCapAckHook(CapHook):
    def __init__(self, plugin, base_hook):
        super().__init__("ack", plugin, base_hook)
