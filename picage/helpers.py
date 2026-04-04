# -*- coding: utf-8 -*-

"""
Utility functions.
"""

import sys
import string


def get_sp_dir() -> str:  # pragma: no cover
    """
    Return the absolute path of the ``site-packages`` directory.

    Scans :data:`sys.path` in reverse order and returns the first entry
    that ends with ``"site-packages"``.

    :raises Exception: If no ``site-packages`` directory is found in
        :data:`sys.path`.
    """
    for p in sys.path[::-1]:
        if p.endswith("site-packages"):
            return p
    raise Exception("'site-package' directory not found!")


SP_DIR: str = get_sp_dir()
"""Absolute path of the current interpreter's ``site-packages`` directory."""

_first_letter_for_valid_name: set[str] = set(string.ascii_lowercase + "_")
_char_set_for_valid_name: set[str] = set(string.ascii_letters + string.digits + "_-")


def is_valid_package_module_name(
    name: str,
) -> bool:
    """
    Return ``True`` if *name* is a valid Python package or module name.

    Rules applied to each dot-separated component:

    - Must be non-empty.
    - First character must be a lowercase ASCII letter or ``_``.
    - Remaining characters may be ASCII letters, digits, ``_``, or ``-``.

    Examples of **valid** names:

    - ``a``
    - ``a.b.c``
    - ``_a``
    - ``_a._b._c``

    Examples of **invalid** names:

    - ``A``   (uppercase first letter)
    - ``0``   (digit as first character)
    - ``.a``  (leading dot produces an empty component)
    - ``a#b`` (illegal character ``#``)
    """
    if "." in name:
        return all(is_valid_package_module_name(part) for part in name.split("."))
    if not name:
        return False
    if name[0] not in _first_letter_for_valid_name:
        return False
    return not set(name).difference(_char_set_for_valid_name)


def assert_is_valid_name(
    name: str,
    error: Exception | None = None,
) -> None:
    """
    Raise an error if *name* is not a valid package or module name.

    :param name: The name to validate.
    :param error: Exception instance to raise on failure.  Defaults to a
        :exc:`ValueError` whose message includes *name*.
    :raises ValueError: (or the provided *error*) when *name* is invalid.
    """
    if error is None:
        error = ValueError("%r is not a valid package or module name!" % name)
    if not is_valid_package_module_name(name):
        raise error
