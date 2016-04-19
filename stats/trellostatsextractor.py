# -*- coding: utf-8 -*-
import datetime
import numpy
import re

import settings
from stats.debug import print_card
from stats.trelloboard import TrelloBoard


class TrelloStatsExtractor(TrelloBoard):

    def __init__(self, trello_connector, configuration):
        self.configuration = configuration
        super(TrelloStatsExtractor, self).__init__(trello_connector, configuration)

    # Computes the statistics of the cards.
    # Computes mean and standard deviation for metrics time by list, lead_time and Cycle time.
    # The other metrics are absolute values.
    def get_stats(self):

        def add_statistic_summary(value_list):
            return {"values": value_list, "avg": numpy.mean(value_list), "std_dev": numpy.std(value_list, axis=0)}

        def statistic_summary_by_list(stat_by_list):
            stats_summary_by_list = {}
            for list_name_, list_times_ in stat_by_list.items():
                stats_summary_by_list[list_name_] = add_statistic_summary(list_times_)

            return stats_summary_by_list

        stats = self.get_full_stats()

        # Change the values for its mean and standard deviation
        stats.update(
            {
                "time_by_list": statistic_summary_by_list(stats["time_by_list"]),
            }
        )

        return stats

    # Compute the full stats of the board.
    # That is, it computes the concrete values for each measure.
    def get_full_stats(self):
        # Function that checks if a card is still active
        card_is_active_function = self.configuration.card_is_active_function

        # Date filter to select only a part of card actions instead of the last 1000 actions as Trello does
        card_movements_filter = self.configuration.card_action_filter

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

                # Compute custom workflows (if needed)
                card.custom_workflow_times = self._get_custom_workflow_times(card)

                # Add this card to active cards
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

    # Get specific workflow times
    def _get_custom_workflow_times(self, card):
        # If there is no custom workflows or this board has no custom workflows, there is no custom workflow times
        # for this card
        if not self.has_custom_workflows():
            return None

        workflows = self.get_custom_workflows()

        card_times_by_workflow = {}
        for custom_workflow in workflows:
            custom_workflow_id = custom_workflow.name
            card_times_by_workflow[custom_workflow_id] = 0

            # If this card is not in one of the lists that have the role of "done" lists, it is not possible to
            # compute this workflow time
            card_list_name = self.lists_dict[card.idList].name.decode("utf-8")
            if not card_list_name in custom_workflow.done_list_names:
                card_times_by_workflow[custom_workflow_id] = None
                continue

            # Sum of the times of each custom workflow list this card has been
            for list_name in custom_workflow.list_name_order:
                list_ = self.lists_dict_by_name[list_name]
                card_times_by_workflow[custom_workflow_id] += card.stats_by_list[list_.id]["time"]

        # Return all the custom workflow times
        return card_times_by_workflow

    def has_custom_workflows(self):
        return len(self.configuration.custom_workflows) > 0

    def get_custom_workflows(self):
        if self.has_custom_workflows():
            return self.configuration.custom_workflows
        return False

    # Gets the spent and estimated times for this card
    # Plugins like Plus for Trello are able to store estimated duration of the task and actual spent time in comments.
    # This plugins has a format (plus! <spent>/<estimated> in case of Plus for Trello) and this format can be defined
    # in settings local by the use of a regular expression.
    def _get_spent_estimated(self, card):
        # If there is no defined regex with the format of spent/estimated comment in cards, don't fetch comments
        if self.configuration.spent_estimated_time_card_comment_regex:
            return False

        comments = card.get_comments()
        spent = None
        estimated = None
        # For each comment, find the desired pattern and extract the spent and estimated times
        for comment in comments:
            comment_content = comment["data"]["text"]
            matches = re.match(self.configuration.spent_estimated_time_card_comment_regex, comment_content)
            if matches:
                if spent is None:
                    spent = 0
                spent += float(matches.group("spent"))
                if estimated is None:
                    estimated = 0
                estimated += float(matches.group("estimated"))
        return {"spent": spent, "estimated": estimated}
