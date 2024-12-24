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
from rich_pixels import Pixels
from PIL import Image


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


def get_nts_data():
    """Fetch current NTS broadcast data"""
    try:
        response = requests.get('https://www.nts.live/api/v2/live')
        return response.json()
    except requests.exceptions.ConnectionError:
        raise Exception("Unable to connect to NTS. Please check your internet connection and try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error connecting to NTS: {str(e)}")


def create_show_panel(show, channel_num, show_art=False, art_width=80, art_height=40):
    """Create a rich panel for the current show"""
    details = show.get('embeds', {}).get('details', {})

    # Create show info text
    show_info = Text()

    # Show title
    title = html.unescape(show['broadcast_title'])
    if "(R)" in title:
        show_info.append(f"{title}\n", style="bold")
    else:
        show_info.append(f"{title} {LIVE_INDICATOR}\n", style="bold")

    # Time
    time_str = f"{format_time(show['start_timestamp'])} - {format_time(show['end_timestamp'])}"
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

    show_panel = Panel(
        show_info, title=f"CHANNEL {channel_num}", border_style="blue", box=box.ROUNDED
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

    return show_panel, art_panel


def create_upcoming_table(channel):
    """Create a table of upcoming shows"""
    table = Table(box=box.SIMPLE)
    table.add_column("Time", style="yellow")
    table.add_column("Show", style="white")

    # Add next 5 shows
    for i in range(1, 6):
        next_show = channel.get(f'next{i}')
        if next_show:
            time_str = f"{format_time(next_show['start_timestamp'])} - {format_time(next_show['end_timestamp'])}"
            title = html.unescape(next_show['broadcast_title'])
            if "(R)" in title:
                table.add_row(time_str, Text(title))
            else:
                table.add_row(time_str, Text(f"{title} {LIVE_INDICATOR}"))

    return Panel(table, title="UPCOMING", border_style="blue", box=box.ROUNDED)


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

    try:
        with console.status("[bold blue]Fetching NTS data..."):
            data = get_nts_data()

        # Create main layout with two channels
        layout = Layout()
        layout.split_row(Layout(name="channel1"), Layout(name="channel2"))

        for idx, channel in enumerate(data['results']):
            # Create channel layout with optional art section
            sections = []
            show_panel, art_panel = create_show_panel(channel['now'], idx + 1, show_art=art, art_width=art_width, art_height=art_height)
            
            if art and art_panel:
                sections.append(Layout(art_panel, name="art"))
            sections.extend([
                Layout(show_panel, name="show_info"),
                Layout(create_upcoming_table(channel), name="upcoming")
            ])
            
            # Update channel with all sections
            channel_layout = Layout()
            channel_layout.split_column(*sections)
            layout[f"channel{idx + 1}"].update(channel_layout)

        console.print(layout)

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


@click.command()
def schedule():
    """Display full schedule for both channels"""
    console = Console()

    try:
        with console.status("[bold blue]Fetching NTS data..."):
            data = get_nts_data()

        for idx, channel in enumerate(data['results']):
            table = Table(title=f"Channel {idx + 1} Schedule", box=box.ROUNDED)
            table.add_column("Time", style="yellow")
            table.add_column("Show", style="white")
            table.add_column("Live", style="white")

            # Add current show
            current = channel['now']
            table.add_row(
                f"{format_time(current['start_timestamp'])} - {format_time(current['end_timestamp'])}",
                Text(
                    html.unescape(current['broadcast_title']),
                    style="bold blue"
                ), LIVE_INDICATOR if "(R)" not in current['broadcast_title'] else ""
            )

            # Add upcoming shows
            for i in range(1, 18):  # NTS usually provides next 17 shows
                next_show = channel.get(f'next{i}')
                if next_show:
                    title = html.unescape(next_show['broadcast_title'])
                    is_replay = "(R)" in title
                    show_type = LIVE_INDICATOR if not is_replay else ""
                    table.add_row(
                        f"{format_time(next_show['start_timestamp'])} - {format_time(next_show['end_timestamp'])}",
                        title, show_type
                    )

            console.print(table)
            console.print()  # Add spacing between channels

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


cli.add_command(now)
cli.add_command(schedule)

if __name__ == '__main__':
    cli()
