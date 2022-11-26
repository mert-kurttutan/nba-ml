'''transform teamstat'''

import os

from pathlib import Path
from datetime import date
import pandas as pd
import numpy as np

from nbaetl.enums import FileConfig

from nbaetl.utils import add_prefix, daterange


lag_len_arr = ["08", "16", "32", "64", "180"]

relevant_cols_teamstat = [
    'TEAM_ID', 'GAME_DATE', 'GP', 'W_PCT', 'FG_PCT', 'FT_PCT', 'DAY_WITHIN_SEASON',
    'OREB', 'DREB', 'REB', 'AST', 'TOV', 'STL', 'BLK', 'PTS','PLUS_MINUS',
    'W_PCT_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK'
]

relevant_cols_playerstat = [
    'PLAYER_ID','GAME_DATE', 'GP', 'W_PCT', 'FG_PCT', 'FG3M', 'FG3_PCT', 'FTM', 'FT_PCT', 'OREB',
    'DREB', 'AST', 'TOV', 'STL', 'BLK', 'PTS', 'DAY_WITHIN_SEASON',
    'PLUS_MINUS', 'NBA_FANTASY_PTS', 'W_PCT_RANK', 'FGM_RANK', 'FG_PCT_RANK',
    'FG3M_RANK', 'FG3_PCT_RANK', 'FT_PCT_RANK', 'OREB_RANK', 'DREB_RANK','AST_RANK',
    'TOV_RANK', 'STL_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK', 'NBA_FANTASY_PTS_RANK',
]


# Cols to add tage
cols_to_tag_teamstat = [
    'GP', 'W_PCT', 'FG_PCT', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'TOV', 'STL', 
    'BLK', 'PTS','PLUS_MINUS', 'W_PCT_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK'
]


cols_to_tag_playerstat = [
    'GP', 'W_PCT', 'FG_PCT', 'FG3M', 'FG3_PCT', 'FTM', 'FT_PCT', 'OREB',
    'DREB', 'AST', 'TOV', 'STL', 'BLK', 'PTS', 'PLUS_MINUS', 
    'NBA_FANTASY_PTS', 'W_PCT_RANK', 'FGM_RANK', 'FG_PCT_RANK',
    'FG3M_RANK', 'FG3_PCT_RANK', 'FT_PCT_RANK', 'OREB_RANK', 'DREB_RANK', 'AST_RANK',
    'TOV_RANK', 'STL_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK', 'NBA_FANTASY_PTS_RANK'
]


