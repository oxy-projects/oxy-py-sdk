from oxy.utils.http import make_response_processors, origin_response


def test_make_response_processors_ignores():
    processors = make_response_processors(ignores=['parser'])
    assert set(processors) == {'success', 'error_msg'}
    assert set(make_response_processors(ignores='parser')) == {'success', 'error_msg'}
    assert set(origin_response()) == {'success', 'error_msg', 'parser'}
