# -*- coding: utf-8 -*-

from charts import trellochart
from printer.printer import Printer
from stats import trellostats


def make(client, board_name):
    """
    Creates a summary of the stats of a card board.
    Creates a txt file with the data and three svgs with the charts.
    :param client: TrelloClient used to get information
    :param board_name: Name of the board.
    """

    stats = trellostats.get_stats(client, board_name=board_name)

    printer = Printer(u"results_for_{0}_board".format(board_name))

    printer.newline()
    printer.p(u"Measurements for {0}".format(board_name))

    # Average time in each column for all the cards
    printer.p(u"# Average time in each column for all the board cards")
    for list_ in stats["lists"]:
        list_id = list_.id
        list_name = list_.name.decode("utf-8")
        avg_list_time = stats["time_by_list"][list_id]["avg"]
        std_dev_list_time = stats["time_by_list"][list_id]["std_dev"]
        printer.p(u"- {0}: {1} h (std. dev. {2})".format(list_name, avg_list_time, std_dev_list_time))

    printer.newline()

    # Forward/backward movements by column for all the cards
    printer.p(u"# Sum of forward/backward movements by source column for all the cards")
    for list_ in stats["lists"]:
        list_id = list_.id
        list_name = list_.name.decode("utf-8")
        forward_movements = stats["forward_movements_by_list"][list_id]
        backward_movements = stats["backward_movements_by_list"][list_id]
        printer.p(u"- {0}".format(list_name))
        printer.p(u"  - Forward movements: {0}".format(forward_movements))
        printer.p(u"  - Backward movements: {0}".format(backward_movements))

    printer.newline()

    # Cycle time
    printer.p(u"# Cycle")
    printer.p(u"Time between development state and reaching 'Done' state.")
    printer.p(u"- avg: {0} h, std_dev: {1}".format(stats["cycle_time"]["avg"], stats["cycle_time"]["std_dev"]))

    # Lead time
    printer.p(u"# Lead")
    printer.p(u"Time from start to end ('Done' state).")
    printer.p(u"- avg: {0} h, std_dev: {1}".format(stats["lead_time"]["avg"], stats["lead_time"]["std_dev"]))

    # Chart with times for all cards in each column
    file_paths = trellochart.get_graphics(stats, board_name=board_name)

    printer.newline()
    printer.p(u"Chart with average card time in each list created in {0}".format(file_paths["time"]))
    printer.p(u"Chart with average time a list is a forward destination in {0}".format(file_paths["forward"]))
    printer.p(u"Chart with average time a list is a backward destination in {0}".format(file_paths["backward"]))

    printer.flush()