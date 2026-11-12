# Data dictionary

## Source
- Name: NYC TLC Yellow Taxi Trip Records
- Publisher: New York City Taxi and Limousine Commission (TLC)
- Page: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Official field descriptions: Yellow Trips Data Dictionary (TLC, 18 March 2025), linked from the page above
- Files: one Parquet file per month, `yellow_tripdata_YYYY-MM.parquet`, plus the Taxi Zone Lookup Table (`taxi_zone_lookup.csv`)
- Months used: January to March 2024 and January to March 2025 (default of `scripts/download_data.py`)
- File size: 2024 about 50 MB (Jan), 50 MB (Feb) and 60 MB (Mar), measured after download on 30 Oct 2026; 2025 about 59 MB (Jan), 60 MB (Feb) and 70 MB (Mar) as reported by the download server on 21 Oct 2026; the zone lookup table is about 12 KB
- Number of records: 20,752,804 trips. 2024: 9,554,778 (Jan 2,964,624, Feb 3,007,526, Mar 3,582,628). 2025: 11,198,026 (Jan 3,475,226, Feb 3,577,543, Mar 4,145,257). The zone lookup table has 265 rows
- Notes from the publisher: the trip data was collected by technology providers, not created by the TLC, and the TLC makes no claims about its accuracy. Data is published monthly with about a two-month delay. From 2025 the files have a new `cbd_congestion_fee` column.

## Raw trip columns
Descriptions follow the official data dictionary. Types and missing-value counts come from `scripts/profile_raw_data.py`, run on all six months. `load_trips` in `src/hlds/loading.py` reads the files, and it fails if a column has a different type in one of them.

| Column | Type | Description | Missing values |
|---|---|---|---|
| `VendorID` | integer | Technology provider of the record: 1 Creative Mobile Technologies, 2 Curb Mobility, 6 Myle Technologies, 7 Helix | 0 |
| `tpep_pickup_datetime` | timestamp_ntz | Date and time when the meter was engaged | 0 |
| `tpep_dropoff_datetime` | timestamp_ntz | Date and time when the meter was disengaged | 0 |
| `passenger_count` | long | Number of passengers, reported by the driver | 2024: 751,962 (7.87%); 2025: 2,263,749 (20.22%) |
| `trip_distance` | double | Trip distance in miles reported by the taximeter | 0 |
| `RatecodeID` | long | Final rate code: 1 standard, 2 JFK, 3 Newark, 4 Nassau or Westchester, 5 negotiated fare, 6 group ride, 99 unknown | 2024: 751,962 (7.87%); 2025: 2,263,749 (20.22%) |
| `store_and_fwd_flag` | string | `Y` if the record was stored in the vehicle before sending because there was no connection, else `N` | 2024: 751,962 (7.87%); 2025: 2,263,749 (20.22%) |
| `PULocationID` | integer | Taxi zone where the meter was engaged (joins to `LocationID` in the zone table) | 0 |
| `DOLocationID` | integer | Taxi zone where the meter was disengaged (joins to `LocationID` in the zone table) | 0 |
| `payment_type` | long | 0 flex fare, 1 credit card, 2 cash, 3 no charge, 4 dispute, 5 unknown, 6 voided trip | 0 |
| `fare_amount` | double | Time-and-distance fare calculated by the meter | 0 |
| `extra` | double | Miscellaneous extras and surcharges | 0 |
| `mta_tax` | double | Tax triggered by the metered rate in use | 0 |
| `tip_amount` | double | Tip, filled in automatically for credit card payments; cash tips are not included | 0 |
| `tolls_amount` | double | Total tolls paid in the trip | 0 |
| `improvement_surcharge` | double | Improvement surcharge charged at the flag drop (since 2015) | 0 |
| `total_amount` | double | Total charged to the passenger, without cash tips | 0 |
| `congestion_surcharge` | double | New York State congestion surcharge for the trip | 2024: 751,962 (7.87%); 2025: 2,263,749 (20.22%) |
| `Airport_fee` | double | Fee for pickups at LaGuardia and JFK airports only (written `airport_fee` in the official dictionary) | 2024: 751,962 (7.87%); 2025: 2,263,749 (20.22%) |
| `cbd_congestion_fee` | double | Per-trip charge for the MTA Congestion Relief Zone, from 5 January 2025. Not present in 2024 files, so it is null when the two years are combined. In 2025 the days before the start are 0 rather than null, except 401 rows on the evening of 4 January | 2024: 9,554,778 (100%, column absent); 2025: 0 |

