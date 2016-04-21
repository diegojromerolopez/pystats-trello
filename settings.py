# -*- coding: utf-8 -*-

import importlib
import pytz
from trello.configuration import Configuration

TIMEZONE = pytz.timezone('Europe/Madrid')
Configuration.TIMEZONE = 'Europe/Madrid'

try:
    settings_local = importlib.import_module('settings_local')
except ImportError:
    print("Please, create a local_settings.py with authentication data and other preferences")
    exit(-1)

TRELLO_API_KEY = settings_local.TRELLO_API_KEY
TRELLO_API_SECRET = settings_local.TRELLO_API_SECRET

TRELLO_TOKEN = settings_local.TRELLO_TOKEN
TRELLO_TOKEN_SECRET = settings_local.TRELLO_TOKEN_SECRET

