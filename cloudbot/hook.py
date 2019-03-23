import collections
import inspect
import re

from .event import EventType
from .hooks import (
    CommandHook, EventHook, IrcOutHook, OnCapAckHook, OnCapAvaliableHook, OnConnectHook, OnStartHook,
    OnStopHook, PeriodicHook, PermHook, PostHookHook, RawHook, RegexHook, SieveHook,
)
from .plugin import HOOK_ATTR

__all__ = (
    'command', 'event',
    'permission', 'irc_raw', 'irc_out', 'sieve',
    'periodic', 'post_hook', 'regex', 'on_start',
    'on_stop', 'onload', 'on_unload', 'on_cap_ack',
    'on_cap_available', 'connect', 'on_connect',
)

valid_command_re = re.compile(r"^\w+$")


class _Hook:
    """
    :type function: function
    :type type: str
    :type kwargs: dict[str, unknown]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        self.function = function
        self.kwargs = {}

    def _add_hook(self, kwargs):
        """
        :type kwargs: dict[str, unknown]
        """
        # update kwargs, overwriting duplicates
        self.kwargs.update(kwargs)

    @staticmethod
    def get_type():
        raise NotImplementedError

    @property
    def type(self):
        return self.get_type()

    @classmethod
    def get(cls, func):
        hook = _get_hook(func, cls.get_type())
        if hook is None:
            hook = cls(func)
            _add_hook(func, hook)

        return hook

    @staticmethod
    def get_full_hook():
        raise NotImplementedError

    def make_full_hook(self, plugin):
        return self.get_full_hook()(plugin, self)


class _CommandHook(_Hook):
    """
    :type main_alias: str
    :type aliases: set[str]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function)
        self.aliases = set()
        self.main_alias = None

        if function.__doc__:
            doc = inspect.cleandoc(function.__doc__)
            # Split on the first entirely blank line
            self.doc = ' '.join(doc.split('\n\n', 1)[0].strip('\n').split('\n')).strip()
        else:
            self.doc = None

    def add_hook(self, alias_param, kwargs):
        """
        :type alias_param: list[str] | str
        """
        self._add_hook(kwargs)

        if not alias_param:
            alias_param = self.function.__name__
        if isinstance(alias_param, str):
            alias_param = [alias_param]
        if not self.main_alias:
            self.main_alias = alias_param[0]
        for alias in alias_param:
            if not valid_command_re.match(alias):
                raise ValueError("Invalid command name {}".format(alias))
        self.aliases.update(alias_param)

    @staticmethod
    def get_type():
        return "command"

    @staticmethod
    def get_full_hook():
        return CommandHook


class _RegexHook(_Hook):
    """
    :type regexes: list[re.__Regex]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function)
        self.regexes = []

    def add_hook(self, regex_param, kwargs):
        """
        :type regex_param: Iterable[str | re.__Regex] | str | re.__Regex
        :type kwargs: dict[str, unknown]
        """
        self._add_hook(kwargs)
        # add all regex_parameters to valid regexes
        if isinstance(regex_param, str):
            # if the parameter is a string, compile and add
            self.regexes.append(re.compile(regex_param))
        elif hasattr(regex_param, "search"):
            # if the parameter is an re.__Regex, just add it
            # we only use regex.search anyways, so this is a good determiner
            self.regexes.append(regex_param)
        else:
            assert isinstance(regex_param, collections.Iterable)
            # if the parameter is a list, add each one
            for re_to_match in regex_param:
                if isinstance(re_to_match, str):
                    re_to_match = re.compile(re_to_match)
                else:
                    # make sure that the param is either a compiled regex, or has a search attribute.
                    assert hasattr(re_to_match, "search")
                self.regexes.append(re_to_match)

    @staticmethod
    def get_type():
        return "regex"

    @staticmethod
    def get_full_hook():
        return RegexHook


class _RawHook(_Hook):
    """
    :type triggers: set[str]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function)
        self.triggers = set()

    @staticmethod
    def get_type():
        return "irc_raw"

    def add_hook(self, trigger_param, kwargs):
        """
        :type trigger_param: list[str] | str
        :type kwargs: dict[str, unknown]
        """
        self._add_hook(kwargs)

        if isinstance(trigger_param, str):
            self.triggers.add(trigger_param)
        else:
            # it's a list
            self.triggers.update(trigger_param)

    @staticmethod
    def get_full_hook():
        return RawHook


