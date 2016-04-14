# -*- coding: utf-8 -*-

import pygal


def get_graphics(stats, board_name, file_path=None):
    """
    Prints a chart with the average time a card is in each column.
    :param stats: statistics generated with trellostats
    :param board_name:
    :param file_path:
    :return:
    """

    if not file_path:
        file_path = u"./{0}-time-by-list.svg".format(board_name)

    time_by_list_chart = get_time_by_list_chart(board_name, stats["lists"], stats["time_by_list"])
    time_by_list_chart.render_to_file(file_path)

    return file_path


def get_time_by_list_chart(board_name, lists, time_by_list):
    # Graphic showing the average stance in each column for all cards
    chart_title = u'{0} average card list times'.format(board_name)
    line_chart = pygal.HorizontalBar(title=chart_title, legend_at_bottom=True)

    i = 1
    for list_id, list_ in lists.items():
        list_name = list_.name.decode("utf-8")
        line_chart.add(list_name, time_by_list["avg"][list_.id])
        i += 1
    return line_chart

