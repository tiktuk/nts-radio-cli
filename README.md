# NTS Radio CLI

A command-line interface to check what's playing on NTS Radio.

## Installation

```bash
pip install nts
```

Or if using UV:
```bash
uv pip install nts
```

## Usage

The CLI provides two main commands:

### Check Currently Playing Shows

```bash
nts now
```

To include show artwork (displayed in ASCII art):
```bash
nts now --art
```

### View Full Schedule

```bash
nts schedule
```

## Features

- Display currently playing shows on both NTS channels
- Show upcoming broadcasts
- View full schedule for both channels
- Optional ASCII art display of show artwork
- Real-time conversion of show times to your local timezone

## Requirements

- Python 3.8 or higher
