from collections import Mapping, Iterable
from inspect import isclass
from toolz.curried import *
import pytest


class SchemaError(Exception):
    pass


class Required(object):
    def __call__(self, value):
        return value


required = Required()


class default(object):
    def __init__(self, value):
        self.value = value


def is_required(schema):
    return (
        required is schema or
        isinstance(schema, Iterable) and required in schema
    )


@curry
def validate_dict_schema(schema, data):
    result_data = {}
    for key_schema, value_schema in schema.items():
        key_found = False
        for key, value in data.items():
            key, value = (
                validate_schema(key_schema, key),
                validate_schema(value_schema, value)
            )
            del data[key]
            result_data[key] = value
            key_found = True

        if is_required(key_schema) and not key_found:
            raise SchemaError()


@curry
def validate_schema(schema, data):
    if isinstance(schema, tuple):
        if not compose(*schema[1:])(data):
            raise SchemaError()
        return validate_schema(schema[0], data)
    elif isinstance(schema, dict):
        if not isinstance(data, dict):
            raise SchemaError()

        return validate_dict_schema(schema, data)
    elif isinstance(schema, list):
        if not isinstance(data, list):
            raise SchemaError()

        return list(map(validate_schema(schema[0]), data))
    else:
        if isclass(schema):
            if not isinstance(data, schema):
                raise SchemaError()
        return data


@pytest.mark.parametrize(('schema', 'data'), [
    ([int], [3, 4, 5]),
    (list, []),
    ([list], [[], [], []]),
    (int, 3),
    ({object: object}, {3: 3})
])
def test_valid_schema_data(schema, data):
    assert data == validate_schema(schema, data)


@pytest.mark.parametrize(('schema', 'data'), [
    ([int], ['str']),
    (list, 'str'),
    (dict, 'str'),
    ({str: int}, {3: 3}),
    ({(str, required): 3}, {3: 3}),
    ({(str, required): (int, default(3))}, {}),
    ((list, len), []),
])
def test_invalid_schema_data(schema, data):
    with pytest.raises(SchemaError):
        validate_schema(schema, data)
