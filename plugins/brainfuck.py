"""brainfuck interpreter adapted from (public domain) code at
http://brainfuck.sourceforge.net/brain.py"""

import random
import re

from cloudbot import hook

BUFFER_SIZE = 5000
MAX_STEPS = 1000000


@hook.command("brainfuck", "bf")
async def bf(text):
    """<prog> - executes <prog> as Brainfuck code

    :type text: str
    """

    program = re.sub('[^][<>+-.,]', '', text)

    # create a dict of brackets pairs, for speed later on
    brackets = {}
    open_brackets = []
    for pos, c in enumerate(program):
        if c == '[':
            open_brackets.append(pos)
        elif c == ']':
            if not open_brackets:
                return "Unbalanced brackets"

            brackets[pos] = open_brackets[-1]
            brackets[open_brackets[-1]] = pos
            open_brackets.pop()

    if open_brackets:
        return "Unbalanced brackets"

    # now we can start interpreting
    ip = 0  # instruction pointer
    mp = 0  # memory pointer
    steps = 0
    memory = [0] * BUFFER_SIZE  # initial memory area
    rightmost = 0
    output = ""  # we'll save the output here

    # the main program loop:
    while ip < len(program):
        c = program[ip]
        if c == '+':
            memory[mp] = (memory[mp] + 1) % 256
        elif c == '-':
            memory[mp] = (memory[mp] - 1) % 256
        elif c == '>':
            mp += 1
            if mp > rightmost:
                rightmost = mp
                if mp >= len(memory):
                    # no restriction on memory growth!
                    memory.extend([0] * BUFFER_SIZE)
        elif c == '<':
            mp -= 1 % len(memory)
        elif c == '.':
            output += chr(memory[mp])
            if len(output) > 500:
                break
        elif c == ',':
            memory[mp] = random.randint(1, 255)
        elif c == '[':
            if memory[mp] == 0:
                ip = brackets[ip]
        elif c == ']':
            if memory[mp] != 0:
                ip = brackets[ip]

        ip += 1
        steps += 1
        if steps > MAX_STEPS:
            if not output:
                output = "(no output)"
            output += "(exceeded {} iterations)".format(MAX_STEPS)
            break

    stripped_output = re.sub(r'[\x00-\x1F]', '', output)

    if not stripped_output:
        if output:
            return "No printable output"
        return "No output"

    return stripped_output[:430]
