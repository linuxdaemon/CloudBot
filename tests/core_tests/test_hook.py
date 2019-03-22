import re

import pytest

from cloudbot import hook
from cloudbot.event import EventType
from cloudbot.plugin import HOOK_ATTR


def test_hook_decorate():
    @hook.event(EventType.message)
    @hook.event([EventType.notice, EventType.action])
    @hook.command('test')
    @hook.irc_raw('*')
    @hook.irc_raw(['PRIVMSG'])
    @hook.irc_out
    @hook.on_stop()
    @hook.regex(['test', re.compile('test')])
    def f():
        pass  # pragma: no cover

    assert getattr(f, HOOK_ATTR)['event'].types == {
        EventType.message, EventType.notice, EventType.action
    }
    assert getattr(f, HOOK_ATTR)['command'].aliases == {'test'}
    assert getattr(f, HOOK_ATTR)['irc_raw'].triggers == {'*', 'PRIVMSG'}
    assert 'irc_out' in getattr(f, HOOK_ATTR)
    assert 'on_stop' in getattr(f, HOOK_ATTR)
    assert 'regex' in getattr(f, HOOK_ATTR)
    assert len(getattr(f, HOOK_ATTR)['regex'].regexes) == 2

    with pytest.raises(ValueError, match="Invalid command name test 123"):
        hook.command('test 123')(f)

    with pytest.raises(TypeError):
        hook.periodic(f)

    with pytest.raises(TypeError):
        hook.regex(f)

    with pytest.raises(TypeError):
        hook.event(f)

    with pytest.raises(TypeError):
        hook.irc_raw(f)

    @hook.sieve
    def sieve_func(bot, event, _hook):
        pass  # pragma: no cover

    assert 'sieve' in getattr(sieve_func, HOOK_ATTR)


def test_command_hook_doc():
    @hook.command
    def test(bot):
        """<arg> - foo
        bar
        baz

        :type bot: object"""

    cmd_hook = getattr(test, HOOK_ATTR)['command']
    assert cmd_hook.doc == "<arg> - foo bar baz"

    @hook.command
    def test1(bot):
        """<arg> - foo bar baz

        :type bot: object"""

    cmd_hook = getattr(test1, HOOK_ATTR)['command']
    assert cmd_hook.doc == "<arg> - foo bar baz"

    @hook.command
    def test2(bot):
        """<arg> - foo bar baz"""

    cmd_hook = getattr(test2, HOOK_ATTR)['command']
    assert cmd_hook.doc == "<arg> - foo bar baz"

    @hook.command
    def test3(bot):
        """
        <arg> - foo bar baz
        """

    cmd_hook = getattr(test3, HOOK_ATTR)['command']
    assert cmd_hook.doc == "<arg> - foo bar baz"

    @hook.command
    def test4(bot):
        """<arg> - foo bar baz
        """

    cmd_hook = getattr(test4, HOOK_ATTR)['command']
    assert cmd_hook.doc == "<arg> - foo bar baz"
