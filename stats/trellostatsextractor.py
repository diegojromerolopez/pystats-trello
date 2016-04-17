# -*- coding: utf-8 -*-
import datetime
import numpy
import re

import settings
from stats.debug import print_card


class TrelloStatsExtractor(object):

    # Constructor based on credentials and a board name of the board it will compute the stats
    def __init__(self, trello_connector, board_name):
        self.client = trello_connector.get_trello_client()
        self._fetch_board(board_name)

    # Fetches the board from Trello API
    # It also fetches and initializes its lists and its cards.
    def _fetch_board(self, board_name):
        """
        Connects to Trello and sets the board (py-trello Board object).
        :return: True if board with self.board_name was found, raise and exception otherwise.
        """
        boards = self.client.list_boards()
        for board in boards:
            if board.name.decode("utf-8") == board_name:
                self.board_name = board_name
                self.board = board
                self._fetch_lists()
                self._init_cards()
                return True
        raise RuntimeWarning(u"Board {0} was not found. Are your credentials correct?".format(self.board_name))

    # Fetching of the board lists from Trello API
    def _fetch_lists(self):
        """
        Initialize lists and lists_dict attributes of this objects.
        These attributes contain a list of the board lists and a dict for fast access to a list given its id.
        """
        # List of the board
        self.lists = self.board.all_lists()

        # Compute list orders
        i = 1
        for list_ in self.lists:
            list_.order = i
            i += 1

        # List dict of the board used to avoid fetching list data more than once
        self.lists_dict = {list_.id: list_ for list_ in self.lists}
        self.lists_dict_by_name = {list_.name.decode("utf-8"): list_ for list_ in self.lists}

        # Comparison function used to compute forward and backward movements
        # when computing card.stats_by_list
        def list_cmp(list_a_id, list_b_id):
            if self.lists_dict[list_b_id].order > self.lists_dict[list_a_id].order:
                return 1
            if self.lists_dict[list_b_id].order < self.lists_dict[list_a_id].order:
                return -1
            return 0

        self.list_cmp = list_cmp

        # Done list initialization
        self._init_done_list()

        # Cycle lists initialization
        self._init_cycle_lists()

    # Done list initialization
    def _init_done_list(self):
        # List that will be considered the "done list"
        # It is used to check if the card is done.

        # By default, the last list is the "done list"
        self.done_list = self.lists[-1]

        # But we could have specified another one
        if hasattr(settings, "DONE_LIST"):
            if self.board_name in settings.DONE_LIST:
                self.done_list = self.lists_dict_by_name[settings.DONE_LIST[self.board_name]]
            else:
                self.done_list = self.lists_dict_by_name[settings.DONE_LIST["_default"]]

    # Initializes the cycle lists
    def _init_cycle_lists(self):
        """
        Initializes the lists that play a role when computing the cycle time.
        Cycle lists are stored in self.cycle_lists (list) and self.cycle_lists_dict (dict).
        """

        if self.board_name in settings.DEVELOPMENT_LIST:
            development_list_name = settings.DEVELOPMENT_LIST[self.board_name]
        else:
            development_list_name = settings.DEVELOPMENT_LIST["_default"]

        self.cycle_lists = []
        self.cycle_lists_dict = {}

        # Assumes from the development list to the end list, they all play a role in development
        add_to_cycle_list = False
        for _list in self.lists:
            if _list.name.decode("utf-8") == development_list_name:
                add_to_cycle_list = True
            if add_to_cycle_list:
                self.cycle_lists.append(_list)
                self.cycle_lists_dict[_list.id] = _list

        # If there is no cycle lists, assume the configuration is wrong
        if len(self.cycle_lists) <= 1:
            raise EnvironmentError(u"Development list has not been configured for board {0}".format(self.board_name))

    # Initializes the cards
    def _init_cards(self):
        self.cards = self.board.all_cards()

    # Computes the statistics of the cards.
    # Computes mean and standard deviation for metrics time by list, lead_time and Cycle time.
    # The other metrics are absolute values.
    def get_stats(self, card_is_active_function=lambda c: True, card_movements_filter=None):

        def add_statistic_summary(value_list):
            return {"values": value_list, "avg": numpy.mean(value_list), "std_dev": numpy.std(value_list, axis=0)}

        def statistic_summary_by_list(stat_by_list):
            stats_summary_by_list = {}
            for list_name_, list_times_ in stat_by_list.items():
                stats_summary_by_list[list_name_] = add_statistic_summary(list_times_)

            return stats_summary_by_list

        stats = self.get_full_stats(card_is_active_function, card_movements_filter)

        # Change the values for its mean and standard deviation
        stats.update(
            {
                "time_by_list": statistic_summary_by_list(stats["time_by_list"]),
            }
        )

        return stats

    # Compute the full stats of the board.
    # That is, it computes the concrete values for each measure.
    def get_full_stats(self, card_is_active_function, card_movements_filter=None):

        # Utility function that check if a card is done
        def card_is_done(_card):
            return _card.idList == self.done_list.id

        # Each one of the time of each card in each list
        time_by_list = {list_.id: [] for list_ in self.lists}

        # Forward or backward movements
        forward_list = {list_.id: 0 for list_ in self.lists}
        backward_list = {list_.id: 0 for list_ in self.lists}

        cycle_time = {}
        lead_time = {}

        # Active cards by our definition given by the lambda function
        active_cards = []

        # Cards that are not active
        inactive_cards = []
        done_inactive_cards = []

        # Closed cards
        closed_cards = []

        # Closed done cards
        closed_done_cards = []

        # Done cards
        done_cards = []

        # We store card_creation_datetimes to extract min datetime
        card_creation_datetimes = []

        # Board last activity to computer board life time
        board_last_activity = None

        num_cards = len(self.cards)
        i = 1
        for card in self.cards:

            # Test if the card is closed
            if card.closed:
                closed_cards.append(card)
                # If the card is closed, test if was closed in the "done" list
                if card_is_done(card):
                    closed_done_cards.append(card)

            # Custom filter for only considering cards we want. By default it should be "not card.closed", but we
            # give programmers the option to customize this parameter
            if card_is_active_function(card):
                print_card(card, "{0} {i} of {num_cards}".format(card.name, i=i, num_cards=num_cards))
                card.stats_by_list = card.get_stats_by_list(lists=self.lists, list_cmp=self.list_cmp, done_list=self.done_list,
                                                            tz=settings.TIMEZONE, time_unit="hours",
                                                            card_movements_filter=card_movements_filter)

                # If the card is done, compute lead and cycle time
                if card_is_done(card):
                    #  Lead time (time between creation in board to reaching "Done" state)
                    card.lead_time = sum([list_stats["time"] for list_id, list_stats in card.stats_by_list.items()])
                    lead_time[card.id] = card.lead_time
                    # Cycle time (time between development and reaching "Done" state)
                    card.cycle_time = sum(
                        [list_stats["time"] if list_id in self.cycle_lists_dict else 0 for list_id, list_stats in card.stats_by_list.items()]
                    )
                    cycle_time[card.id] = card.cycle_time
                    done_cards.append(card)

                # Add this card stats to each global stat
                for list_ in self.lists:
                    list_id = list_.id
                    card_stats_by_list = card.stats_by_list[list_id]
                    time_by_list[list_id].append(card_stats_by_list["time"])
                    forward_list[list_id] += card_stats_by_list["forward_moves"]
                    backward_list[list_id] += card_stats_by_list["backward_moves"]

                # Comments
                card.s_e = self._get_spent_estimated(card)

                # Card creation datetime
                card_creation_datetimes.append(card.create_date)

                # Getting the last activity in the board
                if board_last_activity is None or board_last_activity < card.date_last_activity:
                    board_last_activity = card.date_last_activity

                active_cards.append(card)

            # Inactive cards
            else:
                inactive_cards.append(card)
                if card_is_done(card):
                    done_inactive_cards.append(card)

            i += 1

        now = datetime.datetime.now(settings.TIMEZONE)
        first_card_creation_datetime = min(card_creation_datetimes)
        last_card_creation_datetime = max(card_creation_datetimes)
        board_life_time = (board_last_activity - first_card_creation_datetime).total_seconds()

        stats = {
            "lists": self.lists,
            "cards": self.cards,
            "active_card_stats_by_list": {card.id: card.stats_by_list for card in active_cards},
            "active_card_spent_estimated_times": {card.id: card.s_e for card in active_cards},
            "active_cards": active_cards,
            "done_inactive_cards": done_inactive_cards,
            "inactive_cards": inactive_cards,
            "closed_cards": closed_cards,
            "closed_done_cards": closed_done_cards,
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
            "lead_time": {
                "values": lead_time,
                "avg": numpy.mean(lead_time.values()),
                "std_dev": numpy.std(lead_time.values(), axis=0)
            },
            "cycle_time": {
                "values": cycle_time,
                "avg": numpy.mean(cycle_time.values()),
                "std_dev": numpy.std(cycle_time.values(), axis=0)
            },
        }
        return stats

    # Gets the spent and estimated times for this card
    # Plugins like Plus for Trello are able to store estimated duration of the task and actual spent time in comments.
    # This plugins has a format (plus! <spent>/<estimated> in case of Plus for Trello) and this format can be defined
    # in settings local by the use of a regular expression.
    def _get_spent_estimated(self, card):
        # If there is no defined regex with the format of spent/estimated comment in cards, don't fetch comments
        if not hasattr(settings, "SPENT_ESTIMATED_TIME_CARD_COMMENT_REGEX"):
            return False

        comments = card.get_comments()
        spent = None
        estimated = None
        # For each comment, find the desired pattern and extract the spent and estimated times
        for comment in comments:
            comment_content = comment["data"]["text"]
            matches = re.match(settings.SPENT_ESTIMATED_TIME_CARD_COMMENT_REGEX, comment_content)
            if matches:
                if spent is None:
                    spent = 0
                spent += float(matches.group("spent"))
                if estimated is None:
                    estimated = 0
                estimated += float(matches.group("estimated"))
        return {"spent": spent, "estimated": estimated}
