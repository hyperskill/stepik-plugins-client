from __future__ import annotations

import base64
import datetime
import inspect
import time
from decimal import Decimal
from typing import TYPE_CHECKING

import oslo_messaging as messaging
from pytz import UTC

from stepik_plugins_client.exceptions import FormatError  # noqa: I202

if TYPE_CHECKING:
    from typing import Any


def is_int_as_string(obj: Any) -> bool:
    if isinstance(obj, str):
        try:
            int(obj)
        except ValueError:
            pass
        else:
            return True

    return False


def ensure_type(obj: Any, type_: type) -> None:
    # if integer passed as string (EDY-1668)
    if not isinstance(obj, type_) and not (type_ == int and is_int_as_string(obj)):
        raise FormatError(f'Expected {type_.__name__}, got {obj}')


def build(scheme: Any, obj: Any) -> Any:
    if inspect.isfunction(scheme):
        scheme = scheme()

    if _is_primitive(scheme):
        ensure_type(obj, scheme)
        # if integer passed as string (EDY-1668)
        if scheme == int and is_int_as_string(obj):
            return int(obj)
        return obj

    if isinstance(scheme, list):
        ensure_type(obj, list)
        return [build(scheme[0], x) for x in obj]

    assert isinstance(scheme, dict), 'Scheme should be dict'
    ensure_type(obj, dict)

    return ParsedJSON(scheme, obj)


class ParsedJSON:
    def __init__(self, scheme: dict[str, Any], obj: Any) -> None:
        self._original = obj
        for key, sub_scheme in scheme.items():
            if key not in obj:
                raise FormatError(f'Expected key {key} in {obj}')
            setattr(self, key, build(sub_scheme, obj[key]))

    def __repr__(self) -> str:
        return str(self._original)


def _is_primitive(obj: Any) -> bool:
    return obj in [str, bytes, int, float, bool]


class RPCSerializer(messaging.NoOpSerializer):
    def serialize_entity(self, ctxt: dict[str, Any], entity: Any) -> Any:
        if isinstance(entity, (tuple, list)):
            return [self.serialize_entity(ctxt, v) for v in entity]

        if isinstance(entity, dict):
            return {
                k: self.serialize_entity(ctxt, v)
                for k, v in entity.items()
            }

        if isinstance(entity, bytes):
            return {'_serialized.bytes': base64.b64encode(entity).decode()}

        if isinstance(entity, Decimal):
            return {'_serialized.decimal': str(entity)}

        if isinstance(entity, datetime.datetime):
            # doesn't preserve timezone
            return {'_serialized.datetime': entity.timestamp()}

        if isinstance(entity, datetime.date):
            return {'_serialized.date': int(time.mktime(entity.timetuple()))}

        if isinstance(entity, datetime.timedelta):
            return {'_serialized.timedelta': entity.total_seconds()}

        if isinstance(entity, ParsedJSON):
            return self.serialize_entity(ctxt, entity._original)

        return entity

    def deserialize_entity(self, ctxt: dict[str, Any], entity: Any) -> Any:
        if isinstance(entity, dict):
            if '_serialized.bytes' in entity:
                return base64.b64decode(entity['_serialized.bytes'])

            if '_serialized.decimal' in entity:
                return Decimal(entity['_serialized.decimal'])

            if '_serialized.datetime' in entity:
                return datetime.datetime.fromtimestamp(
                    entity['_serialized.datetime'],
                    tz=UTC
                )

            if '_serialized.date' in entity:
                return datetime.datetime.fromtimestamp(
                    entity['_serialized.date'],
                    tz=UTC
                ).date()

            if '_serialized.timedelta' in entity:
                return datetime.timedelta(
                    seconds=entity['_serialized.timedelta']
                )

            return {
                k: self.deserialize_entity(ctxt, v)
                for k, v in entity.items()
            }

        if isinstance(entity, list):
            return [self.deserialize_entity(ctxt, v) for v in entity]

        return entity
