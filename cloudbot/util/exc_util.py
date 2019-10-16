from typing import Union, Type, Tuple

__all__ = ('get_cause_chain', 'get_root_cause', 'match_any_in_chain', 'match_root_cause')


def get_cause_chain(exc):
    while exc:
        yield exc
        # Get "direct cause of" or
        # "during handling of ..., another exception occurred" stack
        cause = getattr(exc, '__cause__', None)
        context = getattr(exc, '__context__', None)
        exc = cause or context


def get_root_cause(exc):
    return list(get_cause_chain(exc))[-1]


ExcType = Union[Type, Tuple[Type]]


def match_any_in_chain(exc, exc_type: ExcType):
    for err in get_cause_chain(exc):
        if isinstance(err, exc_type):
            return True, err

    return False, None


def match_root_cause(exc, exc_type: ExcType):
    return isinstance(get_root_cause(exc), exc_type)
