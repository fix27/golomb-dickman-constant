#!/usr/bin/env python3
"""Restricted pickle reader for checkpoint files.

Checkpoints are plain data: a 4-tuple of integers and integer pairs.  A
normal ``pickle.load`` can execute arbitrary code, so this module accepts a
pickle stream only if

  * every opcode belongs to a small allow-list (no GLOBAL, STACK_GLOBAL,
    REDUCE, BUILD, NEWOBJ, INST, OBJ, EXT1/2/4, PERSID, BINPERSID, ...);
  * no persistent IDs and no extension codes appear;
  * the result is built from ``None``, ``bool``, ``int``, ``tuple`` and
    ``list`` only, recursively.

The structural validation of the checkpoint (field types, ranges, index
coverage) is still the caller's job; this module only refuses code
execution and unexpected object graphs.

Usage
-----
    from safe_pickle import load_restricted, UnsafePickleError
    value = load_restricted(path)
"""

from __future__ import annotations

import io
import pickle
import pickletools
from pathlib import Path
from typing import Any

__all__ = [
    "UnsafePickleError",
    "ALLOWED_OPCODES",
    "loads_restricted",
    "load_restricted",
    "validate_plain_data",
]


class UnsafePickleError(pickle.UnpicklingError):
    """Raised when a pickle stream contains forbidden opcodes or objects."""


# Opcodes needed to encode nested tuples/lists of integers.  Everything that
# can name a global, call a callable, rebuild an object or reference the
# extension registry is deliberately absent.
ALLOWED_OPCODES = frozenset(
    {
        "PROTO",
        "FRAME",
        "STOP",
        "MARK",
        "EMPTY_TUPLE",
        "TUPLE",
        "TUPLE1",
        "TUPLE2",
        "TUPLE3",
        "EMPTY_LIST",
        "LIST",
        "APPEND",
        "APPENDS",
        "EMPTY_DICT",
        "DICT",
        "SETITEM",
        "SETITEMS",
        "NONE",
        "NEWTRUE",
        "NEWFALSE",
        "BININT",
        "BININT1",
        "BININT2",
        "LONG",
        "LONG1",
        "LONG4",
        "MEMOIZE",
        "BINPUT",
        "LONG_BINPUT",
        "BINGET",
        "LONG_BINGET",
        "PUT",
        "GET",
    }
)

_MAX_DEPTH = 32
_MAX_ITEMS = 10_000_000


def _check_opcodes(data: bytes) -> None:
    try:
        for opcode, _arg, _pos in pickletools.genops(data):
            if opcode.name not in ALLOWED_OPCODES:
                raise UnsafePickleError(
                    f"forbidden pickle opcode {opcode.name}"
                )
    except UnsafePickleError:
        raise
    except Exception as exc:  # truncated or malformed stream
        raise UnsafePickleError(f"cannot parse pickle stream: {exc}") from exc


class _RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> Any:  # noqa: D401
        raise UnsafePickleError(f"forbidden global {module}.{name}")

    def persistent_load(self, pid: Any) -> Any:
        raise UnsafePickleError("persistent IDs are forbidden")


def validate_plain_data(value: Any, *, _depth: int = 0) -> Any:
    """Accept only None/bool/int/tuple/list, with bounded nesting."""
    if _depth > _MAX_DEPTH:
        raise UnsafePickleError("object nesting is too deep")
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, (tuple, list)):
        if len(value) > _MAX_ITEMS:
            raise UnsafePickleError("container is too large")
        for item in value:
            validate_plain_data(item, _depth=_depth + 1)
        return value
    raise UnsafePickleError(f"forbidden object type {type(value).__name__}")


def loads_restricted(data: bytes) -> Any:
    """Decode ``data`` if, and only if, it is a plain-data pickle."""
    _check_opcodes(data)
    value = _RestrictedUnpickler(io.BytesIO(data)).load()
    return validate_plain_data(value)


def load_restricted(path: str | Path) -> Any:
    """Read and decode a checkpoint file without executing pickle code."""
    return loads_restricted(Path(path).read_bytes())
