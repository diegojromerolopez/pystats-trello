# -*- coding: utf-8 -*-
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

    stat_extractor = trellostatsextractor.TrelloStatsExtractor(trello_connector=trello_connector,
                                                               configuration=configuration)

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

    statistics = stat_extractor.get_stats()

    stats = statistics.get()

    printer = Printer(u"results_for_{0}_board".format(configuration.board_name), configuration)

    printer.newline()

    printer.p(u"# Measurements for {0}".format(configuration.board_name))

    printer.newline()

    # Board life time
    printer.p(u"## General measurements for {0}".format(configuration.board_name))
    printer.p(u"- The board is {0} hours old".format(stats["board_life_time"]))
    printer.p(u"- Last card was created {0} hours ago".format(stats["last_card_creation"]["hours_ago"]))

    # Task number
    printer.p(u"- There are {0} tasks ({1} active / {2} inactive [see note 1]) (".format(stats["num_cards"], stats["num_active_cards"], stats["num_inactive_cards"]))
    printer.p(u"- There are {0} tasks in 'done' ({1} are inactive [see note 1])".format(stats["done_cards"]["count"], len(stats["inactive_cards"]["done"])))
    printer.p(u"- {0} tasks per day or {1} tasks per hour".format(stats["done_cards"]["per_day"], stats["done_cards"]["per_hour"]))
    printer.p(u"[note 1]: A card is active if meets this criterion: {0}".format(configuration.card_is_active_function))

    printer.newline()

    # Average time in each column for all the cards
    printer.p(u"## Average time in each column for all the board cards{0}".format(in_date_interval_text))
    for list_ in stats["board_lists"]:
        list_id = list_.id
        list_name = list_.name.decode("utf-8")
        avg_list_time = stats["lists"][list_id]["time"]["avg"]
        std_dev_list_time = stats["lists"][list_id]["time"]["std_dev"]
        printer.p(u"- {0}: {1} h (std. dev. {2})".format(list_name, avg_list_time, std_dev_list_time))

    printer.newline()

    # Forward/backward movements by column for all the cards
    printer.p(u"## Sum of forward/backward movements by source column for all the cards{0}".format(in_date_interval_text))
    for list_ in stats["board_lists"]:
        list_id = list_.id
        list_name = list_.name.decode("utf-8")
        forward_movements = stats["lists"][list_id]["forward_moves"]
        backward_movements = stats["lists"][list_id]["backward_moves"]
        printer.p(u"- {0}".format(list_name))
        printer.p(u"  - Forward movements: {0}".format(forward_movements))
        printer.p(u"  - Backward movements: {0}".format(backward_movements))

    printer.newline()

    # Cycle time
    printer.p(u"## Cycle")
    printer.p(u"Time between development state and reaching 'Done' state{0}".format(in_date_interval_text))
    for card in stats["done_cards"]["list"]:
        printer.p(u"- {0} {1}: {2}".format(card.id, _short_card_name(card), stats["cycle_time"]["dict"][card.id]))
    printer.p(u"- avg: {0} h, std_dev: {1}".format(stats["cycle_time"]["avg"], stats["cycle_time"]["std_dev"]))

    printer.newline()

    # Lead time
    printer.p(u"## Lead")
    printer.p(u"Time from start to end ('Done' state){0}".format(in_date_interval_text))
    for card in stats["done_cards"]["list"]:
        printer.p(u"- {0} {1}: {2}".format(card.id, _short_card_name(card), stats["lead_time"]["dict"][card.id]))
    printer.p(u"- avg: {0} h, std_dev: {1}".format(stats["lead_time"]["avg"], stats["lead_time"]["std_dev"]))

    # Chart with times for all cards in each column
    file_paths = trellochart.get_graphics(stats, configuration)

    printer.newline()

    # Custom workflows
    if stat_extractor.has_custom_workflows():
        for custom_workflow in stat_extractor.get_custom_workflows():
            custom_workflow_id = custom_workflow.name
            printer.p(u" ## Custom workflow {0}".format(custom_workflow.name))
            for card_id, card_props in stats["active_cards"].items():
                card = card_props["object"]
                if "custom_workflow_times" in card_props and\
                        custom_workflow_id in card_props["custom_workflow_times"] and\
                        not card_props["custom_workflow_times"][custom_workflow_id] is None:
                    card_line = u"{0}".format(card_props["custom_workflow_times"][custom_workflow_id])
                    printer.p(u"- {0} '{1}': {2}".format(card_id, _short_card_name(card), card_line))

            printer.newline()

    # Time each card has been in each column
    printer.p(u"# Time each card has been in each column (hours){0}".format(in_date_interval_text))

    lists_header = u""
    for list_ in stats["board_lists"]:
        lists_header += list_.name.decode("utf-8") + (", " if list_.id != stat_extractor.done_list.id else "")

    printer.p(u"{0} {1} {2}".format(u"Card_id", u"Card_name", lists_header))

    for card_id, card_props in stats["active_cards"].items():
        card_line = u""
        card = card_props["object"]
        for list_ in stats["board_lists"]:
            card_time_in_list = card_props["stats_by_list"][list_.id]["time"]
            card_line += u"{0}{1}".format(card_time_in_list, (", " if list_.id != stat_extractor.done_list.id else ""))
        printer.p(u"- {0} '{1}': {2}".format(card_id, _short_card_name(card), card_line))

    printer.newline()

    if configuration.spent_estimated_time_card_comment_regex:
        printer.p(u"# Spent and estimated times for each card (in units given by plugin)")

        printer.p(u"Card_id Card_name CurrentList Spent Estimated")
        for card_id, card_props in stats["active_cards"].items():
            card = card_props["object"]
            card_name = _short_card_name(card)
            list_name = stat_extractor.lists_dict[card.idList].name.decode("utf-8")

            # Card spent time
            card_spent_time = "N/A"
            if not stats["active_cards"][card.id]["spent"]["all"] is None:
                card_spent_time = stats["active_cards"][card.id]["spent"]["all"]

            # Card estimated time
            card_estimated_time = "N/A"
            if not stats["active_cards"][card.id]["estimated"]["all"] is None:
                card_estimated_time = stats["active_cards"][card.id]["estimated"]["all"]

            printer.p(u"- {0} '{1}' ({2}): {3} {4}".format(
                    card.id, card_name, list_name, card_spent_time, card_estimated_time
                )
            )

        printer.newline()

    printer.p(u"Chart with average card time in each list created in {0}".format(file_paths["time"]["path"]))
    printer.p(u"Chart with average time a list is a forward destination in {0}".format(file_paths["forward"]["path"]))
    printer.p(u"Chart with average time a list is a backward destination in {0}".format(file_paths["backward"]["path"]))

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