def run_transform_daystat_batch(
    stat_type: str,
    year_arr: list[int],
    config_dict,
    file_config: FileConfig,
    is_upload: bool = True,
    save_array: bool = False,
):
    '''runs batch'''
    data_dir = (
        file_config.TEAMSTAT if stat_type == 'teamstat'
        else file_config.PLAYERSTAT
    )

    id_col = (
        'TEAM_ID' if stat_type == 'teamstat'
        else 'PLAYER_ID'
    )

    # Make sure gamerotation diretory exists
    Path(f'{file_config.ROOT_TRANSFORMED}/{data_dir}/'
    ).mkdir(parents=True, exist_ok=True)

    print("Extracting Team data...")

    for year in year_arr:
        os.system(
            f"aws s3 cp s3://{file_config.ROOT_RAW}/{data_dir}/{year}/ "
            f"{file_config.ROOT_RAW}/{data_dir}/{year}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" " )

    df_daystat_transformed_arr = []
    # Iterate over years
    for year in year_arr:

        # Iterate over season types
        for season_type in ["playoff", "regular"]:

            # Get start and end date of season
            start_date, end_date = config_dict["season_dates"][f"{year}_{season_type}"]

            if season_type == "regular":
                _, end_date = config_dict["season_dates"][f"{year}_playoff"]

            # This will contain all the statisc with all the lagging values
            df_daystat_transformed = pd.DataFrame()

            # Iterate over dates within season
            for i, cur_date in enumerate(daterange(start_date, end_date)):
                print(cur_date)
                # dataframe that contains data for one date and one lagging value
                df_daystat = pd.DataFrame()
                for lag_len in lag_len_arr:

                    df_file_name = (
                        f'{file_config.ROOT_RAW}/{data_dir}/{year}/'
                        f'{stat_type}_{year}_{season_type}_{cur_date}_lagged{lag_len}.csv'
                    )

                    # at the moment, some of the ranges are uploaded yet
                    # so by pass if not exists
                    if not os.path.exists(df_file_name):
                        continue

                    # get file, enter corresponding date, extract only relevant columns
                    df_daystat_lagged = pd.read_csv(df_file_name)
                    df_daystat_lagged = transform_daystat_date(
                        df_daystat_lagged, stat_type, cur_date, i, lag_len
                    )

                    # Some of the tables are empty, add only non-empty ones
                    # otherwise, mergin gives undersired column orders
                    if df_daystat_lagged.shape[0] == 0:
                        continue

                    if df_daystat.empty:
                        df_daystat = df_daystat_lagged
                    else:
                        # Merge teams into one row where info about two team is contained
                        df_daystat = df_daystat.merge(
                            df_daystat_lagged, on=[id_col, "GAME_DATE", "DAY_WITHIN_SEASON"]
                        )

                df_daystat_transformed = pd.concat(
                    [df_daystat_transformed, df_daystat], ignore_index=True
                )

            df_daystat_transformed.to_csv(
                f"{file_config.ROOT_TRANSFORMED}/{data_dir}/{stat_type}_{year}_{season_type}.csv",
                index=False
            )

            if save_array:
                df_daystat_transformed_arr.append(df_daystat_transformed)

    if is_upload:
        os.system(
            f"aws s3 cp {file_config.ROOT_TRANSFORMED}/{data_dir} "
            f"s3://{file_config.ROOT_TRANSFORMED}/{data_dir}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" " )

    return df_daystat_transformed_arr


def transform_daystat_date(
    daystat_lagged: pd.DataFrame,
    stat_type: str,
    current_date: date,
    current_idx: int,
    lag_len: int | str,
) -> pd.DataFrame:
    '''transform single instance of team stat'''
    daystat_lagged['GAME_DATE'] = str(current_date)
    daystat_lagged['DAY_WITHIN_SEASON'] = current_idx
    if stat_type == 'teamstat':
        relevant_cols_daystat = relevant_cols_teamstat
        cols_to_tag_daystat = cols_to_tag_teamstat
    elif stat_type == 'playerstat':
        relevant_cols_daystat = relevant_cols_playerstat
        cols_to_tag_daystat = cols_to_tag_playerstat
    else:
        raise ValueError('Invalid stat type')
    daystat_lagged = daystat_lagged[relevant_cols_daystat]

    # add the lagging tag to time-dependent columns, e.g. point average, 3pt percentage
    col_map_daystat = add_prefix(cols_to_tag_daystat, f"lag{lag_len}_")
    daystat_lagged = daystat_lagged.rename(columns = col_map_daystat)
    return daystat_lagged


def fillpast_daystat(
    stat_type: str,
    year_arr: list[int],
    file_config: FileConfig,
    is_upload: bool = True,
    save_array: bool = False,
):
    '''runs batch'''
    data_dir = (
        file_config.TEAMSTAT if stat_type == 'teamstat'
        else file_config.PLAYERSTAT
    )

    # Make sure gamerotation diretory exists
    Path(f'{file_config.ROOT_TRANSFORMED}/{data_dir}/'
    ).mkdir(parents=True, exist_ok=True)

    df_arr_daystat_transformed = []

    for year in year_arr:
        print(year)
        current_daystat_regular = pd.read_csv(
            f"{file_config.ROOT_TRANSFORMED}/{file_config.TEAMSTAT}/teamstat_{year}_regular.csv"
        )
        current_daystat_playoff = pd.read_csv(
            f"{file_config.ROOT_TRANSFORMED}/{file_config.TEAMSTAT}/teamstat_{year}_playoff.csv"
        )
        filled_daystat_regular = fill_past_teamstat_regular(
            current_daystat_regular, year, file_config
        )

        filled_daystat_playoff = fill_past_teamstat_playoff(
            current_daystat_playoff, filled_daystat_regular
        )

        filled_daystat_regular.to_csv(f"{file_config.ROOT_TRANSFORMED}/{data_dir}/{stat_type}_{year}_regular_filled.csv", index=False)
        filled_daystat_playoff.to_csv(f"{file_config.ROOT_TRANSFORMED}/{data_dir}/{stat_type}_{year}_playoff_filled.csv", index=False)

        if save_array:
            df_arr_daystat_transformed.extend((filled_daystat_regular, filled_daystat_playoff))

    if is_upload:
        os.system(
            f"aws s3 cp {file_config.ROOT_TRANSFORMED}/{data_dir} "
            f"s3://{file_config.ROOT_TRANSFORMED}/{data_dir}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" " )

    return df_arr_daystat_transformed

def fill_past_teamstat_regular(
    current_year_stat: pd.DataFrame,
    current_year: int,
    file_config: FileConfig
):
    '''fill past missing data'''
    # if previous season data is absent
    # dont change it
    if not os.path.exists(f"{file_config.ROOT_TRANSFORMED}/{file_config.TEAMSTAT}/teamstat_{current_year-1}_regular.csv"):
        return current_year_stat

    current_gamelog = pd.read_csv(
        f"{file_config.ROOT_TRANSFORMED}/{file_config.GAMELOG}/gamelog_{current_year}_regular.csv"
    )
    prev_year_stat = pd.read_csv(
        f"{file_config.ROOT_TRANSFORMED}/{file_config.TEAMSTAT}/teamstat_{current_year-1}_regular.csv"
    )
    
    filled_daystat = fill_past_teamstat_regular_single(
        current_year_stat, prev_year_stat, current_gamelog, 1
    )
    filled_daystat = fill_past_teamstat_regular_single(
        filled_daystat, prev_year_stat, current_gamelog, 2
    )

    return filled_daystat

def fill_past_teamstat_regular_single(
    current_year_stat: pd.DataFrame,
    prev_year_stat: pd.DataFrame,
    current_gamelog: pd.DataFrame,
    team_idx: int = 1
):
    '''fills missing dates'''

    current_gamelog = current_gamelog.rename(columns={f"T{team_idx}_TEAM_ID": "TEAM_ID"})
    gamelog_team_combined = pd.merge(current_gamelog, current_year_stat, on=["GAME_DATE", "DAY_WITHIN_SEASON", "TEAM_ID"], how="left")
    
    missing_idx = gamelog_team_combined["lag08_W_PCT"].isna()
    missing_stat = gamelog_team_combined.loc[missing_idx, [ "GAME_DATE", "DAY_WITHIN_SEASON", "TEAM_ID"]]

    current_year_stat["is_prev"] = 1
    prev_year_stat["is_prev"] = 0
    missing_stat["is_prev"] = 1
    missing_stat["TEAM_ID_c"] = missing_stat["TEAM_ID"]

    df_stat_pair = pd.concat([prev_year_stat, current_year_stat])
    
    df_stat_pair["TEAM_ID_c"] = df_stat_pair["TEAM_ID"]

    df_stat_pair_filled = pd.concat([df_stat_pair, missing_stat]).reset_index(drop=True).sort_values(
        by=["GAME_DATE", "DAY_WITHIN_SEASON", "TEAM_ID"], ignore_index=True).groupby("TEAM_ID_c").ffill().sort_values(
            by=["GAME_DATE", "DAY_WITHIN_SEASON", "TEAM_ID"], ignore_index=True)
    return df_stat_pair_filled.loc[df_stat_pair_filled["is_prev"]==1,:].drop(columns=["is_prev"]).reset_index(drop=True)


def fill_past_teamstat_playoff(
    current_playoff_stat: pd.DataFrame,
    current_regular_stat: pd.DataFrame,
):
    '''fill past playoff'''
    playoff_start = current_playoff_stat["GAME_DATE"].min()
    playoff_idx = current_regular_stat["GAME_DATE"] >= playoff_start

    current_regular_stat = current_regular_stat.loc[playoff_idx,:]

    playoff_stat_filled = pd.concat([current_playoff_stat, current_regular_stat])

    target_cols = list(playoff_stat_filled.columns)
    target_cols.remove('TEAM_ID')
    target_cols.remove('GAME_DATE')
    target_cols.remove("DAY_WITHIN_SEASON")
    
    playoff_stat_filled = playoff_stat_filled.groupby(["GAME_DATE", "DAY_WITHIN_SEASON", "TEAM_ID"]).apply(weighted, target_cols).reset_index()    

    return playoff_stat_filled


def weighted(x, cols, w="lag08_GP"):
    return pd.Series(np.average(x[cols], weights=x[w], axis=0), cols)
