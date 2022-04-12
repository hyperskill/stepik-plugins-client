from __future__ import annotations

from base64 import b64decode
from typing import TYPE_CHECKING

import oslo_messaging as messaging
from oslo_config import cfg
from oslo_messaging.rpc.client import _client_opts

from stepik_plugins_client.schema import RPCSerializer  # noqa: I202

if TYPE_CHECKING:
    from typing import Any

messaging.set_transport_defaults(control_exchange='stepic.rpc')

ALLOWED_EXMODS = [
    'stepic_plugins.exceptions'
]


def set_default_response_timeout(timeout: int) -> None:
    """Set default timeout to wait for a response from a call.

    Given timeout is applied for all rpc calls.

    :param timeout: default timeout in seconds

    """
    cfg.CONF.register_opts(_client_opts)
    cfg.CONF.set_default('rpc_response_timeout', timeout)


class BaseAPI:
    """Base class for RPC API clients.

    It sets up the RPC client and binds it to the given topic.
    If required, it handles the starting of a fake RPC server.

    """

    topic: str
    namespace: str
    version: str

    #: A list of methods that are allowed to be called using service requests.
    service_request_methods: list[str] = []

    def __init__(self, transport_url: str) -> None:
        transport = messaging.get_transport(
            cfg.CONF,
            transport_url,
            allowed_remote_exmods=ALLOWED_EXMODS
        )

        target = messaging.Target(
            topic=self.topic,
            namespace=self.namespace,
            version=self.version
        )
        self.client = messaging.RPCClient(
            transport,
            target,
            serializer=RPCSerializer()
        )


class QuizAPI(BaseAPI):
    """Client side of the quizzes RPC API."""

    topic = 'plugins'
    namespace = 'quiz'
    version = '0.2'

    def ping(self, msg: str) -> str:
        return self.client.call({}, 'ping', msg=msg)

    def call(self, quiz_ctxt: dict[str, Any],
             name: str,
             args: list[Any] | None = None,
             kwargs: dict[str, Any] | None = None) -> str:
        """Invoke an arbitrary method or get an attribute of a quiz instance.

        :param name: an attribute or a method name
        :param args: positional arguments to pass on to the method (a list or tuple)
        :param kwargs: keyword arguments to pass on to the method (a dict)

        """
        return self.client.call(
            quiz_ctxt,
            'call',
            name=name,
            args=args,
            kwargs=kwargs
        )

    def validate_source(self, quiz_ctxt: dict[str, Any]) -> str:
        """Validate source from the quiz context.

        Returns None if the source is valid, otherwise raises FormatError

        :raises FormatError: if source is not valid

        """
        return self.client.call(quiz_ctxt, 'validate_source')

    def async_init(self, quiz_ctxt: dict[str, Any]) -> str:
        return self.client.call(quiz_ctxt, 'async_init')

    def generate(self,
                 quiz_ctxt: dict[str, Any]) -> tuple[dict[str, Any], Any] | None:
        return self.client.call(quiz_ctxt, 'generate')

    def clean_reply(self, quiz_ctxt: dict[str, Any],
                    reply: dict[str, Any],
                    dataset: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.client.call(
            quiz_ctxt,
            'clean_reply',
            reply=reply,
            dataset=dataset
        )

    def check(
        self, quiz_ctxt: dict[str, Any],
        reply: dict[str, Any],
        clue: dict[str, Any] | None = None
    ) -> tuple[float | bool, dict[str, Any] | str]:
        return self.client.call(quiz_ctxt, 'check', reply=reply, clue=clue)

    def cleanup(self, quiz_ctxt: dict[str, Any],
                clue: dict[str, Any] | None = None) -> str:
        return self.client.call(quiz_ctxt, 'cleanup', clue=clue)

    def list_computationally_hard_quizzes(self) -> str:
        return self.client.call({}, 'list_computationally_hard_quizzes')


class CodeJailAPI(BaseAPI):
    """Client side of the codejail RPC API."""

    topic = 'plugins'
    namespace = 'codejail'
    version = '0.2'

    def run_code(self, command: str, code: str | None = None,
                 files: list[str] | None = None,
                 argv: list[Any] | None = None,
                 stdin: str | None = None,
                 limits: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self.client.call(
            {},
            'run_code',
            command=command,
            code=code,
            files=files,
            argv=argv,
            stdin=stdin,
            limits=limits
        )
        result['stdout'] = b64decode(result['stdout'])
        result['stderr'] = b64decode(result['stderr'])

        return result


class UtilsAPI(BaseAPI):
    """Client side of the utils RPC API."""

    topic = 'plugins'
    namespace = 'utils'
    version = '0.1'

    service_request_methods = ['ping', 'preview_formula']

    def ping(self, msg: str) -> str:
        return self.client.call({}, 'ping', msg=msg)

    def preview_formula(self, formula: str) -> str:
        """Convert the given formula to LaTeX representation."""
        return self.client.call({}, 'preview_formula', formula=formula)