`passenger_count`, `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` and `Airport_fee` are missing on the same rows in both years: every row that misses one of them misses all five.

## Taxi zone lookup table
| Column | Type | Description |
|---|---|---|
| `LocationID` | integer | Zone id used by `PULocationID` and `DOLocationID` |
| `Borough` | string | Borough of the zone |
| `Zone` | string | Zone name |
| `service_zone` | string | Service area of the zone |

`load_zones` in `src/hlds/loading.py` checks the column names when it reads the file and converts `LocationID` to an integer. No value is missing and all 265 `LocationID` values are distinct, so a join on it does not multiply trips. Every `PULocationID` and `DOLocationID` in the six months is in the table. Two rows hold placeholder text rather than a place: 264 (`Unknown`, `N/A`) and 265 (`N/A`, `Outside of NYC`). Spark reads `N/A` as text, not as a missing value.

## Cleaned table
Filled in by the cleaning tasks (R1-05, R1-07).

`clean_missing_values_and_types` in `src/hlds/cleaning.py` (R1-05) keeps all 20,752,804 rows and changes the columns below; all other columns stay as in the raw table. The counts were measured on all six months on Alican's laptop. Duplicates and invalid rows are handled in R1-07.

| Column | Type | Change from raw | Notes |
|---|---|---|---|
| `passenger_count` | int | long to int; 0 becomes missing | We treat 0 passengers as a count that was not entered. This is our decision, the field description only says that the driver reports the number. Missing: 2024 857,893 (751,962 flex fare rows and 105,931 zeros); 2025 2,332,871 (2,263,749 and 69,122) |
| `RatecodeID` | int | long to int; 99 (unknown) becomes missing | Missing: 2024 848,661 (751,962 flex fare rows and 96,699 with 99); 2025 2,388,832 (2,263,749 and 125,083) |
| `payment_type` | int | long to int | No missing values. Code 0 (flex fare) is found on exactly the rows where `details_missing` is true |
| `store_and_fwd_flag` | boolean | text `Y` / `N` to true / false | Still missing on the flex fare rows |
| `congestion_surcharge`, `Airport_fee` | double | none | Still missing on the flex fare rows. Not filled with 0, because we do not know whether these trips paid them |
| `cbd_congestion_fee` | double | none | Still missing for every 2024 row, never read as 0 |
| `details_missing` | boolean | new | True where the five sparse columns are missing: 2024 751,962, 2025 2,263,749 rows |
| `charge_in_force` | boolean | new | True for pickups from 5 January 2025, 00:00: 0 rows in 2024, 10,833,929 in 2025 |
| `has_negative_part` | boolean | new | True where an amount is negative but `total_amount` is not: 2024 20,862 rows (20,848 flex fare), 2025 315,192 (315,191 flex fare). These trips stay in the demand counts (Q1, Q3) and are left out of the price queries (Q2, Q4) |

`clean_trips` runs the step above, then `drop_invalid_rows` and `drop_duplicate_rows` (R1-07). The counts below come from `scripts/profile_cleaning.py`, run on all six months. A row can match more than one rule, so the rules add up to more than the last line. Years are the years of the files.

| Rule | 2024 | 2025 |
|---|---|---|
| Raw rows | 9,554,778 | 11,198,026 |
| Pickup outside January to March of 2024 and 2025 | 21 | 25 |
| Drop-off before pickup | 180 | 298 |
| Drop-off at the same second as pickup | 2,621 | 29,197 |
| Duration over 5 hours | 5,561 | 3,811 |
| Distance of 0 or below | 215,764 | 294,386 |
| Distance over 100 miles | 252 | 548 |
| Negative `total_amount` | 115,895 | 186,902 |
| `total_amount` over 2,000 dollars | 7 | 6 |
| Rows dropped by any rule | 327,281 (3.43%) | 499,506 (4.46%) |
| Exact duplicates dropped after that | 1 | 0 |
| Rows in the cleaned table | 9,227,496 | 10,698,520 |

The cleaned table has 19,926,016 rows. Flex fare rows lose more than the others: 13.52% in 2024 and 8.01% in 2025, against 2.56% and 3.56%, mostly because of distances of 0. When a negative total is dropped, the trip it reverses stays; `docs/analysis-plan.md` describes how much this is under "Limitations".

