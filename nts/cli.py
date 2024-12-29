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


def get_mixtapes_data():
    """Fetch NTS infinite mixtapes data"""
    try:
        response = requests.get("https://www.nts.live/api/v2/mixtapes")
        return response.json(), None
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ):
        return None, "Network error: Could not connect to the NTS API"


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
        return response.json(), None
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ):
        return None, "Network error: Could not connect to the NTS API"
    # Let other exceptions propagate normally


def format_show_title(title):
    """Format show title with live indicator if not a replay"""
    title = html.unescape(title)
    return title if "(R)" in title else f"{title} {LIVE_INDICATOR}"


def fetch_nts_data_with_status(console):
    """Fetch NTS data with status indicator"""
    with console.status("[bold blue]Fetching NTS data..."):
        try:
            data, error = get_nts_data()
            if error:
                console.print(f"[bold red]Error:[/] {error}")
                return None
            return data
        except Exception:
            # Let non-network errors propagate with traceback
            raise


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
    if not data:
        return

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

    data = fetch_nts_data_with_status(console)
    if not data:
        return

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


@click.command()
@click.pass_context
def json(ctx):
    """Output raw JSON data from NTS API"""
    console = Console(no_color=ctx.obj["no_color"])
    data = fetch_nts_data_with_status(console)
    if data:
        console.print_json(data=data)


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


@click.command()
@click.argument("channel", type=click.Choice(["1", "2"]))
@click.option("--player", help="Path to media player executable (default: mpv)")
@click.pass_context
def play(ctx, channel, player):
    """Play the NTS radio stream for the specified channel (1 or 2)"""
    import subprocess
    import sys

    stream_url = STREAM_URLS[channel]
    player_cmd = player if player else "mpv"

    try:
        subprocess.run(
            [player_cmd, stream_url],
            check=True,
        )
    except FileNotFoundError:
        print(
            f"Error: {player_cmd} not found. Please ensure the media player is installed.",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error playing stream: {e}", file=sys.stderr)
        sys.exit(1)


cli.add_command(now)
cli.add_command(schedule)
cli.add_command(json)
cli.add_command(info)
cli.add_command(stream_url)


@click.command()
@click.option("--play", help="Play the specified mixtape by name (e.g. 'poolside')")
@click.option("--url", is_flag=True, help="Show stream URLs for all mixtapes")
@click.option("--info", help="Show detailed information for a specific mixtape")
@click.option("--random", is_flag=True, help="Play random mixtapes continuously")
@click.pass_context
def infinite(ctx, play, url, info, random):
    """List NTS infinite mixtapes"""
    import random as rand
    import subprocess
    import sys
    
    console = Console(no_color=ctx.obj["no_color"])

    with console.status("[bold blue]Fetching mixtapes data..."):
        data, error = get_mixtapes_data()
        if error:
            console.print(f"[bold red]Error:[/] {error}")
            return
        if not data:
            console.print("[bold red]Error:[/] No data received from API")
            return

    if random:
        while True:
            try:
                mixtape = rand.choice(data["results"])
                console.print(f"[bold blue]Playing:[/] {mixtape['title']}")
                subprocess.run(
                    ["mpv", mixtape["audio_stream_endpoint"]],
                    check=True,
                )
            except FileNotFoundError:
                console.print("[bold red]Error:[/] mpv not found. Please ensure mpv is installed.")
                sys.exit(1)
            except subprocess.CalledProcessError:
                # If the stream ends or errors, we'll just continue to the next random mixtape
                continue
            except KeyboardInterrupt:
                sys.exit(0)

    if info:
        # Find and show info for the specified mixtape
        for mixtape in data["results"]:
            if (
                mixtape["mixtape_alias"].lower() == info.lower()
                or mixtape["title"].lower() == info.lower()
            ):
                # Create info panel
                info_text = Text()
                info_text.append(f"{mixtape['title']}\n", style="bold blue")
                info_text.append(f"{mixtape['subtitle']}\n\n", style="yellow")
                info_text.append(f"{mixtape['description']}\n\n")

                if mixtape["credits"]:
                    info_text.append("Featured Shows:\n", style="bold green")
                    for credit in mixtape["credits"]:
                        info_text.append(f"• {credit['name']}\n")

                panel = Panel(
                    info_text,
                    title=f"MIXTAPE: {mixtape['title'].upper()}",
                    border_style="blue",
                    box=box.ROUNDED,
                )
                console.print(panel)
                return
        console.print(f"[bold red]Error:[/] Mixtape '{info}' not found")
        return

    if play:
        # Find and play the specified mixtape
        if "results" not in data:
            console.print("[bold red]Error:[/] Invalid data format received from API")
            return
        for mixtape in data["results"]:
            if (
                mixtape["mixtape_alias"].lower() == play.lower()
                or mixtape["title"].lower() == play.lower()
            ):
                import subprocess
                import sys

                try:
                    subprocess.run(
                        ["mpv", mixtape["audio_stream_endpoint"]],
                        check=True,
                    )
                    return
                except FileNotFoundError:
                    console.print(
                        "[bold red]Error:[/] mpv not found. Please ensure mpv is installed."
                    )
                    sys.exit(1)
                except subprocess.CalledProcessError as e:
                    console.print(f"[bold red]Error playing stream:[/] {e}")
                    sys.exit(1)
        console.print(f"[bold red]Error:[/] Mixtape '{play}' not found")
        return

    # Create table with mixtape information
    table = Table(title="NTS Infinite Mixtapes", box=box.ROUNDED)

    if url:
        # Simplified table with URLs
        table.add_column("Title", style="bold blue")
        table.add_column("Alias", style="yellow")
        table.add_column("Stream URL", style="green")
    else:
        # Full table with descriptions
        table.add_column("Title", style="bold blue")
        table.add_column("Description")
        table.add_column("Alias", style="yellow")

    if "results" not in data:
        console.print("[bold red]Error:[/] Invalid data format received from API")
        return

    for mixtape in data["results"]:
        if url:
            table.add_row(
                mixtape["title"],
                mixtape["mixtape_alias"],
                mixtape["audio_stream_endpoint"],
            )
        else:
            table.add_row(
                mixtape["title"],
                Text(mixtape["description"], style="white", overflow="fold"),
                mixtape["mixtape_alias"],
            )

    console.print(table)


cli.add_command(infinite)
cli.add_command(play)

if __name__ == "__main__":
    cli()
