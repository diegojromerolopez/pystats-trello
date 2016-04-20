# -*- coding: utf-8 -*-
import datetime
import numpy

import settings


class TrelloStats(object):

    def __init__(self, trelloboard):
        self.trello_board = trelloboard

        # List dict with the stats by list
        self.lists = {list_.id: {"time": {"by_card":{}, "avg":0, "std_dev":0}, "forward_moves": 0, "backward_moves":0} for list_ in self.trello_board.lists}

        # Active cards by our definition given by the lambda function
        self.active_cards = {}

        self.active_card_list = []

        # Cards that are not active
        self.inactive_cards = {"all": [], "done": []}

        # Closed cards
        self.closed_cards = {"all": [], "done": []}

        # Done cards
        self.done_cards = []

        # We store card_creation_datetimes to extract min and max datetime
        self.card_creation_datetimes = []
        self.first_card_creation_datetime = None
        self.last_card_creation_datetime = None

        # Last activity of the board
        self.board_last_activity = None

        # Time of life of the board
        self.board_life_time = None


    def get(self):
        now = datetime.datetime.now(settings.TIMEZONE)

        # Min and max card creation datetimes
        self.first_card_creation_datetime = min(self.card_creation_datetimes)
        self.last_card_creation_datetime = max(self.card_creation_datetimes)
        self.board_life_time = (self.board_last_activity - self.first_card_creation_datetime).total_seconds()

        cycle_times = self._get_card_property_list("cycle")
        lead_times = self._get_card_property_list("lead")

        last_card_creation_seconds_ago = (now - self.last_card_creation_datetime).total_seconds()

        for list_ in self.trello_board.lists:
            self.lists[list_.id]["object"] = list_
            self.lists[list_.id]["time"]["avg"] = numpy.mean(self.lists[list_.id]["time"]["by_card"].values())
            self.lists[list_.id]["time"]["std_dev"] = numpy.std(self.lists[list_.id]["time"]["by_card"].values(), axis=0)

        stats = {
            "board_lists": self.trello_board.lists,
            "lists": self.lists,
            "cards": self.trello_board.cards,
            "num_cards": len(self.trello_board.cards),
            "active_cards": self.active_cards,
            "num_active_cards": len(self.active_cards.keys()),
            "inactive_cards": self.inactive_cards,
            "num_inactive_cards": len(self.inactive_cards.keys()),
            "closed_cards": self.closed_cards,
            "done_cards": {
                "list": self.done_cards,
                "count": len(self.done_cards),
                "per_hour": len(self.done_cards) / (self.board_life_time / 60.0),
                "per_day": len(self.done_cards) / (self.board_life_time / 3600.0)
            },
            "board_life_time": self.board_life_time / 60.0,
            "board_last_activity": self.board_last_activity,
            "last_card_creation": {
                "absolute": self.last_card_creation_datetime,
                "seconds_ago": last_card_creation_seconds_ago,
                "hours_ago": last_card_creation_seconds_ago/3600.0,
                "days_ago": (last_card_creation_seconds_ago/3600.0)/24.0
            },
            "lead_time": {
                "dict": {card.id : card.lead_time for card in self.done_cards},
                "values": lead_times,
                "avg": numpy.mean(lead_times),
                "std_dev": numpy.std(lead_times, axis=0)
            },
            "cycle_time": {
                "dict": {card.id: card.cycle_time for card in self.done_cards},
                "values": cycle_times,
                "avg": numpy.mean(cycle_times),
                "std_dev": numpy.std(cycle_times, axis=0)
            },
        }
        return stats

    # Updates the last board activity according to the date of last activity of the card
    def update_board_last_activity(self, card):
        if self.board_last_activity is None or self.board_last_activity < card.date_last_activity:
            self.board_last_activity = card.date_last_activity

    def update_done_cards(self, card):
        if card.is_done:
            self.done_cards.append(card)

    # Closed cards are defined
    def update_closed_cards(self, card):
        # Test if the card is closed
        if card.closed:
            self.closed_cards["all"].append(card)
            # If the card is closed, test if was closed in the "done" list
            if card.is_done:
                self.closed_cards["done"].append(card)

    # Update inactive cards
    # Inactive cards are determined by the card_is_active function of the configuration file
    def update_inactive_cards(self, card):
        self.inactive_cards["all"].append(card)
        if card.is_done:
            self.inactive_cards["done"].append(card)

    # Returns a list with the values of a property of all the active cards
    def _get_card_property_list(self, prop, include_none=False):
        prop_values = []
        for card, card_properties in self.active_cards.items():
            if include_none or not card_properties[prop] is None:
                prop_values.append(card_properties[prop])
        return prop_values