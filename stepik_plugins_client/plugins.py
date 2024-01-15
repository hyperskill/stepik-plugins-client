from __future__ import annotations

from functools import wraps
from typing import overload, TYPE_CHECKING

import structlog
from oslo_messaging import MessagingTimeout

from stepik_plugins_client import rpcapi
from stepik_plugins_client.constants import SECOND
from stepik_plugins_client.exceptions import PluginTimeoutError

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Literal

logger = structlog.get_logger()

_RPC_API_CLIENTS: dict[tuple[str, str, str], rpcapi.BaseAPI] = {}


class WrappedEndpointMetaclass(type):
    def __new__(
        cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]
    ) -> WrappedEndpointMetaclass:
        """Create API class."""
        instance = super().__new__(cls, name, bases, dct)
        for _name in dir(instance):
            method = getattr(instance, _name)
            if not _name.startswith("_") and callable(method):
                setattr(instance, _name, cls.method_wrapper(method))
        return instance

    @staticmethod
    def method_wrapper(method: Callable[..., Any]) -> Callable[..., Any]:
        """Raise PluginTimeout when raised MessagingTimeout."""

        @wraps(method)
        def wrapper(self: Any, *args, **kwargs) -> Any:
            try:
                return method(self, *args, **kwargs)
            except MessagingTimeout as exception:
                msg = (
                    "A timeout occurred while calling Problem API. "
                    "It looks like calculations take a long time."
                )
                raise PluginTimeoutError(msg) from exception

        return wrapper


class ReportedQuizAPI(rpcapi.QuizAPI, metaclass=WrappedEndpointMetaclass):
    pass


class ReportedUtilsAPI(rpcapi.UtilsAPI, metaclass=WrappedEndpointMetaclass):
    pass


@overload
def _get_rpcapi_client(
    name: Literal["quiz"], transport_url: str, topic: str | None = None, timeout: int = 5 * 60
) -> ReportedQuizAPI:
    ...


@overload
def _get_rpcapi_client(
    name: Literal["utils"], transport_url: str, topic: str | None = None, timeout: int = 5 * 60
) -> ReportedUtilsAPI:
    ...


def _get_rpcapi_client(name, transport_url, topic=None, timeout=5 * 60):
    api_class_map = {
        "quiz": ReportedQuizAPI,
        "utils": ReportedUtilsAPI,
    }
    rpc_api_class = api_class_map.get(name)
    if not rpc_api_class:
        msg = "Incorrect RPC API client name"
        raise ValueError(msg)
    key = (name, transport_url, topic)
    if name not in _RPC_API_CLIENTS:
        rpcapi.set_default_response_timeout(timeout)
        _RPC_API_CLIENTS[key] = rpc_api_class(transport_url, topic)
    return _RPC_API_CLIENTS[key]


def quiz_rpcapi(
    transport_url: str, topic: str | None = None, timeout: int = 5 * 60 * SECOND
) -> ReportedQuizAPI:
    """Get client for the quizzes RPC API."""
    return _get_rpcapi_client("quiz", transport_url, topic, timeout)


def utils_rpcapi(
    transport_url: str, topic: str | None = None, timeout: int = 5 * 60 * SECOND
) -> ReportedUtilsAPI:
    """Get client for the utils RPC API."""
    return _get_rpcapi_client("utils", transport_url, topic, timeout)
