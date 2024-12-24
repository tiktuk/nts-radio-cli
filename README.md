# NTS Radio CLI

A command-line interface to check what's playing on NTS Radio.

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

## Features

- Display currently playing shows on both NTS channels
- Show upcoming broadcasts
- View full schedule for both channels
- Optional ASCII art display of show artwork with customizable dimensions
- Access raw JSON data from the NTS API
- View stream URLs and general NTS Radio information
- Option to disable colored output

### Disable Colors

You can disable colored output using the `--no-color` option:

```bash
nts-radio --no-color json
```

## Requirements

- Python 3.8 or higher

## Testing

To run the tests:

```bash
# Install test dependencies
uv sync --group dev

# Run tests
uv run pytest
```
