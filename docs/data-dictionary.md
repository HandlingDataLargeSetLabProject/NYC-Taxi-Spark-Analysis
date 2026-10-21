# Data dictionary

## Source
- Name: NYC TLC Yellow Taxi Trip Records
- Publisher: New York City Taxi and Limousine Commission (TLC)
- Page: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Official field descriptions: Yellow Trips Data Dictionary (TLC, 18 March 2025), linked from the page above
- Files: one Parquet file per month, `yellow_tripdata_YYYY-MM.parquet`, plus the Taxi Zone Lookup Table (`taxi_zone_lookup.csv`)
- Months used: January to March 2025 (default of `scripts/download_data.py`)
- File size: about 59 MB (Jan), 60 MB (Feb) and 70 MB (Mar) as reported by the download server on 21 Oct 2026; the zone lookup table is about 12 KB
- Number of records: filled in after loading (task R1-06)
- Notes from the publisher: the trip data was collected by technology providers, not created by the TLC, and the TLC makes no claims about its accuracy. Data is published monthly with about a two-month delay. From 2025 the files have a new `cbd_congestion_fee` column.

## Raw trip columns
Descriptions follow the official data dictionary. Types and missing-value counts are filled in after loading (task R1-06).

| Column | Type | Description | Missing values |
|---|---|---|---|
| `VendorID` | | Technology provider of the record: 1 Creative Mobile Technologies, 2 Curb Mobility, 6 Myle Technologies, 7 Helix | |
| `tpep_pickup_datetime` | | Date and time when the meter was engaged | |
| `tpep_dropoff_datetime` | | Date and time when the meter was disengaged | |
| `passenger_count` | | Number of passengers, reported by the driver | |
| `trip_distance` | | Trip distance in miles reported by the taximeter | |
| `RatecodeID` | | Final rate code: 1 standard, 2 JFK, 3 Newark, 4 Nassau or Westchester, 5 negotiated fare, 6 group ride, 99 unknown | |
| `store_and_fwd_flag` | | `Y` if the record was stored in the vehicle before sending because there was no connection, else `N` | |
| `PULocationID` | | Taxi zone where the meter was engaged (joins to `LocationID` in the zone table) | |
| `DOLocationID` | | Taxi zone where the meter was disengaged (joins to `LocationID` in the zone table) | |
| `payment_type` | | 0 flex fare, 1 credit card, 2 cash, 3 no charge, 4 dispute, 5 unknown, 6 voided trip | |
| `fare_amount` | | Time-and-distance fare calculated by the meter | |
| `extra` | | Miscellaneous extras and surcharges | |
| `mta_tax` | | Tax triggered by the metered rate in use | |
| `tip_amount` | | Tip, filled in automatically for credit card payments; cash tips are not included | |
| `tolls_amount` | | Total tolls paid in the trip | |
| `improvement_surcharge` | | Improvement surcharge charged at the flag drop (since 2015) | |
| `total_amount` | | Total charged to the passenger, without cash tips | |
| `congestion_surcharge` | | New York State congestion surcharge for the trip | |
| `airport_fee` | | Fee for pickups at LaGuardia and JFK airports only | |
| `cbd_congestion_fee` | | Per-trip charge for the MTA Congestion Relief Zone, from 5 January 2025 | |

## Taxi zone lookup table
| Column | Type | Description |
|---|---|---|
| `LocationID` | | Zone id used by `PULocationID` and `DOLocationID` |
| `Borough` | | Borough of the zone |
| `Zone` | | Zone name |
| `service_zone` | | Service area of the zone |

The column names of the lookup table are checked when it is loaded (task R1-06).

## Cleaned table
Filled in by the cleaning tasks (R1-05, R1-07).

| Column | Type | Change from raw | Notes |
|---|---|---|---|
