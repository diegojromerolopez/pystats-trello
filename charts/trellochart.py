# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import pygal
import settings
from slugify import slugify


def get_graphics(stats, stat_extractor):
    """
    Prints a chart with the average time a card is in each column.
    :param stats: statistics generated with trellostats
    :param configuration: configuration of the board
    :return:
    """

    lists = stats["lists"]

    configuration = stat_extractor.configuration
    board_name = configuration.board_name
    if configuration.censored:
        board_name = stat_extractor.board.id

    # Time by list
    chart_title = u"Average time for all board cards by list for {0}".format(board_name)
    time_by_list_chart_ = avg_by_list_chart(chart_title, lists, stats, "time_by_list")
    time_chart_file_path = _get_chart_path(u"time_by_list", configuration)
    time_by_list_chart_.render_to_png(time_chart_file_path)

    # Time by list in custom workflow context
    if stat_extractor.has_custom_workflows():
        for custom_workflow in stat_extractor.get_custom_workflows():
            chart_title = u"Average time for all board cards by list for custom workflow {0} of {1}".format(custom_workflow.name, board_name)
            wf_i_lists = custom_workflow.lists
            wf_i_time_by_list_chart_ = avg_by_list_chart(chart_title, wf_i_lists, stats, "time_by_list")
            wf_i_time_chart_file_path = _get_chart_path(u"wf_time_by_list_{0}".format(custom_workflow.name), configuration)
            wf_i_time_by_list_chart_.render_to_png(wf_i_time_chart_file_path)


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

    # Forwards - Backwards per user
    chart_title = u"Forwarded - Pushed back tasks per user {0}".format(board_name)
    mov_difference_by_user_file_path = _get_chart_path(u"diff_movements_by_user", configuration)
    mov_difference_by_user_chart = member_chart(chart_title, stat_extractor, mov_difference_by_user_file_path, stats["movements_by_user"], stat_extractor.members, key="difference")

    # Forwards per user
    chart_title = u"Forward movement on tasks per user {0}".format(board_name)
    forwarded_by_user_file_path = _get_chart_path(u"forward_movements_by_user", configuration)
    forwarded_by_user_chart = member_chart(chart_title, stat_extractor, forwarded_by_user_file_path, stats["movements_by_user"], stat_extractor.members,
                 key="forward")

    # Backwards per user
    chart_title = u"Backward movements on tasks per user {0}".format(board_name)
    backwarded_by_user_file_path = _get_chart_path(u"backward_movements_by_user", configuration)
    backwarded_by_user_file_chart = member_chart(chart_title, stat_extractor, backwarded_by_user_file_path, stats["movements_by_user"], stat_extractor.members,
                 key="backward")

    # Spent/Estimated time per user per month
    monthly_chart_title = u"Spent time per month per user {0}".format(board_name)
    spent_estimated_time_chart_by_user(monthly_chart_title, stat_extractor, file_path=_get_chart_path("monthly_spent_times_by_user", configuration), period="month", measure="spent")
    monthly_chart_title = u"Estimated time per month per user {0}".format(board_name)
    spent_estimated_time_chart_by_user(monthly_chart_title, stat_extractor,
                                       file_path=_get_chart_path("monthly_estimated_times_by_user",
                                                                 configuration), period="month", measure="estimated")
    monthly_chart_title = u"Estimated - Spent time per month per user {0}".format(board_name)
    spent_estimated_time_chart_by_user(monthly_chart_title, stat_extractor,
                                       file_path=_get_chart_path("monthly_diff_times_by_user",
                                                                 configuration), period="month", measure="diff")

    # Spent/Estimated time per user per week
    weekly_chart_title = u"Spent time per week per user {0}".format(board_name)
    spent_estimated_time_chart_by_user(weekly_chart_title, stat_extractor, file_path=_get_chart_path("weekly_spent_times_by_user", configuration), period="week", measure="spent")
    weekly_chart_title = u"Estimated time per week per user {0}".format(board_name)
    spent_estimated_time_chart_by_user(weekly_chart_title, stat_extractor, file_path=_get_chart_path("weekly_estimated_times_by_user", configuration), period="week", measure="estimated")
    weekly_chart_title = u"Estimated - Spent time per week per user {0}".format(board_name)
    spent_estimated_time_chart_by_user(weekly_chart_title, stat_extractor,
                                       file_path=_get_chart_path("weekly_diff_times_by_user", configuration),
                                       period="week", measure="diff")

    return {
        "time": {"object":time_by_list_chart_,"path": time_chart_file_path},
        "forward": {"object": forward_by_list_chart_, "path": forward_file_path},
        "backward": {"object": backward_by_list_chart_, "path": backward_file_path},
        "forward_movements_by_user": {"object": forwarded_by_user_chart, "path": forwarded_by_user_file_path},
        "backward_movements_by_user": {"object": backwarded_by_user_file_chart, "path": backwarded_by_user_file_path},
        "difference_movements_by_user": {"object": mov_difference_by_user_chart, "path": mov_difference_by_user_file_path}
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


def member_chart(chart_title, stat_extractor, file_path, stats_by_member, members, key="forward"):
    by_user_chart_ = pygal.HorizontalBar(title=chart_title, legend_at_bottom=True)
    for member in members:
        member_name = member.username.decode("utf-8")
        if not member.id in stats_by_member:
            stats_by_member[member.id] = {"forward": 0, "backward": 0.}

        if key == "difference":
            value = stats_by_member[member.id]["forward"] - stats_by_member[member.id]["backward"]
        else:
            value = stats_by_member[member.id][key]

        # Allow possibility to censure username
        member_chart_name = member_name
        if stat_extractor.configuration.censored:
            member_chart_name = member.id

        by_user_chart_.add(u"{0}".format(member_chart_name), value)

    by_user_chart_.render_to_png(file_path)
    return by_user_chart_


def spent_estimated_time_chart_by_user(chart_title, stat_extractor, file_path, period="month", measure="spent"):
    """
    Creates a chart that shows spent and estimated (in that order) times by user.
    :param chart_title:
    :param stat_extractor:
    :param file_path:
    :param period:
    :param measure:
    :return:
    """
    spent_time_by_user = None
    estimated_time_by_user = None
    if period == "month":
        spent_time_by_user = stat_extractor.spent_month_time_by_user
        estimated_time_by_user = stat_extractor.estimated_month_time_by_user
    elif period == "week":
        spent_time_by_user = stat_extractor.spent_week_time_by_user
        estimated_time_by_user = stat_extractor.estimated_week_time_by_user

    # Calculation of the x-labels
    periods = {}
    for member in stat_extractor.members:
        periods.update(spent_time_by_user.get(member.id))
        periods.update(estimated_time_by_user.get(member.id))
    periods = periods.keys()
    periods.sort()

    s_e_by_user_chart_ = pygal.Line(title=chart_title, legend_at_bottom=False)
    for member in stat_extractor.members:
        member_name = member.username.decode("utf-8")
        if stat_extractor.configuration.censored:
            member_name = member.id
        if periods:
            if measure == "spent":
                s_e_by_user_chart_.add(u"{0}".format(member_name), [spent_time_by_user[member.id].get(time) for time in periods])
            elif measure == "estimated":
                s_e_by_user_chart_.add(u"{0}".format(member_name),[estimated_time_by_user[member.id].get(time) for time in periods])
            elif measure == "diff":
                diff_values = []
                for time in periods:
                    spent_time = spent_time_by_user[member.id].get(time)
                    estimated_time = estimated_time_by_user[member.id].get(time)
                    if not spent_time is None and not estimated_time is None:
                        diff_values.append(estimated_time - spent_time)
                    else:
                        diff_values.append(None)
                s_e_by_user_chart_.add(u"{0}".format(member_name), diff_values)

    s_e_by_user_chart_.x_labels = periods
    s_e_by_user_chart_.show_x_labels = True
    s_e_by_user_chart_.render_to_png(file_path)


def _get_chart_path(chart_type, configuration):
    board_name = configuration.board_name
    now_str = datetime.datetime.now(settings.TIMEZONE).strftime("%Y_%m_%d_%H_%M_%S")
    file_path = u"{0}/{1}-{2}-{3}.png".format(configuration.output_dir, slugify(board_name), slugify(chart_type), slugify(now_str))
    return file_path
