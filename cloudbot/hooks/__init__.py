from enum import unique, IntEnum, Enum


@unique
class Priority(IntEnum):
    # Reversed to maintain compatibility with sieve hooks numeric priority
    LOWEST = 127
    LOW = 63
    NORMAL = 0
    HIGH = -64
    HIGHEST = -128


@unique
class Action(Enum):
    """Defines the action to take after executing a hook"""
    HALTTYPE = 0  # Once this hook executes, no other hook of that type should run
    HALTALL = 1  # Once this hook executes, No other hook should run
    CONTINUE = 2  # Normal execution of all hooks
