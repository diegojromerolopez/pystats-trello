# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import pygal
import settings


def _get_chart_path(chart_type, board_name):
    now_str = datetime.datetime.now(settings.TIMEZONE).strftime("%Y_%m_%d_%H_%M_%S")
    return u"./{0}/{1}-{2}-{3}.png".format(settings.OUTPUT_DIR, board_name, chart_type, now_str)


def get_graphics(stats, board_name):
    """
    Prints a chart with the average time a card is in each column.
    :param stats: statistics generated with trellostats
    :param board_name: name of the board
    :return:
    """

    lists = stats["lists"]

    # Time by list
    chart_title = u"Average time for all board cards by list for {0}".format(board_name)
    time_by_list_chart_ = avg_by_list_chart(chart_title, lists, stats, "time_by_list")
    file_path = _get_chart_path(u"time_by_list", board_name)
    time_by_list_chart_.render_to_png(file_path)

    # Forward by list
    chart_title = u"Number of times a list is the source of a card forward movement in {0}".format(board_name)
    forward_by_list_chart_ = number_by_list_chart(chart_title, lists, stats, "forward_movements_by_list")
    file_path = _get_chart_path(u"forward_movements_by_list", board_name)
    forward_by_list_chart_.render_to_png(file_path)

    # Backwards by list
    chart_title = u"Number of times a list is the source of a card movement to backwards in {0}".format(board_name)
    backward_by_list_chart_ = number_by_list_chart(chart_title, lists, stats, "backward_movements_by_list")
    file_path = _get_chart_path(u"backward_movements_by_list", board_name)
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