class _PeriodicHook(_Hook):
    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function)
        self.interval = 60.0

    @staticmethod
    def get_type():
        return "periodic"

    def add_hook(self, interval, kwargs):
        """
        :type interval: int
        :type kwargs: dict[str, unknown]
        """
        self._add_hook(kwargs)

        if interval:
            self.interval = interval

    @staticmethod
    def get_full_hook():
        return PeriodicHook


class _EventHook(_Hook):
    """
    :type types: set[cloudbot.event.EventType]
    """

    def __init__(self, function):
        """
        :type function: function
        """
        _Hook.__init__(self, function)
        self.types = set()

    @staticmethod
    def get_type():
        return "event"

    def add_hook(self, trigger_param, kwargs):
        """
        :type trigger_param: cloudbot.event.EventType | list[cloudbot.event.EventType]
        :type kwargs: dict[str, unknown]
        """
        self._add_hook(kwargs)

        if isinstance(trigger_param, EventType):
            self.types.add(trigger_param)
        else:
            # it's a list
            self.types.update(trigger_param)

    @staticmethod
    def get_full_hook():
        return EventHook


class _CapHook(_Hook):
    def __init__(self, func):
        super().__init__(func)
        self.caps = set()

    @classmethod
    def get_type(cls):
        return "on_cap_{}".format(cls.get_subtype())

    @classmethod
    def get_subtype(cls):
        raise NotImplementedError

    def add_hook(self, caps, kwargs):
        self._add_hook(kwargs)
        self.caps.update(caps)


class _CapAckHook(_CapHook):
    @classmethod
    def get_subtype(cls):
        return "ack"

    @staticmethod
    def get_full_hook():
        return OnCapAckHook


class _CapAvailableHook(_CapHook):
    @classmethod
    def get_subtype(cls):
        return "available"

    @staticmethod
    def get_full_hook():
        return OnCapAvaliableHook


class _PermissionHook(_Hook):
    def __init__(self, func):
        super().__init__(func)
        self.perms = set()

    @staticmethod
    def get_type():
        return "perm_check"

    def add_hook(self, perms, kwargs):
        self._add_hook(kwargs)
        self.perms.update(perms)

    @staticmethod
    def get_full_hook():
        return PermHook


class _PostHook(_Hook):
    @staticmethod
    def get_type():
        return "post_hook"

    @staticmethod
    def get_full_hook():
        return PostHookHook


class _IrcOutHook(_Hook):
    @staticmethod
    def get_type():
        return "irc_out"

    @staticmethod
    def get_full_hook():
        return IrcOutHook


class _OnStartHook(_Hook):
    @staticmethod
    def get_type():
        return "on_start"

    @staticmethod
    def get_full_hook():
        return OnStartHook


class _OnStopHook(_Hook):
    @staticmethod
    def get_type():
        return "on_stop"

    @staticmethod
    def get_full_hook():
        return OnStopHook


class _SieveHook(_Hook):
    @staticmethod
    def get_type():
        return "sieve"

    @staticmethod
    def get_full_hook():
        return SieveHook


class _ConnectHook(_Hook):
    @staticmethod
    def get_type():
        return "on_connect"

    @staticmethod
    def get_full_hook():
        return OnConnectHook


def _add_hook(func, hook):
    try:
        hooks = getattr(func, HOOK_ATTR)
    except AttributeError:
        hooks = {}
        setattr(func, HOOK_ATTR, hooks)

    hooks[hook.type] = hook


def _get_hook(func, hook_type):
    try:
        return getattr(func, HOOK_ATTR)[hook_type]
    except (AttributeError, LookupError):
        return None


def command(*args, **kwargs):
    """External command decorator. Can be used directly as a decorator, or with args to return a decorator.
    :type param: str | list[str] | function
    """

    def _command_hook(func, alias_param=None):
        hook = _CommandHook.get(func)
        hook.add_hook(alias_param, kwargs)
        return func

    if len(args) == 1 and callable(args[0]):  # this decorator is being used directly
        return _command_hook(args[0])

    # this decorator is being used indirectly, so return a decorator function
    return lambda func: _command_hook(func, alias_param=args)


def irc_raw(triggers_param, **kwargs):
    """External raw decorator. Must be used as a function to return a decorator
    :type triggers_param: str | list[str]
    """

    def _raw_hook(func):
        hook = _RawHook.get(func)
        hook.add_hook(triggers_param, kwargs)
        return func

    if callable(triggers_param):  # this decorator is being used directly, which isn't good
        raise TypeError("@irc_raw() must be used as a function that returns a decorator")

    # this decorator is being used as a function, so return a decorator
    return _raw_hook


