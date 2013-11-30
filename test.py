from collections import Mapping, Iterable
from inspect import isclass
import pytest


class SchemaError(Exception):
    pass



def compose(*functions):
    def inner(arg):
        for f in reversed(functions):
            arg = f(arg)
        return arg
    return inner


class Required(object):
    def __call__(self, value):
        return value


required = Required()


class default(object):
    def __init__(self, value):
        self.value = value


def validate_subschema(schema, data):
    for subschema in schema:
        try:
            return validate_schema(subschema, data)
        except SchemaError:
            pass
    raise SchemaError()


def validate_schema(schema, data):
    if isinstance(schema, tuple):
        if not all(map(lambda func: func(data), schema[1:])):
            raise SchemaError()
        return composed_validator(validate_schema(schema[0], data))
    elif isinstance(schema, dict):
        if not isinstance(data, dict):
            raise SchemaError()

        return dict(
            map(
                lambda a: (
                    validate_subschema(schema, a[0]),
                    validate_subschema(schema.values(), a[1])
                ),
                data.items()
            )
        )
    elif isinstance(schema, list):
        if not isinstance(data, list):
            raise SchemaError()

        return map(lambda a: validate_schema(schema[0], a), data)
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
    ({str: (int, default(3))}, {}),
    ((list, len), []),
])
def test_invalid_schema_data(schema, data):
    with pytest.raises(SchemaError):
        validate_schema(schema, data)
