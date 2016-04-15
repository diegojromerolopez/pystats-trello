# -*- coding: utf-8 -*-

import numpy
import settings
from stats.debug import print_card


def get_stats(client, board_name):

    boards = client.list_boards()
    for board in boards:
        if board.name.decode("utf-8") == board_name:
            return get_stats_by_board(board)

    return None


def get_stats_by_board(board):
    lists = board.all_lists()
    times = get_times_by_board(board)
    time_by_list = times["time_by_list"]

    avg_time_by_list = {}
    std_dev_time_by_list = {}
    for list_name, list_times in time_by_list.items():
        avg_time_by_list[list_name] = numpy.mean(list_times)
        std_dev_time_by_list[list_name] = numpy.std(list_times, axis=0)

    stats = {
        "lists": lists,
        "time_by_list": {"avg": avg_time_by_list, "std_dev": std_dev_time_by_list},
        "lead_time": {"avg": numpy.mean(times["lead_time"]), "std_dev": numpy.std(times["lead_time"], axis=0)},
        "cycle_time": {"avg": numpy.mean(times["cycle_time"]), "std_dev": numpy.std(times["cycle_time"], axis=0)},
    }
    return stats


def get_times_by_board(board):
    # All the lists of a board
    lists = board.all_lists()

    # The last list is "Done" list. It is used to check if the card is done.
    last_list = lists[-1]

    # Lists that play a role in the computation of cycle time
    cycle_lists_dict = {list_.id: True for list_ in get_cycle_lists(board, lists)}

    # Each one of the time of each card in each list
    time_by_list = {list_.id: [] for list_ in lists}

    cycle_time = []
    lead_time = []

    cards = board.all_cards()
    num_cards = len(cards)
    i = 1
    for card in cards:
        print_card(card, "{0} {i} of {num_cards}".format(card.name, i=i, num_cards=num_cards))

        card.time_by_list = card.get_time_by_list(done_list=last_list, tz=settings.TIMEZONE, time_unit="hours")

        # Add zero time of columns this card has not been yet
        for list_ in lists:
            if not list_.id in card.time_by_list:
                card.time_by_list[list_.id] = 0

        # If the card is done, compute lead and cycle time
        if card.idList == last_list.id:
            #  Lead time (time between creation in board to reaching "Done" state)
            card.lead_time = sum([time_ for list_, time_ in card.time_by_list.items()])
            lead_time.append(card.lead_time)
            # Cycle time (time between development and reaching "Done" state)
            card.cycle_time = sum(
                [time_ if list_ in cycle_lists_dict else 0 for list_, time_ in card.time_by_list.items()])
            cycle_time.append(card.cycle_time)

        # Add this card time to global time by list
        for list_ in lists:
            time_by_list[list_.id].append(card.time_by_list[list_.id])

        i += 1

    stats = {
        "lists": lists,
        "cards": cards,
        "time_by_list": time_by_list,
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
