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
    response = requests.get('https://www.nts.live/api/v2/live')
    return response.json()


def create_show_panel(show, channel_num, show_art=False):
    """Create a rich panel for the current show"""
    details = show.get('embeds', {}).get('details', {})

    # Create show info text
    show_info = Text()
    show_info.append(f"CHANNEL {channel_num}\n", style="bold white on black")

    # Show title
    title = html.unescape(show['broadcast_title'])
    if "(R)" in title:
        show_info.append(f"{title}\n", style="bold magenta")
    else:
        show_info.append(f"{title}\n", style="bold blue")

    # Time
    time_str = f"{format_time(show['start_timestamp'])} - {format_time(show['end_timestamp'])}\n"
    show_info.append(time_str, style="yellow")

    # Description
    if details.get('description'):
        show_info.append(f"\n{details['description']}\n", style="white")

    # Genres
    if details.get('genres'):
        show_info.append("\nGenres: ", style="bright_black")
        genres = [genre['value'] for genre in details['genres']]
        show_info.append(", ".join(genres), style="green")

    # Location
    if details.get('location_long'):
        show_info.append(
            f"\nLocation: {details['location_long']}", style="bright_black"
        )

    show_panel = Panel(
        show_info, title="NOW PLAYING", border_style="blue", box=box.ROUNDED
    )

    art_panel = None
    if show_art and details.get('media', {}).get('background_small'):
        try:
            # Get the url
            url = details['media']['background_small']

            r = requests.get(url, stream=True)
            aux_im = Image.open(io.BytesIO(r.content))

            # Create pixels from image with larger size to fill the frame better
            pixels = Pixels.from_image(aux_im, resize=(80, 40))
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
            style = "magenta" if "(R)" in title else "white"
            table.add_row(time_str, Text(title, style=style))

    return Panel(table, title="UPCOMING", border_style="blue", box=box.ROUNDED)


@click.command()
@click.option(
    '--art', is_flag=True, help='Show ASCII art for the current shows'
)
def now(art):
    """Display currently playing shows on NTS"""
    console = Console()

    try:
        with console.status("[bold blue]Fetching NTS data..."):
            data = get_nts_data()

        layout = Layout()
        layout.split_row(Layout(name="channel1"), Layout(name="channel2"))

        for idx, channel in enumerate(data['results']):
            channel_layout = Layout()
            if art:
                channel_layout.split_column(
                    Layout(name="art"),
                    Layout(name="show_info"),
                    Layout(name="upcoming")
                )
            else:
                channel_layout.split_column(
                    Layout(name="show_info"),
                    Layout(name="upcoming")
                )

            show_panel, art_panel = create_show_panel(channel['now'], idx + 1, show_art=art)
            if art:
                channel_layout["art"].update(art_panel if art_panel else Layout())
            channel_layout["show_info"].update(show_panel)
            channel_layout["upcoming"].update(create_upcoming_table(channel))

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
            table.add_column("Type", style="magenta")

            # Add current show
            current = channel['now']
            table.add_row(
                f"{format_time(current['start_timestamp'])} - {format_time(current['end_timestamp'])}",
                Text(
                    html.unescape(current['broadcast_title']),
                    style="bold blue"
                ), "LIVE"
            )

            # Add upcoming shows
            for i in range(1, 18):  # NTS usually provides next 17 shows
                next_show = channel.get(f'next{i}')
                if next_show:
                    title = html.unescape(next_show['broadcast_title'])
                    show_type = "REPLAY" if "(R)" in title else "LIVE"
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
