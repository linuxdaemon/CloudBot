import venusian

__all__ = ('api', 'client')


class SimpleDecorator:
    def __init__(self, category):
        self._category = category

    def cb_register(self, scanner, name, ob):
        raise NotImplementedError

    def __call__(self, wrapped):
        venusian.attach(wrapped, self.cb_register, category=self._category)
        return wrapped


class api(SimpleDecorator):
    def __init__(self, name):
        super().__init__('cloudbot.api')
        self.name = name

    def cb_register(self, scanner, name, ob):
        scanner.plugin.apis[self.name] = ob


class client(SimpleDecorator):
    def __init__(self, name):
        super().__init__('cloudbot.client')
        self.name = name

    def cb_register(self, scanner, name, ob):
        scanner.bot.add_client(self.name, ob)
