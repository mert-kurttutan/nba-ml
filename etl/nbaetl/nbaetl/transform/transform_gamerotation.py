'''transform gamerotation'''

import os

from pathlib import Path

import pandas as pd

from nbaetl.enums import FileConfig

GAMEROTATION_KEEP_COLS = ["PERSON_ID", "PLAYER_FIRST", "PLAYER_LAST", "TEAM_ID"]

def run_transform_gamerotation_batch(
    year_arr: list[int],
    file_config: FileConfig,
    is_upload: bool = True,
    save_array: bool = False,
):
    '''runs batch'''
    # Make sure gamerotation diretory exists
    Path(f'{file_config.ROOT_TRANSFORMED}/{file_config.GAMEROTATION}/'
    ).mkdir(parents=True, exist_ok=True)

    for year in year_arr:
        for season_type in ['regular', 'playoff']:
            season_dir = f"{year}_{season_type}"
            os.system(
                f"aws s3 cp s3://{file_config.ROOT_RAW}/{file_config.GAMEROTATION}/{season_dir} "
                f"{file_config.ROOT_RAW}/{file_config.GAMEROTATION}/{season_dir} --recursive "
                f"--exclude \"*\" --include \"*.csv\" " )

    print("Extracting Game Rotation data...")
    raw_directory = f'{file_config.ROOT_RAW}/{file_config.GAMEROTATION}'
    df_gamerotation_transformed_arr = []
    for season in os.listdir(raw_directory):
        season_dir = os.path.join(raw_directory, season)
        df_gamerotation_season = pd.DataFrame({'A' : []})
        for gamerotation_file in os.listdir(season_dir):
            if not ".csv" in gamerotation_file:
                continue

            full_path = os.path.join(season_dir, gamerotation_file)
            df_gamerotation = pd.read_csv(full_path)

            df_gamerotation = transform_gamerotation_game(
                df_gamerotation, gamerotation_file
            )

            if df_gamerotation_season is None:
                df_gamerotation_season = df_gamerotation

            else:
                df_gamerotation_season = pd.concat(
                    [df_gamerotation_season, df_gamerotation], ignore_index=True
                )

        df_gamerotation_season.to_csv(
            f"{file_config.ROOT_TRANSFORMED}/{file_config.GAMEROTATION}/gamerotation_map_{season}.csv",
            index=False
        )

        if save_array:
            df_gamerotation_transformed_arr.append(df_gamerotation_season)

    if is_upload:
        os.system(
            f"aws s3 cp {file_config.ROOT_TRANSFORMED}/{file_config.GAMEROTATION} "
            f"s3://{file_config.ROOT_TRANSFORMED}/{file_config.GAMEROTATION}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" " )

    return df_gamerotation_transformed_arr


def transform_gamerotation_game(
    gamerotation: pd.DataFrame,
    gamerotation_file: str,
):
    '''transofrms single gamerotain file'''
    start_idx, last_idx = (
        gamerotation_file.find('_'), gamerotation_file.find('.csv')
    )
    game_id = gamerotation_file[start_idx+1:last_idx]
    gamerotation = gamerotation[GAMEROTATION_KEEP_COLS]
    gamerotation = gamerotation.drop_duplicates(ignore_index=True)
    gamerotation["GAME_ID"] = int(game_id)

    # change player_id column name for it to be compatible with other tables
    gamerotation = gamerotation.rename(columns={"PERSON_ID": "PLAYER_ID"})
    return gamerotation
