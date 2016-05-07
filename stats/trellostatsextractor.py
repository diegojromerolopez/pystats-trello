# -*- coding: utf-8 -*-
import datetime
import numpy
import re
import dateutil.parser

import settings
from stats.debug import print_card
from stats.trelloboard import TrelloBoard

# Extract stats from a board
class TrelloStatsExtractor(TrelloBoard):

    def __init__(self, trello_connector, configuration):
        self.configuration = configuration
        super(TrelloStatsExtractor, self).__init__(trello_connector, configuration)

        # Active cards by our definition given by the lambda function
        self.active_cards = []

        # Cards that are not active
        self.inactive_cards = []
        self.done_inactive_cards = []

        # Closed cards
        self.closed_cards = []

        # Closed done cards
        self.closed_done_cards = []

        # Done cards
        self.done_cards = []

        # Spent time by period of time by user
        self.spent_month_time_by_user = {member.id: {} for member in self.members}
        self.spent_week_time_by_user = {member.id: {} for member in self.members}

        # Estimated time by period of time by user
        self.estimated_month_time_by_user = {member.id: {} for member in self.members}
        self.estimated_week_time_by_user = {member.id: {} for member in self.members}

        # Cards by period of time by label
        self.cards_by_creation_month_by_label = {}
        self.cards_by_creation_week_by_label = {}

        # Each one of the time of each card in each list
        self.time_by_list = {list_.id: [] for list_ in self.lists}

        # Forward or backward movements
        self.forward_movements_by_list = {list_.id: 0 for list_ in self.lists}
        self.backward_movements_by_list = {list_.id: 0 for list_ in self.lists}
        self.movements_by_member = {member.id: {"username": member.username, "forward": 0, "backward": 0} for member in self.members}

        # Cycle and lead times by card
        self.cycle_time = {}
        self.lead_time = {}

        self.last_card_creation_datetime = None
        self.first_card_creation_datetime = None

        # Time this board has been alive
        self.board_life_time = None

        # Board last activity to computer board life time
        self.board_last_activity = None

    # Compute the full stats of the board.
    # That is, it computes the concrete values for each measure.
    # and returns a series of useful stats additional to the concrete values stored in this object
    def get_stats(self):
        # Function that checks if a card is still active
        card_is_active_function = self.configuration.card_is_active_function

        # Date filter to select only a part of card actions instead of the last 1000 actions as Trello does
        card_movements_filter = self.configuration.card_action_filter

        # Utility function that check if a card is done
        def card_is_done(_card):
            return _card.idList == self.done_list.id

        # We store card_creation_datetimes to extract min datetime
        card_creation_datetimes = []

        num_cards = len(self.cards)
        i = 1
        for card in self.cards:

            # Test if the card is closed
            if card.closed:
                self.closed_cards.append(card)
                # If the card is closed, test if was closed in the "done" list
                if card_is_done(card):
                    self.closed_done_cards.append(card)

            # Custom filter for only considering cards we want. By default it should be "not card.closed", but we
            # give programmers the option to customize this parameter
            if card_is_active_function(card):
                print_card(card, "{0} {i} of {num_cards}".format(card.name, i=i, num_cards=num_cards))
                card.stats_by_list = card.get_stats_by_list(lists=self.lists, list_cmp=self.list_cmp, done_list=self.done_list,
                                                            time_unit="hours", card_movements_filter=card_movements_filter)

                # If the card is done, compute lead and cycle time
                if card_is_done(card):
                    #  Lead time (time between creation in board to reaching "Done" state)
                    card.lead_time = sum([list_stats["time"] for list_id, list_stats in card.stats_by_list.items()])
                    self.lead_time[card.id] = card.lead_time
                    # Cycle time (time between development and reaching "Done" state)
                    card.cycle_time = sum(
                        [list_stats["time"] if list_id in self.cycle_lists_dict else 0 for list_id, list_stats in card.stats_by_list.items()]
                    )
                    self.cycle_time[card.id] = card.cycle_time
                    self.done_cards.append(card)

                # Add this card stats to each global stat
                for list_ in self.lists:
                    list_id = list_.id
                    card_stats_by_list = card.stats_by_list[list_id]
                    self.time_by_list[list_id].append(card_stats_by_list["time"])
                    self.forward_movements_by_list[list_id] += card_stats_by_list["forward_moves"]
                    self.backward_movements_by_list[list_id] += card_stats_by_list["backward_moves"]

                # Forward and backward movements by member of the card
                card_forward_movements = sum([list_stats["forward_moves"] for list_id, list_stats in card.stats_by_list.items()])
                card_backward_movements = sum([list_stats["backward_moves"] for list_id, list_stats in card.stats_by_list.items()])
                for idMember in card.member_ids:
                    self.movements_by_member[idMember]["backward"] += card_backward_movements
                    self.movements_by_member[idMember]["forward"] += card_forward_movements

                # Comments S/E
                card.s_e = self._get_spent_estimated(card)

                # Categorizing the card according to its creation datetime and labels
                self._categorize_card_by_label_period_of_time(card)

                # Card creation datetime
                card_creation_datetimes.append(card.create_date)

                # Getting the last activity in the board
                if self.board_last_activity is None or self.board_last_activity < card.date_last_activity:
                    self.board_last_activity = card.date_last_activity

                # Compute custom workflows (if needed)
                card.custom_workflow_times = self._get_custom_workflow_times(card)

                # Add this card to active cards
                self.active_cards.append(card)

            # Inactive cards
            else:
                self.inactive_cards.append(card)
                if card_is_done(card):
                    self.done_inactive_cards.append(card)

            i += 1

        now = datetime.datetime.now(settings.TIMEZONE)
        self.first_card_creation_datetime = min(card_creation_datetimes)
        self.last_card_creation_datetime = max(card_creation_datetimes)
        self.board_life_time = (self.board_last_activity - self.first_card_creation_datetime).total_seconds()

        stats = {
            "lists": self.lists,
            "cards": self.cards,
            "active_card_stats_by_list": {card.id: card.stats_by_list for card in self.active_cards},
            "active_card_spent_estimated_times": {card.id: card.s_e for card in self.active_cards},
            "active_cards": self.active_cards,
            "done_inactive_cards": self.done_inactive_cards,
            "inactive_cards": self.inactive_cards,
            "closed_cards": self.closed_cards,
            "closed_done_cards": self.closed_done_cards,
            "done_cards": self.done_cards,
            "done_cards_per_hour": len(self.done_cards) / (self.board_life_time/60.0),
            "done_cards_per_day": len(self.done_cards)/(self.board_life_time/3600.0),
            "board_life_time": self.board_life_time / 60.0,
            "board_last_activity": self.board_last_activity,
            "last_card_creation": self.last_card_creation_datetime,
            "last_card_creation_ago": (now - self.last_card_creation_datetime).total_seconds(),
            "time_by_list": self._get_time_summary_by_list(),
            "backward_movements_by_list": self.backward_movements_by_list,
            "movements_by_user": self.movements_by_member,
            "forward_movements_by_list": self.forward_movements_by_list,
            "lead_time": {
                "values": self.lead_time,
                "avg": numpy.mean(self.lead_time.values()),
                "std_dev": numpy.std(self.lead_time.values(), axis=0)
            },
            "cycle_time": {
                "values": self.cycle_time,
                "avg": numpy.mean(self.cycle_time.values()),
                "std_dev": numpy.std(self.cycle_time.values(), axis=0)
            },
        }
        return stats

    # Get a summary of the time each task has been in each list
    def _get_time_summary_by_list(self):
        def add_statistic_summary(value_list):
            return {"values": value_list, "avg": numpy.mean(value_list), "std_dev": numpy.std(value_list, axis=0)}

        def statistic_summary_by_list(stat_by_list):
            stats_summary_by_list = {}
            for list_name_, list_times_ in stat_by_list.items():
                stats_summary_by_list[list_name_] = add_statistic_summary(list_times_)

            return stats_summary_by_list

        return statistic_summary_by_list(self.time_by_list)

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
            return {"spent": None, "estimated": None}

        times = {"total": {"spent": None, "estimated": None}, "by_user": {}}

        comments = card.get_comments()
        total_spent = None
        total_estimated = None
        # For each comment, find the desired pattern and extract the spent and estimated times
        for comment in comments:
            comment_content = comment["data"]["text"]
            matches = re.match(self.configuration.spent_estimated_time_card_comment_regex, comment_content)
            if matches:
                # Comment creator
                comment_creator_id = comment["idMemberCreator"]
                if comment_creator_id not in times["by_user"]:
                    times["by_user"][comment_creator_id] = {
                        "total": {"spent": 0, "estimated": 0},
                        "by_month": {},
                        "by_week": {},
                        "by_day": {}
                    }

                # Add to total spent
                if total_spent is None:
                    total_spent = 0
                spent = float(matches.group("spent"))
                total_spent += spent

                # Add to total estimated
                if total_estimated is None:
                    total_estimated = 0
                estimated = float(matches.group("estimated"))
                total_estimated += estimated

                # Comment iso timestamp conversion to datetime
                comment_creation_iso_timestamp = comment["date"]
                comment_creation_datetime = dateutil.parser.parse(comment_creation_iso_timestamp)
                comment_creation_date = comment_creation_datetime.date()

                # Spent/Estimated by month
                month = comment_creation_date.strftime("%Y-M%m")
                if month not in times["by_user"][comment_creator_id]["by_month"]:
                    times["by_user"][comment_creator_id]["by_month"][month] = {"spent": 0, "estimated": 0}

                # Spent by month
                times["by_user"][comment_creator_id]["by_month"][month]["spent"] += spent
                if month not in self.spent_month_time_by_user[comment_creator_id]:
                    self.spent_month_time_by_user[comment_creator_id][month] = 0
                self.spent_month_time_by_user[comment_creator_id][month] += spent

                # Estimated by month
                times["by_user"][comment_creator_id]["by_month"][month]["estimated"] += estimated
                if month not in self.estimated_month_time_by_user[comment_creator_id]:
                    self.estimated_month_time_by_user[comment_creator_id][month] = 0
                self.estimated_month_time_by_user[comment_creator_id][month] += estimated

                # Spent/Estimated by week of year
                week_number = "{0}-W{1}".format(comment_creation_date.year, comment_creation_date.isocalendar()[1])
                if week_number not in times["by_user"][comment_creator_id]["by_week"]:
                    date_week_starts = datetime.datetime.strptime(week_number + '-0', "%Y-W%W-%w")
                    times["by_user"][comment_creator_id]["by_week"][week_number] = {"week_starts_at": date_week_starts.strftime("%Y-%m-%d"), "spent": 0, "estimated": 0}

                # Spent by week of year
                times["by_user"][comment_creator_id]["by_week"][week_number]["spent"] += spent
                if week_number not in self.spent_week_time_by_user[comment_creator_id]:
                    self.spent_week_time_by_user[comment_creator_id][week_number] = 0
                self.spent_week_time_by_user[comment_creator_id][week_number] += spent

                times["by_user"][comment_creator_id]["by_week"][week_number]["estimated"] += estimated
                # Estimated by week of year
                if week_number not in self.estimated_week_time_by_user[comment_creator_id]:
                    self.estimated_week_time_by_user[comment_creator_id][week_number] = 0
                self.estimated_week_time_by_user[comment_creator_id][week_number] += estimated

                # Spent/Estimated by day of year
                yyyymmdd = comment_creation_date.strftime("%Y-%m-%d")
                if yyyymmdd not in times["by_user"][comment_creator_id]["by_day"]:
                    times["by_user"][comment_creator_id]["by_day"][yyyymmdd] = {"spent": 0, "estimated": 0}
                times["by_user"][comment_creator_id]["by_day"][yyyymmdd]["spent"] += spent
                times["by_user"][comment_creator_id]["by_day"][yyyymmdd]["estimated"] += estimated

        times["total"] = {"spent": total_spent, "estimated": total_estimated}

        return times

    # Categorize this card by period of creation time and each one of its labels
    def _categorize_card_by_label_period_of_time(self, card):
        creation_datetime = card.create_date
        month = creation_datetime.strftime("%Y-M%m")
        week_number = "{0}-W{1}".format(creation_datetime.year, creation_datetime.isocalendar()[1])

        if month not in self.cards_by_creation_month_by_label:
            self.cards_by_creation_month_by_label[month] = {}

        if week_number not in self.cards_by_creation_week_by_label:
            self.cards_by_creation_week_by_label[week_number] = {}

        # For each label we categorize this card in each one of its label and month and week number
        for label_id in card.label_ids:

            # Categorizing the card to its label and month
            if label_id not in self.cards_by_creation_month_by_label[month]:
                self.cards_by_creation_month_by_label[month][label_id] = []
            self.cards_by_creation_month_by_label[month][label_id].append(card)

            # Categorizing the card to its label and week number
            if label_id not in self.cards_by_creation_week_by_label[week_number]:
                self.cards_by_creation_week_by_label[week_number][label_id] = []
            self.cards_by_creation_week_by_label[week_number][label_id].append(card)


