from click.testing import CliRunner
import requests
import json as json_lib
from nts.cli import (
    format_time,
    format_time_range,
    get_nts_data,
    create_show_panel,
    json,
    info,
    stream_url,
    infinite,
)


def test_format_time_range():
    show = {
        "start_timestamp": "2024-03-14T15:00:00Z",
        "end_timestamp": "2024-03-14T17:00:00Z",
    }
    time_range = format_time_range(show)
    assert " - " in time_range
    assert len(time_range.split(" - ")) == 2
    # Each time should be in HH:MM format
    start_time, end_time = time_range.split(" - ")
    assert len(start_time) == 5 and ":" in start_time
    assert len(end_time) == 5 and ":" in end_time


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
                    "end_timestamp": "2024-03-14T17:00:00Z",
                }
            }
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)

    data, error = get_nts_data()
    assert data is not None
    assert error is None
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
                "location_long": "London, UK",
            }
        },
    }

    channel_data = {
        "next1": {
            "broadcast_title": "Upcoming Show 1",
            "start_timestamp": "2024-03-14T17:00:00Z",
            "end_timestamp": "2024-03-14T19:00:00Z",
        }
    }

    show_panel, art_panel = create_show_panel(
        show_data, channel_data, 1, show_art=False
    )
    # Since rich panels are complex objects, we'll just verify it's created
    assert show_panel is not None
    assert art_panel is None


def test_no_color_option():
    runner = CliRunner()
    result = runner.invoke(json, obj={"no_color": True})
    assert result.exit_code == 0


def test_json_command(mocker):
    # Mock the API response
    mock_response = mocker.Mock()
    test_data = {
        "results": [
            {
                "now": {
                    "broadcast_title": "Test Show",
                    "start_timestamp": "2024-03-14T15:00:00Z",
                    "end_timestamp": "2024-03-14T17:00:00Z",
                }
            }
        ]
    }
    mock_response.json.return_value = test_data
    mocker.patch("requests.get", return_value=mock_response)

    # Run the command
    runner = CliRunner()
    result = runner.invoke(json, obj={"no_color": False})
    # Verify the output is valid JSON and matches our test data
    assert result.exit_code == 0
    output_data = json_lib.loads(result.output)
    assert output_data == test_data


def test_info_command():
    runner = CliRunner()
    result = runner.invoke(info, obj={"no_color": False})
    assert result.exit_code == 0
    # Verify key information is present in the output
    assert "NTS RADIO INFO" in result.output
    assert "NTS is an online radio station" in result.output
    assert "stream-relay-geo.ntslive.net/stream" in result.output
    assert "stream-relay-geo.ntslive.net/stream2" in result.output
    assert "nts.live" in result.output


def test_stream_url_command():
    runner = CliRunner()

    # Test channel 1
    result = runner.invoke(stream_url, ["1"], obj={"no_color": False})
    assert result.exit_code == 0
    assert result.output.strip() == "https://stream-relay-geo.ntslive.net/stream"

    # Test channel 2
    result = runner.invoke(stream_url, ["2"], obj={"no_color": False})
    assert result.exit_code == 0
    assert result.output.strip() == "https://stream-relay-geo.ntslive.net/stream2"

    # Test invalid channel
    result = runner.invoke(stream_url, ["3"], obj={"no_color": False})
    assert result.exit_code != 0  # Should fail with invalid choice


def test_infinite_command(mocker):
    # Mock the API response
    mock_response = mocker.Mock()
    test_data = {
        "results": [
            {
                "title": "Test Mixtape",
                "description": "Test Description",
                "mixtape_alias": "test-mixtape",
                "audio_stream_endpoint": "https://test-stream-url"
            }
        ]
    }
    mock_response.json.return_value = test_data
    mocker.patch("requests.get", return_value=mock_response)

    # Test basic listing
    runner = CliRunner()
    result = runner.invoke(infinite, obj={"no_color": False})
    assert result.exit_code == 0
    assert "Test Mixtape" in result.output
    assert "Test Description" in result.output
    assert "test-mixtape" in result.output

    # Test URL display in simplified table
    result = runner.invoke(infinite, ["--url"], obj={"no_color": False})
    assert result.exit_code == 0
    assert "Test Mixtape" in result.output
    assert "Test Description" not in result.output  # Description should be omitted
    assert "test-mixtape" in result.output
    assert "https://test-stream-url" in result.output
    assert "Stream URL" in result.output  # Check for column header

    # Test play functionality (mock subprocess.run)
    mock_run = mocker.patch("subprocess.run")
    result = runner.invoke(infinite, ["--play", "test-mixtape"], obj={"no_color": False})
    assert result.exit_code == 0
    mock_run.assert_called_once_with(
        ["mpv", "https://test-stream-url"],
        check=True
    )


def test_infinite_command_errors(mocker):
    # Test network error
    mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError)
    runner = CliRunner()
    result = runner.invoke(infinite, obj={"no_color": False})
    assert result.exit_code == 0  # Command handles error gracefully
    assert "Network error" in result.output

    # Test invalid data format
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"invalid": "data"}
    mocker.patch("requests.get", return_value=mock_response)
    result = runner.invoke(infinite, obj={"no_color": False})
    assert result.exit_code == 0  # Command handles error gracefully
    assert "Invalid data format" in result.output

    # Test invalid mixtape name
    mock_response.json.return_value = {"results": []}
    mocker.patch("requests.get", return_value=mock_response)
    result = runner.invoke(infinite, ["--play", "nonexistent"], obj={"no_color": False})
    assert result.exit_code == 0  # Command handles error gracefully
    assert "not found" in result.output
