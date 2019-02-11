import venusian


class api:
    def __init__(self, name):
        self.name = name

    def __call__(self, wrapped):
        def cb_callback(scanner, name, ob):
            scanner.plugin.apis[self.name] = ob

        venusian.attach(wrapped, cb_callback, category='cloudbot.api')
        return wrapped
