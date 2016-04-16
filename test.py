# -*- coding: utf-8 -*-

import settings
from auth.connector import TrelloConnector
from stats import summary

if __name__ == "__main__":

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET

    trello_connector = TrelloConnector(api_key, api_secret, token, token_secret)

    summary.make(trello_connector, settings.TEST_BOARD)

