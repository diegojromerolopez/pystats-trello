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


# How to use it

```python
stats.trellostats.get_stats
```

returns the status of the board. See test.py for more details.