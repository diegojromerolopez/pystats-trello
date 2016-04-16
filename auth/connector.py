# -*- coding: utf-8 -*-

from trello import TrelloClient


class TrelloConnector(object):

    def __init__(self, api_key, api_secret, token, token_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.token = token
        self.token_secret = token_secret

    def get_trello_client(self):
        client = TrelloClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            token=self.token,
            token_secret=self.token_secret
        )
        return client

    def test(self):
        client = self.get_trello_client()
        print(u"Listing all accesible boards")
        boards = client.list_boards()
        for board in boards:
            print(u"{0}".format(board.name.decode("utf-8")))
