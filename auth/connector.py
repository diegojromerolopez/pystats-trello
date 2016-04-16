# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from trello import TrelloClient

class TrelloConnector(object):

    def __init__(self, api_key, api_secret, token, token_secret):
        self.api_key = api_key
        self.api_secret = api_secret,
        self.token = token,
        self.token_secret = token_secret

    def get_trello_client(self):
        client = TrelloClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            token=self.token,
            token_secret=self.token_secret
        )
        return client
