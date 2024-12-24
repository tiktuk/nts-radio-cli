from nts.cli import format_time, get_nts_data, create_show_panel, create_upcoming_table

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
    
    show_panel, art_panel = create_show_panel(show_data, 1, show_art=False)
    # Since rich panels are complex objects, we'll just verify it's created
    assert show_panel is not None
    assert art_panel is None

def test_create_upcoming_table():
    # Test data
    channel_data = {
        "next1": {
            "broadcast_title": "Upcoming Show 1",
            "start_timestamp": "2024-03-14T17:00:00Z",
            "end_timestamp": "2024-03-14T19:00:00Z"
        },
        "next2": {
            "broadcast_title": "Upcoming Show 2 (R)",
            "start_timestamp": "2024-03-14T19:00:00Z",
            "end_timestamp": "2024-03-14T21:00:00Z"
        }
    }
    
    table = create_upcoming_table(channel_data)
    # Verify table is created
    assert table is not None
