'''Module for extracting daily stat'''

import os

from pathlib import Path
from datetime import timedelta, date

import requests

from nbaetl.enums import TIMEOUT_LIMTT, NBA_STAT_HEADER, NBAEndpoint, FileConfig
from nbaetl.utils import (
    format_year, format_season_type, daterange
)

from nbaetl.extract.extract_base import (
    json_to_dataframe, rotate_proxy
)


def run_extract_daystat_batch(
    stat_type: str,
    _year_array: str | int | list[int] | list[str],
    config_dict: dict,
    file_config: FileConfig,
    upload_result: bool = True,
):
    '''RUN BATCH'''
    # Make sure parent directories exists
    data_dir = file_config.TEAMSTAT if stat_type == 'teamstat' else file_config.PLAYERSTAT
    Path(f'{file_config.ROOT_RAW}/{data_dir}').mkdir(parents=True, exist_ok=True)

    if isinstance(_year_array, (str, int)):
        year_array = [_year_array]
    else:
        year_array = _year_array

    for year in year_array:
        for season_name in config_dict["season_game_ids"]:
            if str(year) in season_name:
                # Date variables for regular season
                season_start, season_end = config_dict["season_dates"][season_name]
                extract_daystat_season(
                    stat_type, season_name, season_start, season_end, file_config, config_dict
                )

    if upload_result:
        # Upload directory to s3 bucket
        # Exclude jupyter checkpoint files
        os.system(
            f"aws s3 cp {file_config.ROOT_RAW}/{data_dir} "
            f"s3://{file_config.ROOT_RAW}/{data_dir}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" "
        )


def extract_daystat_season(
    stat_type: str,
    season: str,
    start_date: str,
    end_date: str,
    file_config: FileConfig,
    config_dict: dict
):
    """Extracts data for entire year, regular season+ playoff games"""
    year = season[:4]
    # Make sure parent directory exists
    data_dir = file_config.TEAMSTAT if stat_type == 'teamstat' else file_config.PLAYERSTAT
    Path(f'{file_config.ROOT_RAW}/{data_dir}/{year}').mkdir(parents=True, exist_ok=True)

    # proxy-related variables
    proxy_arr = config_dict["proxy_arr"]
    proxy_idx = 0

    for cur_date in daterange(start_date, end_date):
        # Current date
        proxy_idx = rotate_proxy(
            proxy_arr, proxy_idx, extract_daystat_day, 2,
            stat_type, cur_date, season,
            file_config
        )


def extract_daystat_day(
    stat_type: str,
    date_: date,
    season_label: str,
    file_config: FileConfig,
    proxy_config: dict
):
    """Extracst player data from for one season and type of season
        Stores the data into playerstat and teamstat directory"""
    _year = season_label[:4]
    if season_label[-7:] == 'regular':
        season_arr = [f"{_year}_regular"]
    elif season_label[-7:] == 'playoff':
        season_arr = [f"{_year}_regular", f"{_year}_playoff"]
    else:
        raise ValueError(f'{season_label} is an Invalid Season Name!!!')

    # Statistical data from past 8, 16, 32, 64, 180 dates, can be thought of as a hyperparameter
    # 180 days is to capture entire season statistics
    lag_len_arr = [8, 16, 32, 64, 180]

    _get_stat_func, _data_dir = name2function[stat_type]

    for lag_len in lag_len_arr:
        for _season in season_arr:
            df_file_name = (
                f'{file_config.ROOT_RAW}/{_data_dir}/{_year}/'
                f'{stat_type}_{_season}_{date_}_lagged{lag_len:02d}.csv'
            )
            # Query data only if it does not exist
            if os.path.exists(df_file_name):
                continue
            print(df_file_name)
            df_arr = json_to_dataframe(
                _get_stat_func(date_, _season, lag_len, proxy_config)
            )
            for result_df in df_arr:
                result_df.to_csv(df_file_name)


def get_teamstat_lagged(
    cur_date: date, season: str, lag_length: int, proxy_config: dict
) -> list:
    '''Lagged time average of teamstat'''

    season_year = format_year(season[:4])
    season_type = format_season_type(season[-7:])

    previous_day = cur_date - timedelta(days=1)
    previous_day_lag_len = cur_date - timedelta(days=1+lag_length)

    df_arr = get_raw_teamstat(
        date_to=str(previous_day),
        date_from=str(previous_day_lag_len),
        season=season_year, season_type=season_type, per_mode="PerMinute",
        proxy_config=proxy_config
    )

    return df_arr


def get_playerstat_lagged(
    cur_date: date, season: str, lag_length: int, proxy_config: dict
) -> list:
    '''Lagged time average of teamstat'''

    season_year = format_year(season[:4])
    season_type = format_season_type(season[-7:])

    previous_day = cur_date - timedelta(days=1)
    previous_day_lag_len = cur_date - timedelta(days=1+lag_length)

    df_arr = get_raw_playerstat(
        date_to=str(previous_day),
        date_from=str(previous_day_lag_len),
        season=season_year, season_type=season_type, per_mode="PerMinute",
        proxy_config=proxy_config
    )

    return df_arr


