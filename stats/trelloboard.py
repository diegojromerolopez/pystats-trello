# -*- coding: utf-8 -*-

import settings


# Abstraction of a Trello Board with all the fields needed for the stats initialized
class TrelloBoard(object):

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
                raise EnvironmentError(
                    u"Development list has not been configured for board {0}".format(self.board_name))

        # Initializes the cards
        def _init_cards(self):
            self.cards = self.board.all_cards()

