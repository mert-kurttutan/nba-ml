'''Utils module for NBA ETL'''
import os
from datetime import datetime, timedelta
import pandas as pd

season_format_dict = {
    'regular': 'Regular Season',
    'playoff': 'Playoffs'
}


def format_year(year: str | int):
    '''Required for nba stats endpoint'''
    return f"{year}-{str(int(year)+1)[-2:]}"


def format_season_type(season_type: str):
    '''Required for nba stats endpoint'''
    return season_format_dict[season_type]


def clear_dir(root_data_dir:str):
    'After data processing, delete unnecessary folders'
    # After uploading this directory, delete it
    # Since its presence is not needed anymore
    os.system(f"rm -rf {root_data_dir}/")


def get_relative_day(start_date_str:str, date: str):
    '''relative day with respect to start date'''
    current_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    return (current_date - start_date).days


def add_suffix(col_arr: list, suffix: str):
    return {col:col+suffix for col in col_arr}


def add_prefix(col_arr: list, prefix: str):
    return {col:prefix+col for col in col_arr}


def sort_df_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reindex(sorted(df.columns), axis=1)
    return df


def daterange(start_date, end_date):
    '''dateragne'''
    _start_date = (
        datetime.strptime(start_date, "%Y-%m-%d").date() if isinstance(start_date, str)
        else start_date
    )
    _end_date = (
        datetime.strptime(end_date, "%Y-%m-%d").date() if isinstance(end_date, str) else end_date
    )

    for n in range(int((_end_date - _start_date).days)+1):
        yield _start_date + timedelta(n)
