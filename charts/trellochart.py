# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import pygal
import settings
from slugify import slugify

def _get_chart_path(chart_type, configuration):
    board_name = configuration.board_name
    now_str = datetime.datetime.now(settings.TIMEZONE).strftime("%Y_%m_%d_%H_%M_%S")
    file_path = u"{0}/{1}-{2}-{3}.png".format(configuration.output_dir, slugify(board_name), chart_type, now_str)
    return file_path


def get_graphics(stats, configuration):
    """
    Prints a chart with the average time a card is in each column.
    :param stats: statistics generated with trellostats
    :param configuration: configuration of the board
    :return:
    """

    lists = stats["lists"]

    board_name = configuration.board_name

    # Time by list
    chart_title = u"Average time for all board cards by list for {0}".format(board_name)
    time_by_list_chart_ = avg_by_list_chart(chart_title, lists, stats, "time_by_list")
    time_chart_file_path = _get_chart_path(u"time_by_list", configuration)
    time_by_list_chart_.render_to_png(time_chart_file_path)

    # Forward by list
    chart_title = u"Number of times a list is the source of a card forward movement in {0}".format(board_name)
    forward_by_list_chart_ = number_by_list_chart(chart_title, lists, stats, "forward_movements_by_list")
    forward_file_path = _get_chart_path(u"forward_movements_by_list", configuration)
    forward_by_list_chart_.render_to_png(forward_file_path)

    # Backwards by list
    chart_title = u"Number of times a list is the source of a card movement to backwards in {0}".format(board_name)
    backward_by_list_chart_ = number_by_list_chart(chart_title, lists, stats, "backward_movements_by_list")
    backward_file_path = _get_chart_path(u"backward_movements_by_list", configuration)
    backward_by_list_chart_.render_to_png(backward_file_path)

    return {
        "time": {"object":time_by_list_chart_,"path": time_chart_file_path},
        "forward": {"object": forward_by_list_chart_, "path": forward_file_path},
        "backward": {"object": backward_by_list_chart_, "path": backward_file_path}
    }


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