## Copies of the cleaned table (O3)
Written by `scripts/write_clean_tables.py` to `data/derived/`, which is not committed. Both copies hold the rows of `clean_trips` and one more column, `pickup_date` (the date of `tpep_pickup_datetime`, New York clock time).

| Folder | Layout | Files | Size |
|---|---|---|---|
| `data/derived/clean_plain` | plain Parquet | 22 | 450 MB |
| `data/derived/clean_by_pickup_date` | Parquet partitioned by `pickup_date`, one folder and one file per day | 181 | 446 MB |

## Query results
Small grouped tables in `results/`, written by the query scripts for the charts of Report 3. Pickup hour and date are New York clock times; `weekday` is 0 for Monday to 6 for Sunday.

| File | Written by | Columns |
|---|---|---|
| `q1_daily_trips.csv` | `scripts/query_demand.py` (Q1) | `year`, `pickup_date`, `trips` |
| `q1_daily_average.csv` | `scripts/query_demand.py` (Q1) | `year`, `days`, `trips`, `trips_per_day` |
| `q1_hour_weekday.csv` | `scripts/query_demand.py` (Q1) | `year`, `weekday`, `hour`, `trips`, `days` (days of that weekday in the quarter), `trips_per_day` |
| `q2_by_payment.csv` | `scripts/query_prices.py` (Q2) | `year`, `payment` (flex fare, credit card, cash, other), `trips`, `median_duration_minutes`, mean and median of `speed_mph`, `price_per_mile` and `tip_pct` (credit card only). Rows with `has_negative_part` are left out |
| `q2_by_hour_payment.csv` | `scripts/query_prices.py` (Q2) | the same columns, also grouped by pickup `hour` |
| `q3_pickup_zones.csv` | `scripts/query_places.py` (Q3) | `year`, `zone_id`, `borough`, `zone`, `trips`, `trips_per_day`, `rank_in_year` (1 is the zone with the most pickups). Zones 264 and 265 are left out, because they are placeholders, not places |
| `q3_dropoff_zones.csv` | `scripts/query_places.py` (Q3) | the same columns for the drop-off zone |
| `q3_borough_flows.csv` | `scripts/query_places.py` (Q3) | `year`, `pickup_borough`, `dropoff_borough`, `trips`, `trips_per_day`, `share` (of all trips of the year). `Unknown` and `N/A` are the boroughs of zones 264 and 265 |
| `q3_top_routes.csv` | `scripts/query_places.py` (Q3) | `year`, `rank_in_year`, `pickup_zone_id`, `pickup_borough`, `pickup_zone`, `dropoff_zone_id`, `dropoff_borough`, `dropoff_zone`, `trips`, `trips_per_day`; the 20 busiest zone pairs of each year, without zones 264 and 265 |
| `q3_airport_trips.csv` | `scripts/query_places.py` (Q3) | `year`, `airport` (zone name of Newark, JFK or LaGuardia), `direction` (`from` the airport or `to` it), `trips`, `trips_per_day`. A trip between two airports counts in both directions |
| `q4_overview.csv` | `scripts/query_congestion.py` (Q4) | `year`, `charge_group` (`all trips`; in 2025 also `pays the charge` and `does not pay`), `trips`, `trips_per_day`, `share` (of all trips of the year), `median_total_amount`, `median_trip_distance`. Both years from 5 January to 31 March; rows with `has_negative_part` are left out |
| `q4_by_hour.csv` | `scripts/query_congestion.py` (Q4) | the same columns, also grouped by pickup `hour`; `share` is within the hour |
| `q4_by_pickup_zone.csv` | `scripts/query_congestion.py` (Q4) | the same columns, also grouped by `zone_id`, `borough` and `zone` of the pickup; `share` is within the zone. Zones 264 and 265 are left out |
| `q4_by_dropoff_zone.csv` | `scripts/query_congestion.py` (Q4) | the same columns for the drop-off zone |
| `timings_<machine>.csv` | `scripts/run_benchmarks.py` | `date`, `optimization`, `variant`, `median_s`, `min_s`, `max_s`, `runs_s`, `cpu`, `logical_cores`, `ram_gb`, `spark_version`, `driver_memory` |
