# -*- coding: utf-8 -*-
import settings
from auth.connector import TrelloConnector
from stats import summary
from auth import connector
import sys

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(u"ERROR. Use: python stats_extractor.py <board_name> [since] [before]")
        print(u"- <board_name> is the board name you want to extract stats to.")
        print(u"- [since] and [before] are optional and are the date limits to get movements in that interval.")
        exit(-1)

    board_name = sys.argv[1]

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET

    trello_connector = TrelloConnector(api_key, api_secret, token, token_secret)

    card_movements_filter = None
    if len(sys.argv) == 4:
        card_movements_filter = [sys.argv[2], sys.argv[3]]
    elif len(sys.argv) == 3:
        card_movements_filter = [sys.argv[2], None]

    summary.make(trello_connector, board_name, card_movements_filter)

