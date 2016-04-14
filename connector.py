# -*- coding: utf-8 -*-

from trello import TrelloClient


def connect(api_key, api_secret, token, token_secret):
    client = TrelloClient(
        api_key=api_key,
        api_secret=api_secret,
        token=token,
        token_secret=token_secret
    )
    return client