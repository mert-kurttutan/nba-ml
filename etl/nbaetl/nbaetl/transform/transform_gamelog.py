'''transform gamelog'''

import os

from functools import partial
from pathlib import Path

import pandas as pd

from nbaetl.utils import (
    get_relative_day, add_prefix, sort_df_cols
)
from nbaetl.enums import FileConfig



def run_transform_gamelog_batch(
    year_arr: list[int],
    file_config: FileConfig,
    is_upload: bool = True,
    save_array: bool = False
):
    '''transform gamelog'''

    # Make sure gamelog diretory exists
    Path(f'{file_config.ROOT_TRANSFORMED}/{file_config.GAMELOG}/'
    ).mkdir(parents=True, exist_ok=True)

    for year in year_arr:
        for season_type in ['regular', 'playoff']:
            file_name = f"gamelog_{year}_{season_type}.csv"
            os.system(
                f"aws s3 cp "
                f"s3://{file_config.ROOT_RAW}/{file_config.GAMELOG}/{file_name} "
                f"{file_config.ROOT_RAW}/{file_config.GAMELOG}/{file_name} "
            )


    print("Extracting Gamelog data...")
    raw_directory = f'{file_config.ROOT_RAW}/{file_config.GAMELOG}'
    df_gamelog_transformed_arr = []
    for gamelog_file in os.listdir(raw_directory):
        if not ".csv" in gamelog_file:
            continue
        full_path = os.path.join(raw_directory, gamelog_file)
        df_gamelog = pd.read_csv(full_path)
        df_gamelog_transformed = transform_gamelog(df_gamelog, False)
        df_gamelog_transformed = sort_df_cols(df_gamelog_transformed)
        df_gamelog_transformed.to_csv(
            f"{file_config.ROOT_TRANSFORMED}/{file_config.GAMELOG}/{gamelog_file}", index=False
        )
        # Append transformed data of current season into total data
        if save_array:
            df_gamelog_transformed_arr.append(df_gamelog_transformed)

    if is_upload:
        os.system(
            f"aws s3 cp {file_config.ROOT_TRANSFORMED}/{file_config.GAMELOG} "
            f"s3://{file_config.ROOT_TRANSFORMED}/{file_config.GAMELOG}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" " )


    return df_gamelog_transformed_arr


def transform_gamelog(
    df_gamelog: pd.DataFrame, sort_by_home: bool = True
) -> pd.DataFrame:
    '''transform gamelog'''

    sort_col = 'IS_HOME' if sort_by_home else 'TEAM_ID'

    redundant_cols = ["Unnamed: 0","VIDEO_AVAILABLE", "MIN", "TEAM_ABBREVIATION", "SEASON_ID"]
    ordered_cols = [
        'GAME_ID', 'GAME_DATE', 'DAY_WITHIN_SEASON', 'TEAM_ID', 'TEAM_NAME',
        'WL', 'PTS', 'PLUS_MINUS', "IS_HOME"
    ]

    # Eliminate columns that will lead to data leakage
    # namely any data that resulted in during the game
    # e.g. percentage of 3 point shots, free throws, etc
    # other than prediction labels
    data_leakage_cols = [
        'FGM', 'FGA', 'FG_PCT','FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA',
        'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF',
    ]

    df_gamelog = df_gamelog.drop(redundant_cols+data_leakage_cols, axis=1)

    # Boolean column to indicate whether the team is home team or not
    df_gamelog["IS_HOME"] = df_gamelog["MATCHUP"].apply(is_home)

    # Unnecessary column
    df_gamelog.drop(["MATCHUP"], axis=1, inplace=True)

    df_gamelog.sort_values(by=["GAME_DATE", "GAME_ID", sort_col], inplace=True)

    # Relative point of match within season (relative to start of the season)
    start_date = df_gamelog["GAME_DATE"].min()
    df_gamelog["DAY_WITHIN_SEASON"] = (
        df_gamelog["GAME_DATE"].apply(partial(get_relative_day, start_date))
    )
    # Convenient column order
    df_gamelog = df_gamelog[ordered_cols]

    df_gamelog["W"] = (df_gamelog["WL"]=="W").astype("int32")
    df_gamelog["L"] = 1 - df_gamelog["W"]
    df_gamelog.drop(columns=["WL"], inplace=True)

    df1_gamelog = (df_gamelog.iloc[::2]).reset_index(drop=True)
    df2_gamelog = (df_gamelog.iloc[1::2]).reset_index(drop=True)


    # tag team number to column names
    # first team that appears is the visitor team
    cols = ['TEAM_ID', 'TEAM_NAME', 'WL', "PTS", "PLUS_MINUS", "W", "L", "IS_HOME"]
    col_map1 = add_prefix(cols, "T1_")
    col_map2 = add_prefix(cols, "T2_")
    df1_gamelog = df1_gamelog.rename(columns = col_map1)
    df2_gamelog = df2_gamelog.rename(columns = col_map2)

    # Merge teams into one row where info about two team is contained
    df2_gamelog.drop(columns=["GAME_ID", "GAME_DATE", "DAY_WITHIN_SEASON"], inplace=True)
    final_gamelog = pd.concat([df1_gamelog, df2_gamelog], axis=1)#.T.drop_duplicates().T


    # Add win/loss for series between two teams
    team1_id_arr = list(final_gamelog["T1_TEAM_ID"].unique())
    team2_id_arr = list(final_gamelog["T2_TEAM_ID"].unique())

    for team1_id in team1_id_arr:
        for team2_id in team2_id_arr:
            matchup_cond = (
                (final_gamelog["T1_TEAM_ID"] == team1_id) &
                (final_gamelog["T2_TEAM_ID"] == team2_id)
            )
            #  cumulative W/L for team 1
            final_gamelog.loc[matchup_cond, "T1_W_cum"] = (
                final_gamelog.loc[matchup_cond, "T1_W"].rolling(
                    min_periods=1, window=2000).sum().shift(periods=1, fill_value=0)
            )
            final_gamelog.loc[matchup_cond, "T1_L_cum"] = (
                final_gamelog.loc[matchup_cond, "T1_L"].rolling(
                    min_periods=1, window=2000).sum().shift(periods=1, fill_value=0)
            )
    # cumulative W/L for team 2
    final_gamelog["T2_W_cum"] = final_gamelog["T1_L_cum"]
    final_gamelog["T2_L_cum"] = final_gamelog["T1_W_cum"]

    return final_gamelog


def is_home(matchup_str: str):
    '''home teams do not have @ symbol in matchup column'''
    return not "@" in matchup_str
