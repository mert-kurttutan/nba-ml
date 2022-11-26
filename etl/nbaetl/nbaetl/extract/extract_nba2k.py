'''Module for extractr nba2k data
'''
import os
from pathlib import Path


import requests
import pandas as pd
from bs4 import BeautifulSoup, element

from nbaetl.enums import TIMEOUT_LIMTT, FileConfig, NBAEndpoint
from nbaetl.extract.extract_base import (
    rotate_proxy
)


def run_extract_nba2k_batch(
    year_arr: list,
    config_dict: dict,
    file_config: FileConfig,
    upload_result: bool = True
):
    """Extracts data for entire year, regular season+ playoff games"""

    # Make sure parent directories exists
    Path(f'{file_config.ROOT_RAW}/{file_config.NBA2K}/').mkdir(parents=True, exist_ok=True)
    # proxy-related variables
    proxy_arr = config_dict["proxy_arr"]
    proxy_idx = 0

    for year in year_arr:
        proxy_idx = rotate_proxy(
            proxy_arr, proxy_idx, extract_nba2k_year, 2,
            year, file_config
        )

    if upload_result:
        # Upload directory to s3 bucket
        # Exclude jupyter checkpoint files
        os.system(
            f"aws s3 cp {file_config.ROOT_RAW}/{file_config.NBA2K} "
            f"s3://{file_config.ROOT_RAW}/{file_config.NBA2K}/ --recursive "
            f"--exclude \"*\" --include \"*.csv\" "
        )

def extract_nba2k_year(
    year: str | int,
    file_config: FileConfig,
    proxy_config: dict | None = None,
):
    """Extracst NBA2K player data from for one season and type of season
    Stores the data into player_stat_data directory"""

    if proxy_config is None:
        proxy_config = {}

    year_formatted = f"{int(year)}-{int(year)+1}"
    df_file_name = f'{file_config.ROOT_RAW}/{file_config.NBA2K}/nba2k_{year}.csv'

    # Query data only if it does not exist
    if not os.path.exists(df_file_name):
        end_point = f"{NBAEndpoint.NBA2K}/{year_formatted}"
        result_df = get_nba2kstat(end_point, proxy_config)
        result_df.to_csv(df_file_name)


def get_nba2kstat(url: str, proxy_config: dict | None = None) -> pd.DataFrame:
    """Scrapes nba2k rating from url and turns into pandas dataframe"""

    # Get response
    page = requests.get(
        url, proxies=proxy_config, timeout=TIMEOUT_LIMTT
    )

    # Parse the HTML page
    soup = BeautifulSoup(page.text, 'html.parser')

    # Extract table from
    # Tag classes are based on HTML elements of the website
    content = soup.find("div", id='content')
    if not content:
        raise ValueError(
            'Webpage has incompatible html structure, check code and webpage html...'
        )
    content_container = content.find("div", id="content-container")
    if not content_container:
        raise ValueError(
            'Webpage has incompatible html structure, check code and webpage html...'
        )
    table_container = content_container.find("div", class_="hh-ranking-ranking")
    if not table_container:
        raise ValueError(
            'Webpage has incompatible html structure, check code and webpage html...'
        )
    table = table_container.find("tbody")
    if not isinstance(table, element.Tag):
        raise ValueError(
            'Webpage has incompatible html structure, check code and webpage html...'
        )
    names_arr = []
    values_arr = []

    for child in table.children:
        # Some of the child tags are empty strings
        # Bypass these empty strings
        if isinstance(child, element.NavigableString):
            continue

        names_arr.append(child.find("td", class_="name").text.strip())
        values_arr.append(child.find("td", class_="value").text.strip())

    return pd.DataFrame.from_dict({
        "name": names_arr, "rating": values_arr
    })
