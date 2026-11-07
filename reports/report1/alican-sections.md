# Report 1: sections by Alican

These sections go into the final Report 1 document. The numbers come from `docs/data-dictionary.md` and from the scripts named under each table, run on all six months.

## 1. Dataset

*Written by Alican Kaya*

We use the yellow taxi trip records of New York City, published by the NYC Taxi and Limousine Commission (TLC) on its Trip Record Data page (https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Every row is one taxi trip: when and where the meter was switched on and off, the distance, the number of passengers, how the trip was paid and every part of the price. The TLC publishes one Parquet file per month, and a small lookup table (`taxi_zone_lookup.csv`) gives the borough and zone name for each of the 265 zone ids used in the trips.

We chose this dataset for three reasons. It is large enough to make Spark worth using: about 20 million rows for our six months. It has time, place and money in the same row, so the queries for Report 2 need filtering, grouping, aggregation and a join with the zone table. And since 5 January 2025 there is a new charge for trips into the Manhattan congestion relief zone, which gives us a real question to answer instead of only describing the data.

We use January to March of 2024 and January to March of 2025. At first we planned to add December 2024 to the first quarter of 2025, but December has Christmas and New Year, which would mix with the effect of the new charge. The same three months one year earlier are the fairer comparison: same season, same kind of weather, but no charge. `scripts/download_data.py` downloads exactly these six files and the zone table into `data/raw/`.

Table 1.1. Size of the raw data

| Month | Rows | File size |
|---|---|---|
| January 2024 | 2,964,624 | about 50 MB |
| February 2024 | 3,007,526 | about 50 MB |
| March 2024 | 3,582,628 | about 60 MB |
| January 2025 | 3,475,226 | about 59 MB |
| February 2025 | 3,577,543 | about 60 MB |
| March 2025 | 4,145,257 | about 70 MB |
| Total | 20,752,804 | about 350 MB |

Source: `scripts/profile_raw_data.py` for the rows; file sizes after download. The zone lookup table has 265 rows and is about 12 KB.

The raw table has 20 columns (19 in the 2024 files, which do not have `cbd_congestion_fee` yet). Their types and meaning are listed in `docs/data-dictionary.md`, which follows the official TLC data dictionary. The TLC notes that the records come from the technology providers in the taxis and that it does not guarantee their accuracy. We found several examples of this during cleaning (Section 6), so we checked every rule against the data before using it.

## 2. Analytical problem

*Written by Alican Kaya*

Our question for the whole project is:

**How do demand, prices and tipping of NYC yellow taxi trips change by time and place in the first quarter of 2025 compared with the first quarter of 2024, and how much of this traffic is affected by the new Manhattan congestion relief zone charge?**

The congestion relief zone charge (`cbd_congestion_fee`) started on 5 January 2025, so the first quarter of 2025 is the first quarter with the charge in the data, and the first quarter of 2024 shows the same season without it. The question fits the data well: the timestamps answer "when", the pickup and drop-off zones answer "where", and the price columns answer "how much". It also fits Spark: the trip table has millions of rows while the zone table has 265, which is the typical case for a broadcast join that we want to test in Report 2.

We do not try to prove that the charge caused every change. Many things differ between two years, for example the share of flex fare trips (Section 6.2). What we can show is what changed, where and when, and how the trips that pay the charge differ from the others.

## 3. Objectives for Reports 2 and 3

*Written by Alican Kaya*

We split the question into four objectives. Each one has one query in Report 2 and at least one chart in Report 3. The full plan is in `docs/analysis-plan.md`.

Table 3.1. Objectives, queries and owners

| Objective | What we want to find out | Query (Report 2) | Owner |
|---|---|---|---|
| O1, demand over time | When people take taxis (hour of day, day of week) and how daily demand moves from January to March | Q1: group trips by date, hour and weekday, count, compare daily averages | Alican |
| O2, prices and tips | How price per mile, trip speed and tip percentage change by hour and payment type | Q2: derived columns, group by hour and payment type, averages and percentiles | Alican |
| O3, places | Which zones and boroughs have the most pickups and drop-offs, and which routes are the busiest | Q3: join with the zone table, group by borough and zone pair, top-N | Berke |
| O4, congestion relief zone | How demand and prices changed from before the charge to after it, and how the trips that pay it differ from the others | Q4: trips with `cbd_congestion_fee` above 0, join with zones, shares by zone and hour, year comparison | Berke |

A few choices are fixed already, because the cleaning showed that they matter:

- We compare the two years by daily averages, because the first quarter of 2024 has 91 days and the first quarter of 2025 has 90.
- We mark the time before the charge by date, not by a missing value. The 2024 files have no `cbd_congestion_fee` at all, and 1 to 4 January 2025 has it as 0.
- In the price queries (Q2 and Q4) we use `total_amount` and leave out the trips marked `has_negative_part` (Section 6.4). These trips stay in the demand counts (Q1 and Q3).
- Flex fare trips are shown as their own group in Q2. Their share of the cleaned rows grows from 7.05% in 2024 to 19.47% in 2025, so an average over all trips would change only because the mix of trips changed.
- The tip percentage is measured only for credit card payments, because cash tips are not recorded in the data.
- Trip durations are computed from New York local time. On 10 March 2024 and 9 March 2025 the clocks in New York jumped from 02:00 to 03:00, and 2,360 trips that cross this hour would otherwise look exactly one hour longer (median 75 minutes instead of 15, from `scripts/check_summer_time.py`).

For the optimizations in Report 2 we plan to test caching of the cleaned table (Alican), a broadcast join with the zone table (Berke) and Parquet output partitioned by pickup date (Berke), each measured before and after on the same data, the same Spark settings and the same laptop. In Report 3 we plan a heat map of trips by hour and weekday and a daily trend line (O1), charts of tip percentage and speed by hour (O2), the top zones and routes (O3), the share of trips that pay the charge by hour and zone (O4), and a chart of the execution times before and after each optimization.

## 6. Data cleaning

*Sections 6.1 to 6.4 and 6.6 written by Alican Kaya (49429), Section 6.5 by Berke Arda Türk (58169).*

### 6.1 Approach

All cleaning steps are in `src/hlds/cleaning.py`, and `clean_trips` runs them in a fixed order. Each step takes a DataFrame and returns a new one, so every step can be tested on its own with a few hand-made rows (`tests/test_cleaning.py`, `tests/test_invalid_rows.py`).

1. `clean_missing_values_and_types` keeps every row. It adds two flag columns, converts types and turns hidden missing values into real ones.
2. `drop_invalid_rows` removes rows that cannot be real trips or that we cannot use, and `add_negative_part_flag` marks rows with a negative price part.
3. `drop_duplicate_rows` removes exact duplicates.

The flags are added first, while the missing values still come only from the raw files. Before we wrote a rule, we measured how many rows it touches in each year, because a rule that removes much more in one year than in the other would change the comparison by itself.

### 6.2 Missing values

Most columns have no missing values. Five columns are missing on exactly the same rows: `passenger_count`, `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` and `Airport_fee`. These are 751,962 rows in 2024 (7.87%) and 2,263,749 rows in 2025 (20.22%). When we looked at these rows, all of them have `payment_type` 0, which the data dictionary calls "flex fare", and no other row has this code. So the missing values are not random errors: flex fare trips are recorded with fewer details.

We keep these trips, because removing them would remove a fifth of the 2025 demand and much less of 2024. Instead we add a column `details_missing`, so that every query can show or leave out these trips on purpose. We do not fill `congestion_surcharge` and `Airport_fee` with 0, because we do not know whether these trips paid them.

Two columns also hide missing values behind a normal-looking number. `RatecodeID` 99 means "unknown" in the data dictionary. `passenger_count` 0 is not described there; the field description only says that the driver enters the number. A paid trip with no passenger is unlikely, so we decided to read 0 as a count that was not entered. This is our own decision, not a rule from the TLC. Both values become missing.

`cbd_congestion_fee` does not exist in the 2024 files. When Spark reads the six files together with `mergeSchema`, the column is null for every 2024 row, and we never read this null as 0.

Table 6.1. Missing values after the first cleaning step

| Column | 2024 | 2025 |
|---|---|---|
| `passenger_count` | 857,893 (751,962 flex fare rows and 105,931 zeros) | 2,332,871 (2,263,749 and 69,122) |
| `RatecodeID` | 848,661 (751,962 flex fare rows and 96,699 with 99) | 2,388,832 (2,263,749 and 125,083) |
| `store_and_fwd_flag`, `congestion_surcharge`, `Airport_fee` | 751,962 | 2,263,749 |
| `cbd_congestion_fee` | 9,554,778 (column not in the files) | 0 |

Source: run of `clean_missing_values_and_types` on all six months; the same numbers are in `docs/data-dictionary.md`.

### 6.3 Type conversions

Spark reads `passenger_count`, `RatecodeID` and `payment_type` as long, although they are small codes and counts, so we convert them to int. `store_and_fwd_flag` is the text `Y` or `N`, and we convert it to a boolean. The timestamps are already `timestamp_ntz` (a date and time without a time zone), which is correct for local New York clock times, and the money columns are already double.

### 6.4 Flag columns

Table 6.2. New columns in the cleaned table

| Column | True for | Rows |
|---|---|---|
| `details_missing` | flex fare trips, where the five columns above are missing | 2024: 751,962; 2025: 2,263,749 (before invalid rows are dropped) |
| `charge_in_force` | pickups from 5 January 2025, 00:00 | 2024: 0; 2025: 10,833,929 (before invalid rows are dropped) |
| `has_negative_part` | a price part is negative but `total_amount` is not | 2024: 20,862; 2025: 315,192 (cleaned table) |

`charge_in_force` is decided by date. Our first idea was "null means before the charge", but in 2025 the days before the start are 0 rather than null, and 401 rows on the evening of 4 January already have a positive charge. With a date rule the period before the charge is the same in every query.

`has_negative_part` comes from a finding Berke made while he measured the rules for invalid rows. Our first plan was to drop every row with a negative amount. When he measured it, it would have removed 3.64% of 2024 but 7.03% of 2025. Most of these 2025 rows were flex fare trips with a negative `fare_amount` but a positive total (median total 3.74 dollars), so they are not refunds. Dropping them would have lowered the 2025 demand only because of the way the data is recorded. So we drop only rows with a negative `total_amount` and mark the others. They count as trips for demand, but the price queries leave them out.

### 6.5 Invalid and duplicate rows

*Written by Berke Arda Türk*

A row is dropped when it cannot be a real trip or when it would distort the averages. Table 6.3 shows how many rows each rule matches. A row can match more than one rule, so the rules add up to more than the dropped total.

Table 6.3. Invalid and duplicate rows

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

Source: `scripts/profile_cleaning.py`, run on all six months.

Why each rule:

- **Pickup outside the quarter.** Each monthly file has a few rows from other dates; the data does not tell us why. We keep a row when its pickup is anywhere in January to March of 2024 or 2025, even if it is in the file of a neighbouring month, so only 46 rows are dropped.
- **Drop-off before or at the same second as pickup.** A trip cannot end before it starts, and a taxi cannot cover a distance in 0 seconds, so we do not count these rows as trips. The rows of 0 seconds grew from 2,621 to 29,197, so keeping them would have raised the demand of 2025 much more than that of 2024.
- **Duration over 5 hours.** A normal taxi trip in New York is far shorter, so these are most likely meters that were left running.
- **Distance of 0 or below.** This is the largest rule. Without a distance we cannot compute speed or price per mile, and the data does not say whether the taxi moved at all.
- **Distance over 100 miles.** 99.92% of the raw rows are under 30 miles, while the largest values reach 320,136 miles, which is impossible for a taxi trip. 100 miles still keeps long airport and out-of-town trips.
- **Negative `total_amount`.** Most of these rows look like reversals or refunds of another trip: a strict match finds the original of many of them, but not of all (Sections 6.4 and 6.6).
- **`total_amount` over 2,000 dollars.** The raw data has 13 such rows, and the other rules already drop 11 of them. The two that are left are from 2025: 863,380.37 and 132,555.41 dollars for trips under 3 miles. The next largest amount is 1,021.99. These two rows alone raised the 2025 mean of `total_amount` by about 0.10 dollars.
- **Exact duplicates.** Only one row in the six months is an exact copy of another, so this rule hardly changes anything, but it makes sure that no trip is counted twice.

The cleaned table has 19,926,016 rows. Flex fare trips lose more rows than the others: 13.52% in 2024 and 8.01% in 2025, against 2.56% and 3.56%, mostly because of distances of 0. The rules remove 3.43% of 2024 and 4.46% of 2025. This difference is much smaller than the 3.64% and 7.03% of our first draft, but it is still there, so in Report 2 we will check that the changes we find between the years are larger than this.

### 6.6 Limitation

When a trip is refunded, the data has the original trip and a second row with the negative total. We drop the negative row, but the original stays, because we cannot always be sure which row it reverses. With a strict match (same vendor, pickup and drop-off time, pickup and drop-off zone, and the opposite total) we find 90,868 such trips in 2024 (0.93% of `total_amount`) and 148,495 in 2025 (1.47%). This makes the price averages slightly too high, more in 2025 than in 2024, and we will keep it in mind when we compare prices in Report 2. Berke noticed this limitation while he wrote the rules, and we agreed to report it instead of guessing which rows to remove.
