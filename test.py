# -*- coding: utf-8 -*-
import settings
from charts import trellochart
from stats import trellostats
from connector import connect

if __name__ == "__main__":

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET
    client = connect(api_key, api_secret, token, token_secret)

    stats = trellostats.get_stats(client, board_name=u"Tareas CDR")

    trellochart.get_graphics(stats, board_name=u"Tareas CDR")
