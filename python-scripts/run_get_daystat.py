#!/usr/bin/env python3
'''Script to get player stat
'''

# Local modules
from nbaetl import extract, utils
from nbaetl.enums import FileConfig


if __name__ == "__main__":
    # date_today = str(date.today())
    CURRENT_DATE = "2014-02-02"
    CURRENT_YEAR = 2013
    data_config = extract.define_config_vars(FileConfig)

    value = extract.cli()
    year_arr = [int(year) for year in value.year_arr]
    STAT_TYPE = 'teamstat'
    if year_arr == [-1]:
        print("Current mode is chosen!!!!")
        current_season = f'{CURRENT_YEAR}_regular'
        extract.extract_daystat_season(
            STAT_TYPE, current_season,  CURRENT_DATE, CURRENT_DATE, FileConfig, data_config
        )
    else:
        extract.run_extract_daystat_batch(STAT_TYPE, year_arr, data_config, FileConfig)

    utils.clear_dir(FileConfig.ROOT_RAW)
