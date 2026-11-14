from oxy.utils.http import make_response_processors, origin_response
from oxy.utils.http._api import _to_model
from pydantic import BaseModel, RootModel, ValidationError
import pytest


class Item(BaseModel):
    value: int


def test_response_model_list():
    result = _to_model([{'value': '42'}], RootModel[list[Item]])
    assert result.root == [Item(value=42)]
    assert _to_model([], RootModel[list[Item]]).root == []
    with pytest.raises(ValidationError):
        _to_model([{'value': 'invalid'}], RootModel[list[Item]])


@pytest.mark.parametrize('data', [{'value': '42'}, '{"value": "42"}'])
def test_response_model_existing_inputs(data):
    assert _to_model(data, Item) == Item(value=42)


def test_response_model_passthrough_and_unsupported_type():
    data = [{'value': '42'}]
    assert _to_model(data, None) is data
    with pytest.raises(TypeError, match='int'):
        _to_model(42, Item)


def test_make_response_processors_ignores():
    processors = make_response_processors(ignores=['parser'])
    assert set(processors) == {'success', 'error_msg'}
    assert set(make_response_processors(ignores='parser')) == {'success', 'error_msg'}
    assert set(origin_response()) == {'success', 'error_msg', 'parser'}