def event(types_param, **kwargs):
    """External event decorator. Must be used as a function to return a decorator
    :type types_param: cloudbot.event.EventType | list[cloudbot.event.EventType]
    """

    def _event_hook(func):
        hook = _EventHook.get(func)
        hook.add_hook(types_param, kwargs)
        return func

    if callable(types_param):  # this decorator is being used directly, which isn't good
        raise TypeError("@irc_raw() must be used as a function that returns a decorator")

    # this decorator is being used as a function, so return a decorator
    return _event_hook


def regex(regex_param, **kwargs):
    """External regex decorator. Must be used as a function to return a decorator.
    :type regex_param: str | re.__Regex | list[str | re.__Regex]
    :type flags: int
    """

    def _regex_hook(func):
        hook = _RegexHook.get(func)
        hook.add_hook(regex_param, kwargs)
        return func

    if callable(regex_param):  # this decorator is being used directly, which isn't good
        raise TypeError("@regex() hook must be used as a function that returns a decorator")

    # this decorator is being used as a function, so return a decorator
    return _regex_hook


def sieve(param=None, **kwargs):
    """External sieve decorator. Can be used directly as a decorator, or with args to return a decorator
    :type param: function | None
    """

    def _sieve_hook(func):
        assert len(inspect.signature(func).parameters) == 3, \
            "Sieve plugin has incorrect argument count. Needs params: bot, input, plugin"

        hook = _SieveHook.get(func)
        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _sieve_hook(param)

    return _sieve_hook


def periodic(interval, **kwargs):
    """External on_start decorator. Can be used directly as a decorator, or with args to return a decorator
    :type param: function | None
    """

    def _periodic_hook(func):
        hook = _PeriodicHook.get(func)
        hook.add_hook(interval, kwargs)
        return func

    if callable(interval):  # this decorator is being used directly, which isn't good
        raise TypeError("@periodic() hook must be used as a function that returns a decorator")

    # this decorator is being used as a function, so return a decorator
    return _periodic_hook


def on_start(param=None, **kwargs):
    """External on_start decorator. Can be used directly as a decorator, or with args to return a decorator
    :type param: function | None
    """

    def _on_start_hook(func):
        hook = _OnStartHook.get(func)
        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _on_start_hook(param)

    return _on_start_hook


# this is temporary, to ease transition
onload = on_start


def on_stop(param=None, **kwargs):
    """External on_stop decorator. Can be used directly as a decorator, or with args to return a decorator
    :type param: function | None
    """

    def _on_stop_hook(func):
        hook = _OnStopHook.get(func)
        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _on_stop_hook(param)

    return _on_stop_hook


on_unload = on_stop


def on_cap_available(*caps, **kwargs):
    """External on_cap_available decorator. Must be used as a function that returns a decorator

    This hook will fire for each capability in a `CAP LS` response from the server
    """

    def _on_cap_available_hook(func):
        hook = _CapAvailableHook.get(func)
        hook.add_hook(caps, kwargs)
        return func

    return _on_cap_available_hook


def on_cap_ack(*caps, **kwargs):
    """External on_cap_ack decorator. Must be used as a function that returns a decorator

    This hook will fire for each capability that is acknowledged from the server with `CAP ACK`
    """

    def _on_cap_ack_hook(func):
        hook = _CapAckHook.get(func)
        hook.add_hook(caps, kwargs)
        return func

    return _on_cap_ack_hook


def on_connect(param=None, **kwargs):
    def _on_connect_hook(func):
        hook = _ConnectHook.get(func)
        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _on_connect_hook(param)

    return _on_connect_hook


connect = on_connect


def irc_out(param=None, **kwargs):
    def _decorate(func):
        hook = _IrcOutHook.get(func)
        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _decorate(param)

    return _decorate


def post_hook(param=None, **kwargs):
    """
    This hook will be fired just after a hook finishes executing
    """

    def _decorate(func):
        hook = _PostHook.get(func)
        hook._add_hook(kwargs)
        return func

    if callable(param):
        return _decorate(param)

    return _decorate


def permission(*perms, **kwargs):
    def _perm_hook(func):
        hook = _PermissionHook.get(func)
        hook.add_hook(perms, kwargs)
        return func

    return _perm_hook
