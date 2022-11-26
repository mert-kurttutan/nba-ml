'''
enums and constans
'''
from __future__ import annotations

from enum import Enum, IntEnum, unique

# contants
TIMEOUT_LIMTT = 120
NBA_STAT_HEADER = {
    'user-agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
    ),
    "host": 'stats.nba.com',
    "cache-control":"max-age=0",
    "connection": 'keep-alive',
    "accept-encoding" : "Accepflate, sdch",
    'accept-language':'he-IL,he;q=0.8,en-US;q=0.6,en;q=0.4',
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    ),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Host': 'stats.nba.com',
    'Referer': (
        'https://stats.nba.com/teams/traditional/'
        '?sort=W_PCT&dir=-1&Season=2019-20&SeasonType=Regular%20Season'
    ),
    'Connection': 'keep-alive',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Origin': 'https://stats.nba.com',
}


@unique
class HTTPCode(IntEnum):
    BAD_REQUEST = 400
    NOT_FOUND = 404
    BAD_GATEWAY = 502


@unique
class NBAEndpoint(str, Enum):
    GAMELOG = "https://stats.nba.com/stats/leaguegamelog"
    GAMEROTATION = "https://stats.nba.com/stats/gamerotation"
    NBA2K = "https://hoopshype.com/nba2k"
    TEAMSTAT = "https://stats.nba.com/stats/leaguedashteamstats"
    PLAYERSTAT = "https://stats.nba.com/stats/leaguedashplayerstats"

    def __str__(self):
        return str(self.value)


@unique
class FileConfig(str, Enum):
    ROOT_RAW = "nba-ml-raw-data"
    ROOT_TRANSFORMED = "nba-ml-transformed-data"
    GAMELOG = "gamelog_data"
    GAMEROTATION = "gamerotation_data"
    NBA2K = "nba2k_data"
    PLAYERSTAT = "playerstat_data"
    TEAMSTAT = "teamstat_data"

    CONFIG_BUCKET = "mert-kurttutan-nba-ml-files/config"

    DATA_CONFIG = "data_config.json"

    def __str__(self):
        return str(self.value)
