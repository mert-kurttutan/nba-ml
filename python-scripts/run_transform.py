#!/usr/bin/env python3
'''Script for transforming gamelog info
'''

# Local modules
from nbaetl import transform, extract, utils
from nbaetl.enums import FileConfig



if __name__ == "__main__":

    data_config = extract.define_config_vars(FileConfig)

    cli_args = extract.cli()
    year_arr = [int(year) for year in cli_args.year_arr]

    if year_arr == [-1]:
        print("Current mode is chosen...")
        year_arr = [2013]

    transform.run_transform_gamelog_batch(year_arr, FileConfig)
    transform.run_transform_daystat_batch('teamstat', year_arr, data_config, FileConfig)
    transform.fillpast_daystat('teamstat', year_arr, FileConfig)
    # transform.run_transform_gamerotation_batch(year_arr, FileConfig)
    # transform.run_transform_daystat_batch('playerstat', year_arr, data_config, FileConfig)
    utils.clear_dir(FileConfig.ROOT_RAW)
    utils.clear_dir(FileConfig.ROOT_TRANSFORMED)
