# Data and ETL

File naming convention for tabular data that requires start_year and season_type:

```python
stat_type = 'gamelog'
start_year = 2010
season_type = 'regular' # or 'playoff'

filename = f'{stat_type}_{start_year}_{season_type}.csv'

```

File naming convention for tabular data that requires start_year, season_type and day:

```python
stat_type = 'playerstat'
start_year = 2010
season_type = 'regular' # or 'playoff'
date = '2010-10-30'

filename = f'{stat_type}_{start_year}_{season_type}_{date}.csv'

```
