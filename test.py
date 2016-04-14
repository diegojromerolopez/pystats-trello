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

    stats = trellostats.get_stats(client, board_name=settings.TEST_BOARD)

    print(u"Cycle")
    print(u"avg: {0}, std_dev: {1}".format(stats["cycle_time"]["avg"], stats["cycle_time"]["std_dev"]))

    print(u"Lead")
    print(u"avg: {0}, std_dev: {1}".format(stats["lead_time"]["avg"], stats["lead_time"]["std_dev"]))

    file_path = trellochart.get_graphics(stats, board_name=settings.TEST_BOARD)
    print(u"Chart with average card time in each list created in {0}".format(file_path))
