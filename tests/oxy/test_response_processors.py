from oxy.utils.http import make_response_processors, origin_response
from oxy.utils.http._api import _to_model
from pydantic import BaseModel, RootModel, TypeAdapter, ValidationError
import pytest


class Item(BaseModel):
    value: int


@pytest.mark.parametrize('data', [[{'value': '42'}], '[{"value": "42"}]'])
def test_response_model_list(data):
    assert _to_model(data, RootModel[list[Item]]) == [Item(value=42)]


@pytest.mark.parametrize('data', [[], '[]'])
def test_response_model_empty_list(data):
    assert _to_model(data, RootModel[list[Item]]) == []


@pytest.mark.parametrize('data', [[{'value': 'invalid'}], '[{"value": "invalid"}]'])
def test_response_model_list_validation(data):
    with pytest.raises(ValidationError):
        _to_model(data, RootModel[list[Item]])


@pytest.mark.parametrize('data', [{'value': '42'}, '{"value": "42"}'])
def test_response_model_existing_inputs(data):
    assert _to_model(data, Item) == Item(value=42)


@pytest.mark.parametrize('data', [[{'value': '42'}], '[{"value": "42"}]'])
def test_response_type_adapter_list(data):
    assert _to_model(data, TypeAdapter(list[Item])) == [Item(value=42)]


def test_response_type_adapter_validation():
    assert _to_model({'value': '42'}, TypeAdapter(Item)) == Item(value=42)
    assert _to_model([], TypeAdapter(list[Item])) == []
    assert _to_model(42, TypeAdapter(int)) == 42
    assert _to_model(None, TypeAdapter(int | None)) is None
    with pytest.raises(ValidationError):
        _to_model([{'value': 'invalid'}], TypeAdapter(list[Item]))
    with pytest.raises(ValidationError):
        _to_model('invalid json', TypeAdapter(list[Item]))


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
