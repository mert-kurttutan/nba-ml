#!/usr/bin/env python3
'''Script for webscraping from nba2k website'''

# Local modules
from nbaetl import extract, utils
from nbaetl.enums import FileConfig


if __name__ == "__main__":

    data_config = extract.define_config_vars(FileConfig)
    year_array = [
        "2009", "2010", "2011", "2012", "2013",
        "2014", "2015", "2016", "2017", "2018",
        "2019", "2020", "2021",
    ]
    extract.run_extract_nba2k_batch(year_array, data_config, FileConfig)
    utils.clear_dir(FileConfig.ROOT_RAW)
