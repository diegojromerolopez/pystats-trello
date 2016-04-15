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

    print("-------------------------------------------------------")
    print(u"Measurements for {0}".format(settings.TEST_BOARD))

    # Average time in each column for all the cards
    print(u"Average time in each column for all the board cards")
    for list_ in stats["lists"]:
        list_name = list_.name.decode("utf-8")
        avg_list_time = stats["time_by_list"]["avg"][list_.id]
        std_dev_list_time = stats["time_by_list"]["std_dev"][list_.id]
        print(u"- {0}: {1} h (std. dev. {2})".format(list_name, avg_list_time, std_dev_list_time))

    print("-------------------------------------------------------")

    # Cycle time
    print(u"Cycle")
    print(u"avg: {0} h, std_dev: {1}".format(stats["cycle_time"]["avg"], stats["cycle_time"]["std_dev"]))

    print(u"Lead")
    print(u"avg: {0} h, std_dev: {1}".format(stats["lead_time"]["avg"], stats["lead_time"]["std_dev"]))

    # Chart with times for all cards in each column
    file_path = trellochart.get_graphics(stats, board_name=settings.TEST_BOARD)

    print("-------------------------------------------------------")
    print(u"Chart with average card time in each list created in {0}".format(file_path))
