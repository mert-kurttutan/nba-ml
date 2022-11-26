#!/usr/bin/env python3
'''Script for extracting gamelog info
'''

# Local modules
from nbaetl import extract, utils
from nbaetl.enums import FileConfig


if __name__ == "__main__":

    data_config = extract.define_config_vars(FileConfig)

    cli_args = extract.cli()
    year_arr = [int(year) for year in cli_args.year_arr]

    if year_arr == [-1]:
        print("Current mode is chosen...")
        year_arr = [2013]

    extract.run_extract_gamelog_batch(year_arr, data_config, FileConfig)
    # extract.update_config(data_config, is_upload=True, file_config=FileConfig)
    utils.clear_dir(FileConfig.ROOT_RAW)
