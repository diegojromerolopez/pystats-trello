# -*- coding: utf-8 -*-
import numpy

from charts import trellochart
from printer.printer import Printer
from stats import trellostatsextractor
import settings
import inspect


def make(trello_connector, configuration):
    """
    Creates a summary of the stats of a card board.
    Creates a txt file with the data and three png images with the charts.
    :param trello_connector: TrelloConnector used to get information
    :param configuration: Configuration of the board (TrelloBoardConfiguration)
    """

    stat_extractor = trellostatsextractor.TrelloStatsExtractor(trello_connector=trello_connector, configuration=configuration)

    # Setting the function that tests if a card is active
    card_is_active_function = lambda c: not c.closed
    if configuration.card_is_active_function:
        card_is_active_function = configuration.card_is_active_function

    # Suffix for the titles of the output file in case there is a
    card_action_filter = configuration.card_action_filter
    in_date_interval_text = u""
    if card_action_filter:
        if card_action_filter[0] and card_action_filter[1]:
            in_date_interval_text = u" between dates {0} and {1}".format(card_action_filter[0], card_action_filter[1])
        elif card_action_filter[0]:
            in_date_interval_text = u" since {0}".format(card_action_filter[0])
        elif card_action_filter[1]:
            in_date_interval_text = u" before {0}".format(card_action_filter[1])

    stats = stat_extractor.get_stats()

    printer = Printer(u"results_for_{0}_board".format(configuration.board_name), configuration)

    printer.newline()

    printer.p(u"# Measurements for {0}".format(configuration.board_name))

    printer.newline()

    # Board life time
    printer.p(u"## General measurements for {0}".format(configuration.board_name))
    printer.p(u"- The board is {0} hours old".format(stats["board_life_time"]))
    printer.p(u"- Last card was created {0} hours ago".format(stats["last_card_creation_ago"]/3600.0))

    # Task number
    printer.p(u"- There are {0} tasks ({1} active / {2} inactive [see note 1]) (".format(len(stats["cards"]), len(stats["active_cards"]), len(stats["inactive_cards"])))
    printer.p(u"- There are {0} tasks in 'done' ({1} are inactive [see note 1])".format(len(stats["done_cards"]), len(stats["done_inactive_cards"])))
    printer.p(u"- {0} tasks per day or {1} tasks per hour".format(stats["done_cards_per_day"], stats["done_cards_per_hour"]))
    printer.p(u"[note 1]: A card is active if meets this criterion: {0}".format(configuration.card_is_active_function))

    printer.newline()

    # Average time in each column for all the cards
    printer.p(u"## Average time in each column for all the board cards{0}".format(in_date_interval_text))
    for list_ in stats["lists"]:
        list_id = list_.id
        list_name = list_.name.decode("utf-8")
        avg_list_time = stats["time_by_list"][list_id]["avg"]
        std_dev_list_time = stats["time_by_list"][list_id]["std_dev"]
        printer.p(u"- {0}: {1} h (std. dev. {2})".format(list_name, avg_list_time, std_dev_list_time))

    printer.newline()

    # Forward/backward movements by column for all the cards
    printer.p(u"## Sum of forward/backward movements by source column for all the cards{0}".format(in_date_interval_text))
    for list_ in stats["lists"]:
        list_id = list_.id
        list_name = list_.name.decode("utf-8")
        forward_movements = stats["forward_movements_by_list"][list_id]
        backward_movements = stats["backward_movements_by_list"][list_id]
        printer.p(u"- {0}".format(list_name))
        printer.p(u"  - Forward movements: {0}".format(forward_movements))
        printer.p(u"  - Backward movements: {0}".format(backward_movements))

    printer.newline()

    # Backward movements of tasks assigned to a user
    printer.p(u"## Forward/backward movements movements by username in this board{0}".format(in_date_interval_text))
    for member_id, member in stat_extractor.members_dict.items():
        movements = stats["movements_by_user"].get(member_id)
        if movements:
            printer.p(u"  - Forward movements of {0}'s tasks: {1}".format(member.username, movements["forward"]))
            printer.p(u"  - Backward movements of {0}'s tasks: {1}".format(member.username, movements["backward"]))

    printer.newline()

    # Cycle time
    printer.p(u"## Cycle")
    printer.p(u"Time between development state and reaching 'Done' state{0}".format(in_date_interval_text))
    for card in stats["done_cards"]:
        printer.p(u"- {0} {1}: {2}".format(card.id, _short_card_name(card), stats["cycle_time"]["values"][card.id]))
    printer.p(u"- avg: {0} h, std_dev: {1}".format(stats["cycle_time"]["avg"], stats["cycle_time"]["std_dev"]))

    printer.newline()

    # Lead time
    printer.p(u"## Lead")
    printer.p(u"Time from start to end ('Done' state){0}".format(in_date_interval_text))
    for card in stats["done_cards"]:
        printer.p(u"- {0} {1}: {2}".format(card.id, _short_card_name(card), stats["lead_time"]["values"][card.id]))
    printer.p(u"- avg: {0} h, std_dev: {1}".format(stats["lead_time"]["avg"], stats["lead_time"]["std_dev"]))

    # Chart with times for all cards in each column
    file_paths = trellochart.get_graphics(stats, stat_extractor)

    printer.newline()

    # Custom workflows
    if stat_extractor.has_custom_workflows():
        for custom_workflow in stat_extractor.get_custom_workflows():
            custom_workflow_id = custom_workflow.name
            printer.p(u" ## Custom workflow {0}".format(custom_workflow.name))
            workflow_times = []
            for card in stats["cards"]:
                if hasattr(card, "custom_workflow_times") and\
                        custom_workflow_id in card.custom_workflow_times and\
                        not card.custom_workflow_times[custom_workflow_id] is None:
                    workflow_times.append(card.custom_workflow_times[custom_workflow_id])
                    card_line = u"{0}".format(card.custom_workflow_times[custom_workflow_id])
                    printer.p(u"- {0} '{1}': {2}".format(card.id, _short_card_name(card), card_line))
            if len(workflow_times) > 0:
                printer.p(u"- avg: {0} h, std_dev: {1}".format(numpy.mean(workflow_times), numpy.std(workflow_times, axis=0)))
            printer.newline()

    # Time each card has been in each column
    printer.p(u"# Time each card has been in each column (hours){0}".format(in_date_interval_text))

    lists_header = u""
    for list_ in stats["lists"]:
        lists_header += list_.name.decode("utf-8") + (", " if list_.id != stats["lists"][-1].id else "")

    printer.p(u"{0} {1} {2}".format(u"Card_id", u"Card_name", lists_header))

    for card in stats["active_cards"]:
        card_line = u""
        for list_ in stats["lists"]:
            card_line += u"{0}{1}".format(stats["active_card_stats_by_list"][card.id][list_.id]["time"], (", " if list_.id != stats["lists"][-1].id else ""))
        printer.p(u"- {0} '{1}': {2}".format(card.id, _short_card_name(card), card_line))

    printer.newline()

    if configuration.spent_estimated_time_card_comment_regex:
        printer.p(u"# Spent and estimated times for each card (in units given by plugin)")
        spent_times = []
        estimated_times = []
        printer.p(u"Card_id Card_name CurrentList Spent Estimated")
        for card in stats["active_cards"]:
            # Short name of the card
            card_name = _short_card_name(card)

            # List name
            list_name = stat_extractor.lists_dict[card.idList].name.decode("utf-8")

            # Spent/Estimated times of the card
            card_s_e_times = stats["active_card_spent_estimated_times"][card.id]

            card_spent_time = card_s_e_times["spent"] if not card_s_e_times["spent"] is None else u"N/A"
            card_estimated_time = card_s_e_times["estimated"] if not card_s_e_times["estimated"] is None else u"N/A"

            if card_spent_time != "N/A":
                spent_times.append(card_spent_time)
            if card_estimated_time != "N/A":
                estimated_times.append(card_estimated_time)

            printer.p(u"- {0} '{1}' ({2}): {3} {4}".format(
                    card.id, card_name, list_name, card_spent_time, card_estimated_time
                )
            )
        printer.p(u"- Spent Times avg: {0} h, std_dev: {1}".format(numpy.mean(spent_times), numpy.std(spent_times, axis=0)))
        printer.p(u"- Estimated Times avg: {0} h, std_dev: {1}".format(numpy.mean(estimated_times), numpy.std(estimated_times, axis=0)))

        printer.newline()

    printer.p(u"Charts done")

    printer.newline()

    printer.p(u"--- END OF FILE ---")

    printer.flush()


def _short_card_name(card, max_length=40):
    """
    Returns a short form of the card name, adding "..." if it is needed.
    :param card: object trello card.
    :param max_length: Max length of the card name.
    :return: Short card name.
    """
    card_name = card.name.decode("utf-8").replace(u"'", u"\'").replace(u"\"", u"\\\"")
    _short_card_name = card_name[:max_length]
    if len(card_name) > max_length:
        _short_card_name += u"..."
    return _short_card_name
