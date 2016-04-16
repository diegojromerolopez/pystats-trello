# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pygal
import settings


def get_graphics(stats, board_name):
    """
    Prints a chart with the average time a card is in each column.
    :param stats: statistics generated with trellostats
    :param board_name:
    :param file_path:
    :return:
    """

    lists = stats["lists"]

    # Time by list
    chart_title = u"Average time in each list for {0}".format(board_name)
    time_by_list_chart_ = avg_by_list_chart(chart_title, lists, stats, "time_by_list")
    file_path = u"./{0}/{1}-time_by_list.png".format(settings.OUTPUT_DIR, board_name)
    time_by_list_chart_.render_to_png(file_path)

    # Forward by list
    chart_title = u"Number of times a list is the source of a card forward movement in {0}".format(board_name)
    forward_by_list_chart_ = number_by_list_chart(chart_title, lists, stats, "forward_movements_by_list")
    file_path = u"./{0}/{1}-forward_movements_by_list.png".format(settings.OUTPUT_DIR, board_name)
    forward_by_list_chart_.render_to_png(file_path)

    # Backwards by list
    chart_title = u"Number of times a list is the source of a card movement to backwards in {0}".format(board_name)
    backward_by_list_chart_ = number_by_list_chart(chart_title, lists, stats, "backward_movements_by_list")
    file_path = u"./{0}/{1}-backward_movements_by_list.png".format(settings.OUTPUT_DIR, board_name)
    backward_by_list_chart_.render_to_png(file_path)

    return {"time": time_by_list_chart_, "forward":forward_by_list_chart_, "backward":backward_by_list_chart_}


def avg_by_list_chart(chart_title, lists, stats, measurement):
    line_chart = pygal.HorizontalBar(title=chart_title, legend_at_bottom=True)

    i = 1
    for list_ in lists:
        list_name = list_.name.decode("utf-8")
        line_chart.add(list_name, stats[measurement][list_.id]["avg"])
        i += 1
    return line_chart


def number_by_list_chart(chart_title, lists, stats, measurement):
    line_chart = pygal.HorizontalBar(title=chart_title, legend_at_bottom=True)

    i = 1
    for list_ in lists:
        list_name = list_.name.decode("utf-8")
        line_chart.add(list_name, stats[measurement][list_.id])
        i += 1
    return line_chart