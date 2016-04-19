# -*- coding: utf-8 -*-
import sys

import settings
from auth.connector import TrelloConnector
from stats import summary
import datetime

from stats.trelloboardconfiguration import TrelloBoardConfiguration

if __name__ == "__main__":

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET

    trello_connector = TrelloConnector(api_key, api_secret, token, token_secret)

    if len(sys.argv) < 2:
        raise ValueError(u"Error. Use python test.py <configuration_file_path>")

    configuration = TrelloBoardConfiguration.load_from_file(sys.argv[1])

    summary.make(trello_connector, configuration)

