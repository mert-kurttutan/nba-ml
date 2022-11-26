'''extract gamerotation'''

import os
from pathlib import Path

import requests
import pandas as pd


from nbaetl.enums import TIMEOUT_LIMTT, NBA_STAT_HEADER, NBAEndpoint, FileConfig

from nbaetl.extract.extract_base import (
    json_to_dataframe, rotate_proxy
)


def run_extract_gamerotation_batch(
    year_arr: list,
    config_dict: dict,
    file_config: FileConfig,
    upload_result: bool = True,
):
    """Extracts data for entire year, regular season+ playoff games"""

    # Make sure parent directories exists
    Path(f'{file_config.ROOT_RAW}/{file_config.GAMEROTATION}/').mkdir(parents=True, exist_ok=True)
    # proxy-related variables
    proxy_arr = config_dict["proxy_arr"]
    proxy_idx = 0

    for year in year_arr:
        for season_name in config_dict["season_game_ids"]:
            if str(year) in season_name:
                # Make sure parent directory exists
                Path(f'{file_config.ROOT_RAW}/{file_config.GAMEROTATION}/{season_name}/'
                ).mkdir(parents=True, exist_ok=True)
                print(f"Query for season: {season_name}")
                game_id_season = config_dict["season_game_ids"][season_name]
                for game_id in game_id_season:
                    print(game_id)
                    proxy_idx = rotate_proxy(
                        proxy_arr, proxy_idx, extract_gamerotation_game, 2,
                        game_id, season_name, file_config
                    )

    if upload_result:
        # Upload directory to s3 bucket
        # Exclude jupyter checkpoint files
        os.system(
            f"aws s3 cp {file_config.ROOT_RAW}/{file_config.GAMEROTATION} "
            f"s3://{file_config.ROOT_RAW}/{file_config.GAMEROTATION}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" "
        )


def extract_gamerotation_game(
    game_id: str, season_label: str, file_config: FileConfig, proxy_config: dict
):
    """Extracts player data from for one season and type of season
    Stores the data into player_stat_data directory"""

    df_file_name = (
        f'{file_config.ROOT_RAW}/{file_config.GAMEROTATION}/'
        f'{season_label}/gamerotation_{game_id}.csv'
    )
    # Query data only if it does not exist
    if os.path.exists(df_file_name):
        return

    df_arr = json_to_dataframe(
        get_raw_gamerotation(game_id=game_id, proxy_config=proxy_config)
    )
    result_df = pd.concat(df_arr)
    result_df.to_csv(df_file_name)


def get_raw_gamerotation(game_id, league_id="00", headers=None, proxy_config=None):
    """Extracts game logs from nba.stats.com and turns in JSON format
    Data: Log of each game, point difference, name of teams, home and visitor, etc
    Correponding end point: https://stats.nba.com/stats/gamerotation"""

    if proxy_config is None:
        proxy_config = {}
    if headers is None:
        headers = NBA_STAT_HEADER

    # Parameters for get request
    payload = {
        'GameID': game_id,
        'LeagueID': league_id,
    }

    # Turn into json format
    json_data = requests.get(
        NBAEndpoint.GAMEROTATION, headers=headers, params=payload,
        proxies=proxy_config, timeout=TIMEOUT_LIMTT
    ).json()
    return json_data
