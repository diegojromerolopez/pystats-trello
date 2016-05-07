# -*- coding: utf-8 -*-
import os
import sys

import re

import settings
from auth.connector import TrelloConnector
from stats import summary
from stats.trelloboardconfiguration import TrelloBoardConfiguration


def extract_stats(configuration_file_path):
    """
    Extract stats for a given configuration file that defines a trello board and other settings.
    :param configuration_file_path: file path where the configuration file is.
    """
    configuration = TrelloBoardConfiguration.load_from_file(configuration_file_path)
    summary.make(trello_connector, configuration)


def file_is_configuration_file(_file_name):
    return re.match(r"^[^\.]+\.conf\.txt", _file_name)

if __name__ == "__main__":

    api_key = settings.TRELLO_API_KEY
    api_secret = settings.TRELLO_API_SECRET
    token = settings.TRELLO_TOKEN
    token_secret = settings.TRELLO_TOKEN_SECRET

    trello_connector = TrelloConnector(api_key, api_secret, token, token_secret)

    if len(sys.argv) < 2:
        raise ValueError(u"Error. Use python stats_extractor.py <configuration_file_path>")

    # Configuration file path
    configuration_path = sys.argv[1]

    # If configuration path is a file, extract stats of the board written in this file
    if os.path.isfile(configuration_path):
        extract_stats(configuration_path)

    # Otherwise, if configuration path is a directory, loop through directory files and extract stats
    # for each of these files
    elif os.path.isdir(configuration_path):
        for file_name in os.listdir(configuration_path):
            if file_is_configuration_file(file_name):
                print(u"Processing {0}".format(file_name))
                extract_stats(u"{0}/{1}".format(configuration_path, file_name))


