# -*- coding: utf-8 -*-
import settings
from stats import summary
from auth import connector
import sys

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(u"ERROR. Use: python stats_extractor.py <board_name>")
        exit(-1)

    board_name = sys.argv[1]

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET

    client = connector.connect(api_key, api_secret, token, token_secret)

    summary.make(client, board_name)

