# NTS Radio CLI

A command-line interface to check what's playing on NTS Radio.

## Features

- Display currently playing shows on both NTS channels
- Show upcoming broadcasts
- View full schedule for both channels
- Optional ASCII art display of show artwork with customizable dimensions
- Access raw JSON data from the NTS API
- View stream URLs and general NTS Radio information
- Option to disable colored output

## Requirements

- Python 3.8 or higher

## Installation

From PyPI:
```bash
pip install nts-radio-cli
```

Or if using uv:
```bash
uv pip install nts-radio-cli
```

For local development with uv:
```bash
# Install in editable mode
uv pip install -e .

# Run the CLI
uv run nts-radio now
# or
uv run nts-radio schedule
```

## Usage

Once installed from PyPI, you can use these commands:

### Check Currently Playing Shows

```bash
nts-radio now
```

To include show artwork (displayed in ASCII art):
```bash
nts-radio now --art
```

You can customize the size of the artwork using the --art-width and --art-height options:
```bash
# Default size (80x40)
nts-radio now --art

# Custom size (100x50)
nts-radio now --art --art-width 100 --art-height 50

# Smaller size (40x20)
nts-radio now --art --art-width 40 --art-height 20
```

### View Full Schedule

```bash
nts-radio schedule
```

### Get Raw JSON Data

```bash
nts-radio json
```

This command outputs the raw JSON data from the NTS API, which can be useful for debugging or piping to other tools.

### View NTS Information and Stream URLs

```bash
nts-radio info
```

This command displays general information about NTS, including stream URLs for both channels.

### Get Stream URL

```bash
nts-radio stream-url <channel>
```

Get just the stream URL for a specific channel (1 or 2). Useful for piping to other applications.

Examples:
```bash
# Get channel 1 stream URL
nts-radio stream-url 1

# Get channel 2 stream URL
nts-radio stream-url 2

# Example: Play channel 1 in mpv
nts-radio stream-url 1 | xargs mpv

# Example: Play channel 2 in VLC
nts-radio stream-url 2 | xargs vlc
```

### Disable Colors

You can disable colored output using the `--no-color` option:

```bash
nts-radio --no-color json
```

## Testing

To run the tests:

```bash
# Install test dependencies
uv sync --group dev

# Run tests
uv run pytest
```

## Related projects

- [brianmichel/Marconio: A simple NTS.live macOS application](https://github.com/brianmichel/Marconio)
- [everdrone/nts: NTS Radio downloader and metadata parser](https://github.com/everdrone/nts)
- [tiktuk/raycast-nts: Show what's playing on NTS Radio in Raycast](https://github.com/tiktuk/raycast-nts)
- [tiktuk/NTS-Now-Playing-Example: Example of using the NTS api to display now playing info](https://github.com/tiktuk/NTS-Now-Playing-Example)
