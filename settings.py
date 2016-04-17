# -*- coding: utf-8 -*-

import importlib
import pytz

TIMEZONE = pytz.timezone('Europe/Madrid')

try:
    settings_local = importlib.import_module('settings_local')
except ImportError:
    print("Please, create a local_settings.py with authentication data and other preferences")
    exit(-1)

TRELLO_API_KEY = settings_local.TRELLO_API_KEY
TRELLO_API_SECRET = settings_local.TRELLO_API_SECRET

TRELLO_TOKEN = settings_local.TRELLO_TOKEN
TRELLO_TOKEN_SECRET = settings_local.TRELLO_TOKEN_SECRET

DEVELOPMENT_LIST = settings_local.DEVELOPMENT_LIST

if hasattr(settings_local, "DONE_LIST"):
    DONE_LIST = settings_local.DONE_LIST

# The conditions to extract all the statistic information about a card is defined here.
# In this application jargon, cards that pass this test are called "active cards".
# This setting is optional and by default, cards that are not archived will be considered active.
if hasattr(settings_local, "CARD_IS_ACTIVE_FUNCTION"):
    CARD_IS_ACTIVE_FUNCTION = settings_local.CARD_IS_ACTIVE_FUNCTION

# Some systems store the spent and estimated times of each task in the card comments.
# Setting this option allow the system to automatically fetch them.
# For example r"^plus!\s(?P<spent>(\-)?\d+(\.\d+)?)/(?P<estimated>(\-)?\d+(\.\d+)?)" is the regex for matching
# Plus for Trello comments
if hasattr(settings_local, "SPENT_ESTIMATED_TIME_CARD_COMMENT_REGEX"):
    SPENT_ESTIMATED_TIME_CARD_COMMENT_REGEX = settings_local.SPENT_ESTIMATED_TIME_CARD_COMMENT_REGEX

TEST_BOARD = settings_local.TEST_BOARD

OUTPUT_DIR = settings_local.OUTPUT_DIR
