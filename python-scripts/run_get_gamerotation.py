#!/usr/bin/env python3
'''Script for extracting gamerotation info
'''

# Local modules
from nbaetl import extract, utils
from nbaetl.enums import FileConfig


if __name__ == "__main__":

    CURRENT_YEAR = 2013
    data_config = extract.define_config_vars(FileConfig)

    value = extract.cli()
    year_arr = [int(year) for year in value.year_arr]

    if year_arr == [-1]:
        print("Current mode is chosen...")
        year_arr = [CURRENT_YEAR]

    extract.run_extract_gamerotation_batch(year_arr, data_config, FileConfig)
    utils.clear_dir(FileConfig.ROOT_RAW)
