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

### View Full Schedule

```bash
nts-radio schedule
```

## Features

- Display currently playing shows on both NTS channels
- Show upcoming broadcasts
- View full schedule for both channels
- Optional ASCII art display of show artwork

## Requirements

- Python 3.8 or higher
