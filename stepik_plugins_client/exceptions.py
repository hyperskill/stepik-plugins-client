from __future__ import annotations

from typing import TYPE_CHECKING

from stepik_plugins_client.constants import USER_OUTPUT_MAX_LENGTH
from stepik_plugins_client.utils import truncate_data

if TYPE_CHECKING:
    from typing import Any


class PluginError(Exception):
    """The base class for all exceptions the plugins service can raise.

    Except an error message you can specify the code of the error and its
    context using optional `code` and `params` attributes.
    """

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        message = truncate_data(message, max_length=USER_OUTPUT_MAX_LENGTH)
        params = truncate_data(params, max_length=USER_OUTPUT_MAX_LENGTH)
        super().__init__(message, code, params)
        self.message = message or ""
        self.code = code or ""
        self.params = params or {}


class FormatError(PluginError):
    pass


class QuizSetUpError(PluginError):
    pass


class UnknownPluginError(PluginError):
    pass


class PluginTimeoutError(PluginError):
    """Exception for timeout exceeded."""
