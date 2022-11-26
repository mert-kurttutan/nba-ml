'''Module for Extracting data for NBA data'''

import os
import json

from pathlib import Path

import pandas as pd
import requests

from nbaetl.enums import TIMEOUT_LIMTT, NBA_STAT_HEADER, NBAEndpoint, FileConfig
from nbaetl.utils import (
    format_year, format_season_type
)
from nbaetl.extract.extract_base import (
    json_to_dataframe, rotate_proxy
)


def run_extract_gamelog_batch(
    _year_array: str | int | list[int] | list[str],
    config_dict: dict,
    file_config: FileConfig,
    upload_result: bool = True,
):
    """Extracts data for entire year, regular season+ playoff games"""

    # Make sure parent directories exists
    Path(f'{file_config.ROOT_RAW}/{file_config.GAMELOG}/').mkdir(parents=True, exist_ok=True)

    if isinstance(_year_array, (str, int)):
        year_array = [_year_array]
    else:
        year_array = _year_array

    # proxy-related variables
    proxy_arr = config_dict["proxy_arr"]
    proxy_idx = 0

    for year in year_array:
        for season in [f"{year}_regular", f"{year}_playoff"]:
            proxy_idx = rotate_proxy(
                proxy_arr, proxy_idx, extract_gamelog_season, 2,
                season, file_config
            )

    if upload_result:
        # Upload directory to s3 bucket
        # Exclude jupyter checkpoint files
        os.system(
            f"aws s3 cp {file_config.ROOT_RAW}/{file_config.GAMELOG} "
            f"s3://{file_config.ROOT_RAW}/{file_config.GAMELOG}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" "
        )


def extract_gamelog_season(
    season: str,
    file_config: FileConfig,
    proxy_config: dict | None = None,
):
    """Extracst player data from for one season and type of season
    Stores the data into player_stat_data directory"""

    if proxy_config is None:
        proxy_config = {}

    stat_type = 'gamelog'
    year, season_type = season.split('_')
    file_name = f'{file_config.ROOT_RAW}/{file_config.GAMELOG}/{stat_type}_{season}.csv'

    # Query data only if it does not exist
    if os.path.exists(file_name):
        return

    df_arr = json_to_dataframe(
        get_raw_gamelog(year=year, season_type=season_type, proxy_config=proxy_config)
    )
    assert len(df_arr) == 1, 'Only One gamelog for the entire season'
    df_arr[0].to_csv(file_name)


def get_raw_gamelog(
    counter="0", player_team="T", league_id="00", year="2018",
    season_type="regular", sort="DATE", direction="ASC", date_from="",
    date_to="", headers=None, proxy_config=None,
):
    """Extracts game logs from nba.stats.com and turns in JSON format
    Data: Log of each game, point difference, name of teams, home and visitor, etc
    Correponding end point: https://stats.nba.com/stats/leaguegamelog"""

    if proxy_config is None:
        proxy_config = {}
    if headers is None:
        headers = NBA_STAT_HEADER

    # Parameters for get request
    payload = {
        'Counter': counter,
        'DateFrom': date_from,
        'DateTo': date_to,
        'Direction': direction,
        'LeagueID': league_id,
        'PlayerOrTeam': player_team,
        'Season': format_year(year),
        'SeasonType': format_season_type(season_type),
        'Sorter': sort
    }

    # Turn into json format
    json_data = requests.get(
        NBAEndpoint.GAMELOG, headers=headers, params=payload,
        proxies=proxy_config, timeout=TIMEOUT_LIMTT
    ).json()
    return json_data


def update_config(config: dict, is_upload: bool, file_config: FileConfig):
    '''Updates config data using latest gamelog data'''
    for file in os.listdir(f"{file_config.ROOT_RAW}/{file_config.GAMELOG}"):
        if not ".csv" in file:
            continue

        # name variables
        season_label = file[8:20]
        gamelog_file_name = f"{file_config.ROOT_RAW}/{file_config.GAMELOG}/{file}"

        # Extract data
        # Use converter to preserve leading zeros in GAME_ID column
        # If leading zeros are not preserved, parameters will be in invalid format
        gamelog_df = pd.read_csv(gamelog_file_name, converters={'GAME_ID': str})

        # Store season dates into config file
        config["season_dates"][season_label] = (
            gamelog_df["GAME_DATE"].min(), gamelog_df["GAME_DATE"].max()
        )

        # Store game ids, turn it into list since it is JSON-serializable
        config["season_game_ids"][season_label] = gamelog_df["GAME_ID"].unique().tolist()


    with open(f"{file_config.ROOT_RAW}/{file_config.DATA_CONFIG}", "w", encoding='utf-8') as outfile:
        json.dump(config, outfile)


    if is_upload:
        os.system(
            f"aws s3 cp {file_config.ROOT_RAW}/{file_config.DATA_CONFIG} "
            f"s3://{file_config.CONFIG_BUCKET}/{file_config.DATA_CONFIG} "
        )
