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
STREAM_URLS = {
    "1": "https://stream-relay-geo.ntslive.net/stream",
    "2": "https://stream-relay-geo.ntslive.net/stream2",
}


@click.group()
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx, no_color):
    """NTS Radio CLI - Check what's playing on NTS Radio"""
    ctx.ensure_object(dict)
    ctx.obj["no_color"] = no_color


def format_time(timestamp):
    """Convert UTC timestamp to local time"""
    utc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    local_time = utc_time.astimezone()
    return local_time.strftime("%H:%M")


def format_time_range(show):
    """Format a time range from a show object"""
    return (
        f"{format_time(show['start_timestamp'])} - {format_time(show['end_timestamp'])}"
    )


def get_nts_data():
    """Fetch current NTS broadcast data"""
    try:
        response = requests.get("https://www.nts.live/api/v2/live")
        return response.json()
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Unable to connect to NTS. Please check your internet connection and try again."
        )
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


def create_show_panel(
    show, channel, channel_num, show_art=False, art_width=80, art_height=40
):
    """Create a rich panel for the current show and upcoming shows"""
    details = show.get("embeds", {}).get("details", {})

    # Create show info text
    show_info = Text()

    # Show title
    show_info.append(f"{format_show_title(show['broadcast_title'])}\n", style="bold")

    # Time
    time_str = format_time_range(show)
    show_info.append(time_str, style="yellow")

    # Location
    if details.get("location_long"):
        show_info.append(f", {details['location_long']}")

    # Description
    if details.get("description"):
        show_info.append(f"\n\n{details['description']}")

    # Genres
    if details.get("genres"):
        genres = ", ".join([genre["value"] for genre in details["genres"]])
        show_info.append(f"\n\n{genres}", style="green")

    show_info.append("\n\n")

    # Create upcoming table
    upcoming_table = create_upcoming_table(channel)

    # Create single panel with all information
    panel = Panel(
        Group(show_info, Rule(title="UPCOMING SHOWS", style="blue"), upcoming_table),
        title=f"CHANNEL {channel_num}",
        border_style="blue",
        box=box.ROUNDED,
    )

    art_panel = None
    if show_art and details.get("media", {}).get("background_small"):
        try:
            # Get the url
            url = details["media"]["background_small"]

            r = requests.get(url, stream=True)
            aux_im = Image.open(io.BytesIO(r.content))

            # Create pixels from image using specified dimensions
            pixels = Pixels.from_image(aux_im, resize=(art_width, art_height))
            art_panel = Panel(
                pixels, title="SHOW ART", border_style="blue", box=box.ROUNDED
            )
        except Exception as e:
            art_panel = Panel(
                f"Error loading show art: {str(e)}",
                title="SHOW ART",
                border_style="red",
                box=box.ROUNDED,
            )

    return panel, art_panel


def create_upcoming_table(channel):
    """Create a list of upcoming shows"""
    upcoming_text = Text("", style="bold")

    # Add next 5 shows
    for i in range(1, 6):
        next_show = channel.get(f"next{i}")
        if next_show:
            time_str = format_time_range(next_show)
            title = format_show_title(next_show["broadcast_title"])
            upcoming_text.append(f"\n{time_str} ", style="yellow")
            upcoming_text.append(title)

    return upcoming_text


@click.command()
@click.option("--art", is_flag=True, help="Show ASCII art for the current shows")
@click.option(
    "--art-width",
    default=80,
    type=int,
    help="Width of the show art in characters (default: 80)",
)
@click.option(
    "--art-height",
    default=40,
    type=int,
    help="Height of the show art in characters (default: 40)",
)
@click.pass_context
def now(ctx, art, art_width, art_height):
    """Display currently playing shows on NTS"""
    console = Console(no_color=ctx.obj["no_color"])

    data = fetch_nts_data_with_status(console)

    # Create main layout with two channels side by side
    layout = Layout()
    layout.split_row(Layout(name="channel1"), Layout(name="channel2"))

    for idx, channel in enumerate(data["results"]):
        show_panel, art_panel = create_show_panel(
            channel["now"],
            channel,
            idx + 1,
            show_art=art,
            art_width=art_width,
            art_height=art_height,
        )

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
@click.pass_context
def schedule(ctx):
    """Display full schedule for both channels"""
    console = Console(no_color=ctx.obj["no_color"])

    try:
        data = fetch_nts_data_with_status(console)

        for idx, channel in enumerate(data["results"]):
            table = Table(title=f"Channel {idx + 1} Schedule", box=box.ROUNDED)
            table.add_column("Time", style="yellow")
            table.add_column("Show", style="white")

            # Add current show
            current = channel["now"]
            title = format_show_title(current["broadcast_title"])
            table.add_row(format_time_range(current), Text(title, style="bold blue"))

            # Add upcoming shows
            for i in range(1, 18):  # NTS usually provides next 17 shows
                next_show = channel.get(f"next{i}")
                if next_show:
                    title = format_show_title(next_show["broadcast_title"])
                    table.add_row(format_time_range(next_show), title)

            console.print(table)
            console.print()  # Add spacing between channels

    except Exception as e:
        handle_command_error(console, e)


@click.command()
@click.pass_context
def json(ctx):
    """Output raw JSON data from NTS API"""
    console = Console(no_color=ctx.obj["no_color"])
    try:
        data = fetch_nts_data_with_status(console)
        console.print_json(data=data)
    except Exception as e:
        handle_command_error(console, e)


@click.command()
@click.pass_context
def info(ctx):
    """Display information about NTS Radio and stream URLs"""
    console = Console(no_color=ctx.obj["no_color"])

    # Create info panel
    info_text = Text()
    info_text.append(
        "NTS is an online radio station based in London with studios in London, Manchester and Los Angeles. This application, `nts-radio-cli` is an unofficial supporter-effort to get NTS in the terminal :) .\n\n"
    )

    # Stream information
    info_text.append("Stream URLs:\n", style="bold yellow")
    info_text.append("Channel 1: ", style="bold")
    info_text.append(f"{STREAM_URLS['1']}\n")
    info_text.append("Channel 2: ", style="bold")
    info_text.append(f"{STREAM_URLS['2']}\n\n")

    # Additional useful info
    info_text.append("Useful Links:\n", style="bold yellow")
    info_text.append("Website: ", style="bold")
    info_text.append("https://www.nts.live\n")
    info_text.append("Shows Archive: ", style="bold")
    info_text.append("https://www.nts.live/shows\n")
    info_text.append("Infinite Mixtapes: ", style="bold")
    info_text.append("https://www.nts.live/infinite-mixtapes\n")
    info_text.append("Broadcast Locations: ", style="bold")
    info_text.append("https://www.nts.live/explore/location\n")
    info_text.append("Become a Supporter: ", style="bold")
    info_text.append("https://www.nts.live/supporters\n\n")

    info_text.append("Source code:\n", style="bold yellow")
    info_text.append("https://github.com/tiktuk/nts-radio-cli")

    panel = Panel(
        info_text,
        title="NTS RADIO INFO",
        border_style="blue",
        box=box.ROUNDED,
    )

    console.print(panel)


@click.command()
@click.argument("channel", type=click.Choice(["1", "2"]))
@click.pass_context
def stream_url(ctx, channel):
    """Output stream URL for the specified channel (1 or 2)"""
    print(STREAM_URLS[channel])


cli.add_command(now)
cli.add_command(schedule)
cli.add_command(json)
cli.add_command(info)
cli.add_command(stream_url)

if __name__ == "__main__":
    cli()
