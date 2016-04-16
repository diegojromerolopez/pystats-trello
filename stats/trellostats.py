# -*- coding: utf-8 -*-

import datetime
import numpy
import settings
from stats.debug import print_card


def get_stats(client, board_name, card_is_active_function=lambda c: True):

    boards = client.list_boards()
    for board in boards:
        if board.name.decode("utf-8") == board_name:
            return get_statistic_summary_by_board(board, card_is_active_function)

    return None


def get_statistic_summary_by_board(board, card_is_active_function):

    def statistic_summary(value_list):
        return {"avg": numpy.mean(value_list), "std_dev": numpy.std(value_list, axis=0)}

    def statistic_summary_by_list(stat_by_list):
        stats_summary_by_list = {}
        for list_name_, list_times_ in stat_by_list.items():
            stats_summary_by_list[list_name_] = statistic_summary(list_times_)

        return stats_summary_by_list

    stats = get_stats_by_board(board, card_is_active_function)

    stats.update(
        {
            "time_by_list": statistic_summary_by_list(stats["time_by_list"]),
            "lead_time": statistic_summary(stats["lead_time"]),
            "cycle_time": statistic_summary(stats["cycle_time"])
        }
    )

    return stats


def get_stats_by_board(board, card_is_active_function):
    # All the lists of a board
    lists = board.all_lists()

    # Compute list orders
    i = 1
    for list_ in lists:
        list_.order = i
        i += 1

    lists_dict = {list_.id : list_ for list_ in lists}

    # Comparison function used to compute forward and backward movements
    # when computing card.stats_by_list
    def list_cmp(list_a_id, list_b_id):
        if lists_dict[list_b_id].order > lists_dict[list_a_id].order:
            return 1
        if lists_dict[list_b_id].order < lists_dict[list_a_id].order:
            return -1
        return 0

    # The last list is "Done" list. It is used to check if the card is done.
    last_list = lists[-1]

    # Lists that play a role in the computation of cycle time
    cycle_lists_dict = {list_.id: True for list_ in get_cycle_lists(board, lists)}

    # Each one of the time of each card in each list
    time_by_list = {list_.id: [] for list_ in lists}

    forward_list = {list_.id: 0 for list_ in lists}
    backward_list = {list_.id: 0 for list_ in lists}

    cycle_time = []
    lead_time = []

    # Done cards
    done_cards = []

    # We store card_creation_datetimes to extract min datetime
    card_creation_datetimes = []

    # Board last activity to computer board life time
    board_last_activity = None

    cards = board.all_cards()
    num_cards = len(cards)
    i = 1
    for card in cards:
        # Custom filter for only considering cards we want
        if card_is_active_function(card):
            print_card(card, "{0} {i} of {num_cards}".format(card.name, i=i, num_cards=num_cards))
            card.stats_by_list = card.get_stats_by_list(lists=lists, list_cmp=list_cmp, done_list=last_list, tz=settings.TIMEZONE, time_unit="hours")

            # If the card is done, compute lead and cycle time
            if card.idList == last_list.id:
                #  Lead time (time between creation in board to reaching "Done" state)
                card.lead_time = sum([list_stats["time"] for list_id, list_stats in card.stats_by_list.items()])
                lead_time.append(card.lead_time)
                # Cycle time (time between development and reaching "Done" state)
                card.cycle_time = sum(
                    [list_stats["time"] if list_id in cycle_lists_dict else 0 for list_id, list_stats in card.stats_by_list.items()]
                )
                cycle_time.append(card.cycle_time)
                done_cards.append(card)

            # Add this card stats to each global stat
            for list_ in lists:
                list_id = list_.id
                card_list_stats = card.stats_by_list[list_id]
                time_by_list[list_id].append(card_list_stats["time"])
                forward_list[list_id] += card_list_stats["forward_moves"]
                backward_list[list_id] += card_list_stats["backward_moves"]

            # Card creation datetime
            card_creation_datetimes.append(card.create_date)

            # Getting the last activity in the board
            if board_last_activity is None or board_last_activity < card.date_last_activity:
                board_last_activity = card.date_last_activity

        i += 1

    now = datetime.datetime.now(settings.TIMEZONE)
    first_card_creation_datetime = min(card_creation_datetimes)
    last_card_creation_datetime = max(card_creation_datetimes)
    board_life_time = (board_last_activity - first_card_creation_datetime).total_seconds()

    stats = {
        "lists": lists,
        "cards": cards,
        "done_cards": done_cards,
        "done_cards_per_hour": len(done_cards) / (board_life_time/60.0),
        "done_cards_per_day": len(done_cards)/(board_life_time/3600.0),
        "board_life_time": board_life_time / 60.0,
        "board_last_activity": board_last_activity,
        "last_card_creation": last_card_creation_datetime,
        "last_card_creation_ago": (now - last_card_creation_datetime).total_seconds(),
        "time_by_list": time_by_list,
        "backward_movements_by_list": backward_list,
        "forward_movements_by_list": forward_list,
        "lead_time": lead_time,
        "cycle_time": cycle_time
    }
    return stats


def get_cycle_lists(board, lists):
    """
    Returns a list of objects trello.Lists that play a role in computing the cycle time.
    :param lists:
    :return:
    """

    if board.name in settings.DEVELOPMENT_LIST:
        development_list_name = settings.DEVELOPMENT_LIST[board.name]
    else:
        development_list_name = settings.DEVELOPMENT_LIST["_default"]

    cycle_lists = []
    add_to_cycle_list = False
    for _list in lists:
        if _list.name.decode("utf-8") == development_list_name:
            add_to_cycle_list = True
        if add_to_cycle_list:
            cycle_lists.append(_list)

    if len(cycle_lists) <= 1:
        raise EnvironmentError(
            u"Development list has not been configured for board {0}".format(board.name.decode("utf-8")))

    return cycle_lists
