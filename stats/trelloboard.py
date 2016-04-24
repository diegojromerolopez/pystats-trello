# -*- coding: utf-8 -*-

import settings


# Abstraction of a Trello Board with all the fields needed for the stats initialized
class TrelloBoard(object):

        # Constructor based on credentials and a board name of the board it will compute the stats
        def __init__(self, trello_connector, configuration):
            self.client = trello_connector.get_trello_client()
            self._fetch_board(configuration.board_name)
            # Check that configuration (that lists name are right)
            self._init_configuration(configuration)

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
                    self._fetch_members()
                    self._fetch_lists()
                    self._fetch_labels()
                    self._init_cards()
                    return True
            raise RuntimeWarning(u"Board {0} was not found. Are your credentials correct?".format(self.board_name))

        # Fetching the members of this board
        def _fetch_members(self):
            self.members = self.board.all_members()
            self.members_dict = {member.id: member for member in self.members}

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
            if self.configuration.done_list_name:
                self.done_list = self.lists_dict_by_name[self.configuration.done_list_name]

        # Initializes the cycle lists
        def _init_cycle_lists(self):
            """
            Initializes the lists that play a role when computing the cycle time.
            Cycle lists are stored in self.cycle_lists (list) and self.cycle_lists_dict (dict).
            """

            development_list = self.lists_dict_by_name[self.configuration.development_list_name]

            self.cycle_lists = []
            self.cycle_lists_dict = {}

            # Assumes from the development list to the end list, they all play a role in development
            add_to_cycle_list = False
            for _list in self.lists:
                if _list.id == development_list.id:
                    add_to_cycle_list = True
                if add_to_cycle_list:
                    self.cycle_lists.append(_list)
                    self.cycle_lists_dict[_list.id] = _list

            # If there is no cycle lists, assume the configuration is wrong
            if len(self.cycle_lists) <= 1:
                raise EnvironmentError(
                    u"Development list has not been configured for board {0}".format(self.board_name))

        # Fetch and initializes board card labels
        def _fetch_labels(self):
            self.labels = self.board.get_labels()
            self.labels_dict = {label.id: label for label in self.labels}

        # Initializes the cards
        def _init_cards(self):
            self.cards = self.board.all_cards()

        def _init_configuration(self, configuration):
            """
            Asserts configuration is right and initializes it lists
            :param configuration:
            :return:
            """
            self._assert_configuration(configuration)
            self._init_configuration_workflows(configuration)
            self.configuration = configuration

        # Asserts configuration looking for errors
        def _assert_configuration(self, configuration):
            # Check development list existence
            self._assert_list_existence(configuration.development_list_name)

            # Check done list existence
            self._assert_list_existence(configuration.done_list_name)

            # Check workflows
            for workflow in configuration.custom_workflows:
                for list_ in workflow.list_name_order:
                    self._assert_list_existence(list_)
                for list_ in workflow.done_list_names:
                    self._assert_list_existence(list_)

        # Check the existence of a list with a name in the board
        def _assert_list_existence(self, list_name):
            if self.lists_dict_by_name.get(list_name) is None:
                raise ValueError(u"Development list '{0}' does not exists in board {1}".format(list_name, self.board_name))

        # Initializes the configuration lists and done_lists attributes
        def _init_configuration_workflows(self, configuration):
            for workflow in configuration.custom_workflows:
                wf_configuration_lists = []
                wf_configuration_done_lists = []
                for list_ in workflow.list_name_order:
                    wf_configuration_lists.append(self.lists_dict_by_name.get(list_))
                for list_ in workflow.done_list_names:
                    wf_configuration_done_lists.append(self.lists_dict_by_name.get(list_))
                workflow.init_lists(wf_configuration_lists, wf_configuration_done_lists)