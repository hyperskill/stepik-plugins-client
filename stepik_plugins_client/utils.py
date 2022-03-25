from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def truncate_data(value: Any, max_length: int = 100) -> Any:
    """Truncate a string or every nested string in a data structure."""
    if isinstance(value, (tuple, list)):
        return type(value)(
            [truncate_data(v, max_length=max_length) for v in value]
        )

    if isinstance(value, dict):
        return type(value)(
            (k, truncate_data(v, max_length=max_length))
            for k, v in value.items()
        )

    if isinstance(value, str):
        return (
            value if len(value) <= max_length
            else value[:max_length] + '...truncated...'
        )

    return value
