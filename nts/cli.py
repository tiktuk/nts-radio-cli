#!/usr/bin/env python3

import io
import click
import requests
import html
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.rule import Rule
from rich_pixels import Pixels
from PIL import Image
from rich.console import Group


LIVE_INDICATOR = "🔴"


@click.group()
def cli():
    """NTS Radio CLI - Check what's playing on NTS Radio"""
    pass


def format_time(timestamp):
    """Convert UTC timestamp to local time"""
    utc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    local_time = utc_time.astimezone()
    return local_time.strftime("%H:%M")


def format_time_range(start_timestamp, end_timestamp):
    """Format a time range from start and end timestamps"""
    return f"{format_time(start_timestamp)} - {format_time(end_timestamp)}"


def get_nts_data():
    """Fetch current NTS broadcast data"""
    try:
        response = requests.get('https://www.nts.live/api/v2/live')
        return response.json()
    except requests.exceptions.ConnectionError:
        raise Exception("Unable to connect to NTS. Please check your internet connection and try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error connecting to NTS: {str(e)}")


def format_show_title(title):
    """Format show title with live indicator if not a replay"""
    title = html.unescape(title)
    return title if "(R)" in title else f"{title} {LIVE_INDICATOR}"


def fetch_nts_data_with_status(console):
    """Fetch NTS data with status indicator"""
    with console.status("[bold blue]Fetching NTS data..."):
        return get_nts_data()


def handle_command_error(console, e):
    """Handle and display command errors"""
    console.print(f"[bold red]Error:[/] {str(e)}")


def create_show_panel(show, channel, channel_num, show_art=False, art_width=80, art_height=40):
    """Create a rich panel for the current show and upcoming shows"""
    details = show.get('embeds', {}).get('details', {})

    # Create show info text
    show_info = Text()

    # Show title
    show_info.append(f"{format_show_title(show['broadcast_title'])}\n", style="bold")

    # Time
    time_str = format_time_range(show['start_timestamp'], show['end_timestamp'])
    show_info.append(time_str, style="yellow")

    # Location
    if details.get('location_long'):
        show_info.append(
            f", {details['location_long']}"
        )

    # Description
    if details.get('description'):
        show_info.append(f"\n\n{details['description']}")

    # Genres
    if details.get('genres'):
        genres = ", ".join([genre['value'] for genre in details['genres']])
        show_info.append(f"\n\n{genres}", style="green")

    show_info.append("\n\n")

    # Create upcoming table
    upcoming_table = create_upcoming_table(channel)
    
    # Create single panel with all information
    panel = Panel(
        Group(
            show_info,
            Rule(title="UPCOMING SHOWS", style="blue"),
            upcoming_table
        ),
        title=f"CHANNEL {channel_num}",
        border_style="blue",
        box=box.ROUNDED
    )

    art_panel = None
    if show_art and details.get('media', {}).get('background_small'):
        try:
            # Get the url
            url = details['media']['background_small']

            r = requests.get(url, stream=True)
            aux_im = Image.open(io.BytesIO(r.content))

            # Create pixels from image using specified dimensions
            pixels = Pixels.from_image(aux_im, resize=(art_width, art_height))
            art_panel = Panel(pixels, title="SHOW ART", border_style="blue", box=box.ROUNDED)
        except Exception as e:
            art_panel = Panel(
                f"Error loading show art: {str(e)}", title="SHOW ART", border_style="red", box=box.ROUNDED
            )

    return panel, art_panel


def create_upcoming_table(channel):
    """Create a list of upcoming shows"""
    upcoming_text = Text("", style="bold")

    # Add next 5 shows
    for i in range(1, 6):
        next_show = channel.get(f'next{i}')
        if next_show:
            time_str = format_time_range(next_show['start_timestamp'], next_show['end_timestamp'])
            title = format_show_title(next_show['broadcast_title'])
            upcoming_text.append(f"\n{time_str} ", style="yellow")
            upcoming_text.append(title)

    return upcoming_text


@click.command()
@click.option(
    '--art', is_flag=True, help='Show ASCII art for the current shows'
)
@click.option(
    '--art-width', default=80, type=int, help='Width of the show art in characters (default: 80)'
)
@click.option(
    '--art-height', default=40, type=int, help='Height of the show art in characters (default: 40)'
)
def now(art, art_width, art_height):
    """Display currently playing shows on NTS"""
    console = Console()

    data = fetch_nts_data_with_status(console)

    # Create main layout with two channels side by side
    layout = Layout()
    layout.split_row(Layout(name="channel1"), Layout(name="channel2"))

    for idx, channel in enumerate(data['results']):
        show_panel, art_panel = create_show_panel(channel['now'], channel, idx + 1, show_art=art, art_width=art_width, art_height=art_height)
        
        # Create a vertical group for each channel
        channel_layout = Layout()
        panels = []
        if art and art_panel:
            panels.append(Layout(art_panel))
        panels.append(Layout(show_panel))
        
        channel_layout.split_column(*panels)
        layout[f"channel{idx + 1}"].update(channel_layout)

    console.print(layout)


@click.command()
def schedule():
    """Display full schedule for both channels"""
    console = Console()

    try:
        data = fetch_nts_data_with_status(console)

        for idx, channel in enumerate(data['results']):
            table = Table(title=f"Channel {idx + 1} Schedule", box=box.ROUNDED)
            table.add_column("Time", style="yellow")
            table.add_column("Show", style="white")

            # Add current show
            current = channel['now']
            title = format_show_title(current['broadcast_title'])
            table.add_row(
                format_time_range(current['start_timestamp'], current['end_timestamp']),
                Text(title, style="bold blue")
            )

            # Add upcoming shows
            for i in range(1, 18):  # NTS usually provides next 17 shows
                next_show = channel.get(f'next{i}')
                if next_show:
                    title = format_show_title(next_show['broadcast_title'])
                    table.add_row(
                        format_time_range(next_show['start_timestamp'], next_show['end_timestamp']),
                        title
                    )

            console.print(table)
            console.print()  # Add spacing between channels

    except Exception as e:
        handle_command_error(console, e)


@click.command()
def json():
    """Output raw JSON data from NTS API"""
    console = Console()
    try:
        data = fetch_nts_data_with_status(console)
        console.print_json(data=data)
    except Exception as e:
        handle_command_error(console, e)

cli.add_command(now)
cli.add_command(schedule)
cli.add_command(json)

if __name__ == '__main__':
    cli()
