'''testing for extract module'''
from unittest import mock
from nbaetl.extract_data import (
    get_raw_gamelog,
    json_to_dataframe
)

from tests.fixtures.mock_response import (
    get_json_gamelog, get_json_gamerotation,
    MockResponse
)


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    """mocked request"""

    if "leaguegamelog" in args[0]:
        return MockResponse(get_json_gamelog(), 200)
    if "gamerotation" in args[0]:
        return MockResponse(get_json_gamerotation(), 200)

    return MockResponse(None, 404)


# test gamelog
@mock.patch('nbaetl.extract_data.requests.get', side_effect=mocked_requests_get)
def test_raw_gamelog(mock_get):
    """test for gamelog"""
    json_data = get_raw_gamelog()
    df_arr = json_to_dataframe(
        json_data
    )
    assert len(df_arr) == 1, 'Gamelog json must include only one dataframe'
    