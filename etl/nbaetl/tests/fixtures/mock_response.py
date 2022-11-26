'''module for producing mock response
'''
import json

import importlib.resources as pkg_resources


# with open("./gamelog.json", "r", encoding='utf-8') as read_content:
#     gamelog_json = json.load(read_content)

# with open("./gamerotation.json", "r", encoding='utf-8') as read_content:
#     gamerotation_json = json.load(read_content)

gamelog_json = pkg_resources.read_text(__package__, 'gamelog.json')

gamerotation_json = pkg_resources.read_text(__package__, 'gamerotation.json')


def get_json_gamelog():
    '''Json for gamelog data'''
    return gamelog_json


def get_json_gamerotation():
    '''Json for gamelog data'''
    return gamerotation_json


class MockResponse:
    """mock response class"""
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """json of mock response"""
        return self.json_data
