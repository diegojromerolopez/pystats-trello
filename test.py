# -*- coding: utf-8 -*-
import settings
from stats import summary
from connector import connector

if __name__ == "__main__":

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET
    client = connector.connect(api_key, api_secret, token, token_secret)

    summary.make(client, settings.TEST_BOARD)

