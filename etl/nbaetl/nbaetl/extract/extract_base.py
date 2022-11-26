'''Module for Extracting data for NBA data'''

from math import floor
import os
import json
import argparse


import requests
import pandas as pd

from nbaetl.enums import FileConfig


def cli():
    '''cli for python scripts'''
    parser = argparse.ArgumentParser(description='Arguments for mlflow python script')
    parser.add_argument(
        "--year-arr", nargs="+", default=["-1"], help="List of years to process data of"
    )
    # parser.add_argument('--is-upload', action='store_true')
    value = parser.parse_args()

    return value


def define_config_vars(
    file_config: FileConfig,
):
    '''Extract config data and define'''
    print("Defining config vars...")

    # Copy config file from s3 bucket
    os.system(
        f"aws s3 cp s3://{file_config.CONFIG_BUCKET}/{file_config.DATA_CONFIG} "
        f"{file_config.ROOT_RAW}/{file_config.DATA_CONFIG} >> ~/entrypoint_log.log "
    )

    with open(f"{file_config.ROOT_RAW}/{file_config.DATA_CONFIG}",
        "r", encoding='utf-8') as read_content:
        config = json.load(read_content)

    return config


def rotate_proxy(
    proxy_arr, proxy_idx, _request_func, rotation_period, *args
):
    '''Keep trying different proxies until request is successful'''
    request_failed = True
    proxy_num = len(proxy_arr)
    while request_failed:
        # time.sleep(random.randint(1, 3))
        # Change proxy at every trial, both success and failure
        proxy_idx = (proxy_idx + 1/rotation_period) % proxy_num

        try:
            # proxy setting
            proxy_str = proxy_arr[floor(proxy_idx)]
            proxy_config = {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}

            # extra data
            _request_func(*args, proxy_config=proxy_config)

            # Update
            request_failed = False
            print("Succeeded in this proxy, going to next query...")

        # Handle only if there is problem with connecting to proxy
        # since this is the only exception type expected to happen
        except requests.exceptions.ProxyError:
            print("Did not succeed in this proxy, Trying another one...")

        except requests.exceptions.JSONDecodeError:
            print('Json decodeerror, trying another proxy')

    return proxy_idx


def json_to_dataframe(json_data):
    """Transforms json data extracted from nba api into list of dataframes and returns it"""
    # Based on this API, there are two possible options for resultant data
    # resultSet or resultSets

    # list of pandas dataframe
    dataframe_arr = []

    # Process one resultSet
    if "resultSet" in json_data:
        rows = json_data['resultSet']['rowSet']
        columns = json_data['resultSet']['headers']
        result_df = pd.DataFrame(rows, columns=columns)
        dataframe_arr.append(result_df)

    elif "resultSets" in json_data:
        for result_set in json_data['resultSets']:
            rows = result_set['rowSet']
            columns = result_set['headers']
            result_df = pd.DataFrame(rows, columns=columns)
            dataframe_arr.append(result_df)

    return dataframe_arr
