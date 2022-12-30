from __future__ import annotations

from functools import wraps
from typing import overload, TYPE_CHECKING

import structlog
from oslo_messaging import MessagingTimeout

from stepik_plugins_client import rpcapi  # noqa: I202
from stepik_plugins_client.constants import SECOND
from stepik_plugins_client.exceptions import PluginError

if TYPE_CHECKING:
    from typing import Any, Callable, Literal

logger = structlog.get_logger()

_RPC_API_CLIENTS: dict[str, rpcapi.BaseAPI] = {}


class PluginTimeout(PluginError):
    pass


class WrappedEndpointMetaclass(type):
    def __new__(cls, name: str,
                bases: tuple[type, ...], dct: dict[str, Any]) -> WrappedEndpointMetaclass:
        instance = super().__new__(cls, name, bases, dct)
        for name in dir(instance):
            method = getattr(instance, name)
            if not name.startswith('_') and callable(method):
                setattr(instance, name, cls.method_wrapper(method))
        return instance

    @staticmethod
    def method_wrapper(method: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(self: Any, *args, **kwargs) -> Any:
            try:
                return method(self, *args, **kwargs)
            except MessagingTimeout as exception:
                raise PluginTimeout(
                    'A timeout occurred while calling Problem API. '
                    'It looks like calculations take a long time.'
                ) from exception

        return wrapper


class ReportedQuizAPI(rpcapi.QuizAPI, metaclass=WrappedEndpointMetaclass):
    pass


class ReportedCodeJailAPI(rpcapi.CodeJailAPI,
                          metaclass=WrappedEndpointMetaclass):
    pass


class ReportedUtilsAPI(rpcapi.UtilsAPI, metaclass=WrappedEndpointMetaclass):
    pass


@overload
def _get_rpcapi_client(name: Literal['quiz'], transport_url: str,
                       timeout: int = 5 * 60) -> ReportedQuizAPI:
    ...


@overload
def _get_rpcapi_client(name: Literal['codejail'], transport_url: str,
                       timeout: int = 5 * 60) -> ReportedCodeJailAPI:
    ...


@overload
def _get_rpcapi_client(name: Literal['utils'], transport_url: str,
                       timeout: int = 5 * 60) -> ReportedUtilsAPI:
    ...


def _get_rpcapi_client(name, transport_url, timeout=5 * 60):
    api_class_map = {
        'quiz': ReportedQuizAPI,
        'codejail': ReportedCodeJailAPI,
        'utils': ReportedUtilsAPI,
    }
    rpc_api_class = api_class_map.get(name)
    if not rpc_api_class:
        raise ValueError('Incorrect RPC API client name')
    if name not in _RPC_API_CLIENTS:
        rpcapi.set_default_response_timeout(timeout)
        _RPC_API_CLIENTS[name] = rpc_api_class(
            transport_url
        )
    return _RPC_API_CLIENTS[name]


def quiz_rpcapi(transport_url: str,
                timeout: int = 5 * 60 * SECOND) -> ReportedQuizAPI:
    """Get client for the quizzes RPC API."""
    return _get_rpcapi_client(
        'quiz', transport_url, timeout
    )


def codejail_rpcapi(transport_url: str,
                    timeout: int = 5 * 60 * SECOND) -> ReportedCodeJailAPI:
    """Get client for the codejail RPC API."""
    return _get_rpcapi_client(
        'codejail', transport_url, timeout
    )


def utils_rpcapi(transport_url: str,
                 timeout: int = 5 * 60 * SECOND) -> ReportedUtilsAPI:
    """Get client for the utils RPC API."""
    return _get_rpcapi_client(
        'utils', transport_url, timeout
    )
