# pystats-trello

Statistics and charts for Trello boards.

These small utilities gives you the functionality needed to extract some metric from Trello Kanban boards.

# Requirements

See requirements.txt.


# Implemented Kanban Metrics

## Time by column

Average time the cards spend in each column.

Very useful to detect bottlenecks in your management process or project.

## Cycle

Time between development state and reaching "Done" state.

The average development and deployment time for all tasks of board.

## Lead time

Time from start to end ("Done" state).

Time a client has to wait to see a feature he/she asked.


# Configuration

First you have to create a file in the root of the project with the name **settings_local.py**.

This file will contain authentication information and other global preferences for this project:

```python

# Trello authentication parameters, see https://trello.com/app-key for more information
TRELLO_API_KEY = "<trello api key>"
TRELLO_API_SECRET = "<trello api secret>"

TRELLO_TOKEN = "<trello token>"
TRELLO_TOKEN_SECRET = "<trello token secret>"

# This dict allows you to specify which of your columns is the "in development" column
# why is this needed? To compute cycle time.
DEVELOPMENT_LIST = {
    "_default": u"<default name of 'development' in your Kanban boards>",
    # You can specify different names for specific boards:
    "<board_1>": u"<board_1_in_development_name>",
    "<board_2>": u"<board_2_in_development_name>",
    # ...
    "<board_N>": u"<board_N_in_development_name>",
}

# Output dir for the stats
OUTPUT_DIR = "<output>"
```


# How to use it

```python

python stats_extractor.py <board_name>

```


returns the status of the board. See test.py for more details.