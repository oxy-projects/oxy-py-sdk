from typing import Optional

from oxy.utils.lang._exception import IllegalArgumentException


def assert_true(condition: bool, message: Optional[str] = None):
    if not condition:
        fail(message)


def assert_false(condition: bool, message: Optional[str] = None):
    assert_true(not condition, message)


def fail(message: Optional[str]):
    if message:
        raise IllegalArgumentException(message)
    else:
        raise IllegalArgumentException()
