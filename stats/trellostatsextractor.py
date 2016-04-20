# -*- coding: utf-8 -*-
import datetime
import numpy
import re

import settings
from stats.debug import print_card
from stats.trelloboard import TrelloBoard
from stats.trellostats import TrelloStats


class TrelloStatsExtractor(TrelloBoard):

    # TrelloStatsExtractor initialization
    def __init__(self, trello_connector, configuration):
        self.configuration = configuration

        super(TrelloStatsExtractor, self).__init__(trello_connector, configuration)

        self.stats = TrelloStats(self)

    # Compute the full stats of the board.
    # That is, it computes the concrete values for each measure.
    def get_stats(self):
        # Function that checks if a card is still active
        card_is_active_function = self.configuration.card_is_active_function

        # Date filter to select only a part of card actions instead of the last 1000 actions as Trello does
        card_movements_filter = self.configuration.card_action_filter

        # Utility function that check if a card is done
        def card_is_done(_card):
            return _card.idList == self.done_list.id

        num_cards = len(self.cards)
        i = 1
        for card in self.cards:

            # Is the card done?
            card.is_done = card_is_done(card)

            # Test if the card is closed (i. e. archived)
            self.stats.update_closed_cards(card)

            # Custom filter for only considering cards we want. By default it should be "not card.closed", but we
            # give programmers the option to customize this parameter
            if card_is_active_function(card):
                print_card(card, "{0} {i} of {num_cards}".format(card.name, i=i, num_cards=num_cards))

                card.stats_by_list = card.get_stats_by_list(lists=self.lists, list_cmp=self.list_cmp, done_list=self.done_list,
                                                            tz=settings.TIMEZONE, time_unit="hours",
                                                            card_movements_filter=card_movements_filter)

                card.lead_time = None
                card.cycle_time = None

                # If the card is done, compute lead and cycle time
                if card.is_done:
                    #  Lead time (time between creation in board to reaching "Done" state)
                    card.lead_time = sum([list_stats["time"] for list_id, list_stats in card.stats_by_list.items()])

                    # Cycle time (time between development and reaching "Done" state)
                    card.cycle_time = sum(
                        [list_stats["time"] if list_id in self.cycle_lists_dict else 0 for list_id, list_stats in card.stats_by_list.items()]
                    )

                    self.stats.update_done_cards(card)

                # Add this card stats to each global stat
                for list_ in self.lists:
                    list_id = list_.id
                    card_stats_by_list = card.stats_by_list[list_id]
                    # List stats
                    self.stats.lists[list_id]["time"]["by_card"][card.id] = card_stats_by_list["time"]
                    self.stats.lists[list_id]["forward_moves"] += card_stats_by_list["forward_moves"]
                    self.stats.lists[list_id]["backward_moves"] += card_stats_by_list["backward_moves"]

                # Comments
                card.s_e = self._get_spent_estimated(card)

                # Card creation datetime
                self.stats.card_creation_datetimes.append(card.create_date)

                self.stats.active_cards[card.id] = {
                    "id": card.id,
                    "object": card,
                    "custom_workflow_times": self._get_custom_workflow_times(card),
                    "stats_by_list": card.stats_by_list,
                    "lead": card.lead_time,
                    "cycle": card.cycle_time,
                    "spent": card.s_e["spent"],
                    "estimated": card.s_e["estimated"],
                    "done": card.is_done,
                }

                # Add this card to active cards
                self.stats.active_card_list.append(card)

                # Getting the last activity in the board
                self.stats.update_board_last_activity(card)

            # Inactive cards
            else:
                self.stats.update_inactive_cards(card)

            i += 1

        return self.stats

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
        if not self.configuration.spent_estimated_time_card_comment_regex:
            return False

        comments = card.get_comments()
        spent = {"all": None, "by_member": {}}
        estimated = {"all": None, "by_member": {}}
        # For each comment, find the desired pattern and extract the spent and estimated times
        for comment in comments:
            # The spent/estimated values are in the content of each comment obeying the regex
            comment_content = comment["data"]["text"]

            matches = re.match(self.configuration.spent_estimated_time_card_comment_regex, comment_content)
            if matches:
                comment_creator_id = comment["idMemberCreator"]
                # Spent time (total and by member)
                if spent["all"] is None:
                    spent["all"] = 0
                spent["all"] += float(matches.group("spent"))
                spent["by_member"][comment_creator_id] = spent["by_member"].get(comment_creator_id, 0) + spent["by_member"].get(comment_creator_id, 0)

                # Estimated time (total and by member)
                if estimated["all"] is None:
                    estimated["all"] = 0
                estimated["all"] += float(matches.group("estimated"))
                estimated["by_member"][comment_creator_id] = estimated["by_member"].get(comment_creator_id, 0) + estimated["by_member"].get(comment_creator_id, 0)

        return {"spent": spent, "estimated": estimated}


    def _get_backward_movements_by_user(self, card):
        members_id = card.idMembers
        for member_id in members_id:
            member = self.members_dict[member_id]
