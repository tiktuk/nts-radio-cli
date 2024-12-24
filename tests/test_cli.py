from click.testing import CliRunner
from nts.cli import format_time, get_nts_data, create_show_panel, json
import json as json_lib

def test_format_time():
    # Test UTC to local time conversion
    utc_timestamp = "2024-03-14T15:30:00Z"
    formatted_time = format_time(utc_timestamp)
    # Since the actual result depends on local timezone, we'll just verify the format
    assert len(formatted_time) == 5  # HH:MM format
    assert ":" in formatted_time
    assert formatted_time.count(":") == 1

def test_get_nts_data(mocker):
    # Mock the requests.get response
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "now": {
                    "broadcast_title": "Test Show",
                    "start_timestamp": "2024-03-14T15:00:00Z",
                    "end_timestamp": "2024-03-14T17:00:00Z"
                }
            }
        ]
    }
    mocker.patch('requests.get', return_value=mock_response)
    
    data = get_nts_data()
    assert data["results"][0]["now"]["broadcast_title"] == "Test Show"

def test_create_show_panel():
    # Test data
    show_data = {
        "broadcast_title": "Test Show",
        "start_timestamp": "2024-03-14T15:00:00Z",
        "end_timestamp": "2024-03-14T17:00:00Z",
        "embeds": {
            "details": {
                "description": "Test description",
                "genres": [{"value": "Electronic"}, {"value": "Ambient"}],
                "location_long": "London, UK"
            }
        }
    }
    
    channel_data = {
        "next1": {
            "broadcast_title": "Upcoming Show 1",
            "start_timestamp": "2024-03-14T17:00:00Z",
            "end_timestamp": "2024-03-14T19:00:00Z"
        }
    }
    
    show_panel, art_panel = create_show_panel(show_data, channel_data, 1, show_art=False)
    # Since rich panels are complex objects, we'll just verify it's created
    assert show_panel is not None
    assert art_panel is None

def test_json_command(mocker):
    # Mock the API response
    mock_response = mocker.Mock()
    test_data = {
        "results": [
            {
                "now": {
                    "broadcast_title": "Test Show",
                    "start_timestamp": "2024-03-14T15:00:00Z",
                    "end_timestamp": "2024-03-14T17:00:00Z"
                }
            }
        ]
    }
    mock_response.json.return_value = test_data
    mocker.patch('requests.get', return_value=mock_response)
    
    # Run the command
    runner = CliRunner()
    result = runner.invoke(json)
    
    # Verify the output is valid JSON and matches our test data
    assert result.exit_code == 0
    output_data = json_lib.loads(result.output)
    assert output_data == test_data
