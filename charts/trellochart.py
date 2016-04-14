# -*- coding: utf-8 -*-

import pygal

from stats import get_stats


def get_graphics(board_name):
    stats = get_stats(board_name)

    time_by_list_chart = get_time_by_list_chart(board_name, stats["lists"], stats["time_by_list"])
    time_by_list_chart.render_to_file(u"./out/{0}-time-by-list.svg".format(board_name))


def get_time_by_list_chart(board_name, lists, time_by_list):
    # Graphic showing the average stance in each column for all cards
    chart_title = u'Tiempo transcurrido en cada columna del tablero Kanban {0}'.format(board_name)
    line_chart = pygal.HorizontalBar(title=chart_title, legend_at_bottom=True)

    i = 1
    for list_id, list_ in lists.items():
        list_name = list_.name.decode("utf-8")
        line_chart.add(list_name, time_by_list["avg"][list_.id])
        i += 1
    return line_chart