name2function = {
    'playerstat': (
        get_playerstat_lagged, FileConfig.PLAYERSTAT
    ),
    'teamstat': (
        get_teamstat_lagged, FileConfig.TEAMSTAT
    ),
}


def get_raw_teamstat(
    conference="", date_from="", date_to="", division="", game_scope="", game_segment="",
    last_ngames=100, league_id="00", location="", measure_type="Base", month=0, opponent_id=0,
    outcome="", po_round="", pace_adjust="N", per_mode="Totals", period=0, player_experience="",
    player_position="", plus_minus="N", rank="N", season="2019-20", season_segment="",
    season_type="Regular Season", shot_clock_range="", starter_bench="", team_id="", two_way="",
    vs_conference="", vs_division="", headers=None, proxy_config=None,
):

    """Transforms json data extracted from nba api into list of dataframes and returns it
    Data: Statistics of individual teams, determined by parameters in get request
    Corresponding end point: https://stats.nba.com/stats/leaguedashteamstats"""

    if proxy_config is None:
        proxy_config = {}
    if headers is None:
        headers = NBA_STAT_HEADER

    # Parameters for the end point
    payload = {
        'Conference': conference,
        'DateFrom': date_from,
        'DateTo': date_to,
        'Division': division,
        'GameScope': game_scope,
        'GameSegment': game_segment,
        'LastNGames': last_ngames,
        'LeagueID': league_id,
        'Location': location,
        'MeasureType': measure_type,
        'Month': month,
        'OpponentTeamID': opponent_id,
        'Outcome': outcome,
        'PORound': po_round,
        'PaceAdjust': pace_adjust,
        'PerMode': per_mode,
        'Period': period,
        'PlayerExperience': player_experience,
        'PlayerPosition': player_position,
        'PlusMinus': plus_minus,
        'Rank': rank,
        'Season': season,
        'SeasonSegment': season_segment,
        'SeasonType': season_type,
        'ShotClockRange': shot_clock_range,
        'StarterBench': starter_bench,
        'TeamID': team_id,
        'TwoWay': two_way,
        'VsConference': vs_conference,
        'VsDivision': vs_division
    }

    # Turn into json format
    json_data = requests.get(
        NBAEndpoint.TEAMSTAT, headers=headers, params=payload,
        proxies=proxy_config, timeout=TIMEOUT_LIMTT
    )

    json_data = json_data.json()
    return json_data


def get_raw_playerstat(
    college="", conference="", country="", date_from="", date_to="",
    division="", draft_pick="", draft_year="", game_scope="", game_segment="",
    height="", last_ngames=100, league_id="00", location="", measure_type="Base",
    month=0, opponent_id=0, outcome="", po_round="", pace_adjust="N",
    per_mode="Totals", period=0, player_experience="", player_position="",
    plus_minus="N", rank="N", season="2019-20", season_segment="",
    season_type="Regular Season", shot_clock_range="", starter_bench="", team_id="",
    two_way="", vs_conference="", vs_division="", weight="",
    headers=None, proxy_config=None
):
    """Transforms json data extracted from nba api into list of dataframes and returns it
    Data: Statistics of individual players, determined by parameters in get request
    Corresponding end point: https://stats.nba.com/stats/leaguedashplayerstats"""

    if proxy_config is None:
        proxy_config = {}
    if headers is None:
        headers = NBA_STAT_HEADER

    # Parameters for the end point
    payload = {
        'College': college,
        'Conference': conference,
        'Country': country,
        'DateFrom': date_from,
        'DateTo': date_to,
        'Division': division,
        'DraftPick': draft_pick,
        'DraftYear': draft_year,
        'GameScope': game_scope,
        'GameSegment': game_segment,
        'Height': height,
        'LastNGames': last_ngames,
        'LeagueID': league_id,
        'Location': location,
        'MeasureType': measure_type,
        'Month': month,
        'OpponentTeamID': opponent_id,
        'Outcome': outcome,
        'PORound': po_round,
        'PaceAdjust': pace_adjust,
        'PerMode': per_mode,
        'Period': period,
        'PlayerExperience': player_experience,
        'PlayerPosition': player_position,
        'PlusMinus': plus_minus,
        'Rank': rank,
        'Season': season,
        'SeasonSegment': season_segment,
        'SeasonType': season_type,
        'ShotClockRange': shot_clock_range,
        'StarterBench': starter_bench,
        'TeamID': team_id,
        'TwoWay': two_way,
        'VsConference': vs_conference,
        'VsDivision': vs_division,
        'Weight': weight
    }

    # Turn into json format
    json_data = requests.get(
        NBAEndpoint.PLAYERSTAT, headers=headers, params=payload,
        proxies=proxy_config, timeout=TIMEOUT_LIMTT
    )

    json_data = json_data.json()
    return json_data
