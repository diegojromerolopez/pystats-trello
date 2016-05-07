import importlib
import re

from stats.trelloboardworkflow import TrelloBoardWorkflow


class TrelloBoardConfiguration(object):

    PLUS_FOR_TRELLO_SPENT_ESTIMATED_TIME_COMMENT_REGEX = r"^plus!\s(?P<spent>(\-)?\d+(\.\d+)?)/(?P<estimated>(\-)?\d+(\.\d+)?)"

    def __init__(self, board_name, card_is_active_function,
                 development_list_name, done_list_name,
                 spent_estimated_time_comment_regex,
                 output_dir, censored=False,
                 card_action_filter=None,
                 custom_workflows=None):

        self.board_name = board_name
        self.card_is_active_function = card_is_active_function
        self.card_is_active_function_code = card_is_active_function

        if self.card_is_active_function and type(self.card_is_active_function).__name__ != "function":
            lambda_card_is_active_function = "lambda card: ({0})".format(self.card_is_active_function)
            self.card_is_active_function = eval(lambda_card_is_active_function)

        self.development_list_name = development_list_name
        self.done_list_name = done_list_name

        if spent_estimated_time_comment_regex == "PLUS_FOR_TRELLO_REGEX":
            self.spent_estimated_time_card_comment_regex = self.__class__.PLUS_FOR_TRELLO_SPENT_ESTIMATED_TIME_COMMENT_REGEX

        self.card_action_filter = card_action_filter

        self.output_dir = output_dir
        self.censored = censored
        self.custom_workflows = custom_workflows

    # Loads the configuration file from a file to a TrelloBoardConfiguration
    @staticmethod
    def load_from_file(file_path):
        conf_file = open(file_path, "r")
        lines = conf_file.readlines()
        num_lines = len(lines)

        censored = False
        board_name = None
        development_list = None
        done_list = None
        card_action_filter = None
        card_is_active_function = None
        comment_spent_estimated_time_regex = None
        output_dir = None
        workflows = []

        i = 0
        while i < num_lines:
            if not re.match("r\s+$", lines[i]):
                # Board name extraction
                param = TrelloBoardConfiguration._get_single_parameter_from_line(u"BOARD_NAME", lines[i])
                if param:
                    board_name = param
                    param = None

                # Development list
                param = TrelloBoardConfiguration._get_single_parameter_from_line(u"DEVELOPMENT_LIST", lines[i])
                if param:
                    development_list = param.decode("utf-8")
                    param = None

                # Done list
                param = TrelloBoardConfiguration._get_single_parameter_from_line(u"DONE_LIST", lines[i])
                if param:
                    done_list = param.decode("utf-8")
                    param = None

                # Custom workflow
                if lines[i].decode("utf-8") == u"CUSTOM_WORKFLOWS:\n":
                    i += 1
                    matches = re.match("^\-\s*(.+)$", lines[i])
                    while matches:
                        if matches.group(1):
                            workflow_name = matches.group(1)
                            i += 1
                            matches = re.match("^\s+\-\s*LISTS:\s*(.+)$", lines[i])
                            if matches.group(1):
                                workflow_lists = re.split(r"\s*,\s*", matches.group(1))
                                i += 1
                                matches = re.match("^\s+\-\s*DONE_LISTS:\s*(.+)$", lines[i])
                                if matches.group(1):
                                    workflow_done_lists = re.split(r"\s*,\s*", matches.group(1))
                                    i += 1
                                    workflow = TrelloBoardWorkflow(workflow_name,
                                                                   [list_.decode("utf-8") for list_ in workflow_lists],
                                                                   [list_.decode("utf-8") for list_ in workflow_done_lists])
                                    workflows.append(workflow)
                                    matches = re.match("^\-\s*(.+)$", lines[i])
                                else:
                                    ValueError(u"DONE_LISTS was expected")
                            else:
                                ValueError(u"LISTS was expected")

                # Card is active function
                matches = re.match(r"^CARD_ACTION_FILTER:\s*\[(\d{4}\-\d{2}\-\d{2}),\s*(\d{4}\-\d{2}\-\d{2})\]\s*$", lines[i])
                if matches:
                    card_action_filter = [matches.group(1), matches.group(2)]
                    i += 1
                    matches = None

                # Card is active function
                param = TrelloBoardConfiguration._get_single_parameter_from_line(u"CARD_IS_ACTIVE_FUNCTION", lines[i])
                if param:
                    card_is_active_function = param
                    i += 1
                    param = None

                # Comment spent estimated time regex
                param = TrelloBoardConfiguration._get_single_parameter_from_line(u"COMMENT_SPENT_ESTIMATED_TIME_REGEX", lines[i])
                if param:
                    comment_spent_estimated_time_regex = param
                    i += 1
                    param = None

                # Card is active function
                param = TrelloBoardConfiguration._get_single_parameter_from_line(u"OUTPUT_DIR", lines[i])
                if param:
                    output_dir = param
                    i += 1
                    param = None

                # Output must be censored
                if i < len(lines):
                    matches = re.match(r"^CENSORED:\s*TRUE$",lines[i])
                    if matches:
                        censored = True
                        i += 1
                        matches = None

            i += 1

        conf_file.close()

        TrelloBoardConfiguration._assert_value(board_name, "BOARD_NAME")
        TrelloBoardConfiguration._assert_value(development_list, "DEVELOPMENT_LIST")
        TrelloBoardConfiguration._assert_value(done_list, "DONE_LIST")
        TrelloBoardConfiguration._assert_value(card_is_active_function, "CARD_IS_ACTIVE_FUNCTION")
        TrelloBoardConfiguration._assert_value(comment_spent_estimated_time_regex, "COMMENT_SPENT_ESTIMATED_TIME_REGEX")
        TrelloBoardConfiguration._assert_value(output_dir, "OUTPUT_DIR")

        return TrelloBoardConfiguration(
            censored=censored,
            board_name=board_name, card_action_filter=card_action_filter,
            card_is_active_function=card_is_active_function,
            development_list_name=development_list, done_list_name=done_list,
            spent_estimated_time_comment_regex=comment_spent_estimated_time_regex,
            output_dir=output_dir,
            custom_workflows=workflows)

    @staticmethod
    def _get_single_parameter_from_line(parameter_name, line):
        matches = re.match(r"^{0}:\s*([^\n]+)$".format(parameter_name), line)
        if matches:
            return matches.group(1)
        return False

    @staticmethod
    def _assert_value(value, value_name):
        if value is None:
            raise ValueError(u"{0} is required".format(value_name))
