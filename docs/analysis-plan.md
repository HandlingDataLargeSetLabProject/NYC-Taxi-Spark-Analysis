# Analysis plan

Written for tasks R1-03 and R1-08 and agreed by both of us for Report 1. It stays the same for all three reports; any later change is written under "Decisions".

## Analytical problem
**How do demand, prices and tipping of NYC yellow taxi trips change by time and place in the first quarter of 2025 compared with the first quarter of 2024, and how much of this traffic is affected by the new Manhattan congestion relief zone charge?**

Why this problem:
- The data covers time (pickup and drop-off timestamps), place (pickup and drop-off zones) and money (fare, tip, surcharges), so filtering, grouping, aggregation and a join all come up naturally.
- The zone lookup table is small (265 zones) while the trip table has millions of rows, which is the typical case for a broadcast join.
- The congestion relief zone charge (`cbd_congestion_fee`) started on 5 January 2025, so this quarter is the first one with it in the data. The first quarter of 2024 is the same season one year earlier, without the charge.

## Objectives
1. **O1, demand over time:** when do people take taxis (hour of day, day of week) and how does daily demand move from January to March? We count all trips of the cleaned table, including those marked `has_negative_part`, and compare the two years by daily averages.
2. **O2, prices and tips:** how price per mile, trip speed and tip percentage change by hour and by payment type. Flex fare trips are shown as their own group, because their share grows from 7.05% to 19.47% of the cleaned rows and their tips are much lower.
3. **O3, places:** which zones and boroughs have the most pickups and drop-offs, and which zone-to-zone or airport routes are the busiest.
4. **O4, congestion relief zone, before and after:** how demand and prices changed from before the charge (first quarter of 2024) to after it (first quarter of 2025), what share of trips pays the charge, where and when these trips happen, and how their total price compares with trips that do not pay it. We mark the period before the charge by date, not by a missing value: the column does not exist in the 2024 files, but 1 to 4 January 2025 has it, mostly as 0. We compare daily averages because the two quarters have 91 and 90 days.

## Queries for Report 2
| Query | Objective | Owner | Main operations |
|---|---|---|---|
| Q1 | O1 | Alican | derive pickup date, hour and weekday, group and count, sort; daily trend and daily average per year |
| Q2 | O2 | Alican | leave out `has_negative_part`, derived columns (duration, speed, price per mile, tip %), group by hour and payment type with flex fare as its own group, averages and percentiles |
| Q3 | O3 | Berke | join with the zone table for pickup and drop-off, group by borough and zone pair, top-N, airport trips |
| Q4 | O4 | Berke | filter trips with `cbd_congestion_fee > 0`, join with zones, share by zone and hour, compare total price with other trips; compare 2024 and 2025 by daily averages |

Measures used in Q2:
- Duration: the time between pickup and drop-off, with both times read as New York local time and converted to UTC first, so that trips across the summer time change are not one hour too long.
- Speed: `trip_distance` divided by the duration in hours. Price per mile: `total_amount` divided by `trip_distance`. Divisions use `try_divide`, because Spark 4 stops with an error on a division by zero.
- Price: `total_amount`, not the single parts. The parts do not add up to the total in the same way for every vendor (`extra` in particular), so comparing parts between vendors would mislead.
- Tip percentage: `tip_amount` divided by `total_amount` minus `tip_amount`, only for credit card payments (`payment_type` 1), because cash tips are not recorded.

Each query is written with the DataFrame API and, where it reads better, also as Spark SQL.

## Optimizations to test
| Optimization | Owner | Before | After | Where it should help |
|---|---|---|---|---|
| Caching / persistence | Alican | Q1–Q2 read and clean the raw files each time | clean once, `cache()` the result, reuse it | repeated queries on the same cleaned table |
| Broadcast join | Berke | shuffle join (automatic broadcast turned off) | `broadcast()` on the zone table | Q3 and Q4 |
| Partitioning / columnar storage | Berke | cleaned data written as plain Parquet, read with the same filters | cleaned data written as Parquet partitioned by pickup date, read with filters | queries that filter on dates or a few columns |

Before/after runs use the same data, the same Spark settings and the same computer, measured with `src/hlds/timing.py`:
- one warm-up run and five measured runs; we report the median and keep the minimum and maximum;
- caching is measured on Q1 and Q2 run one after the other, including the time to fill the cache, because a single query cannot gain from it;
- for each optimization we save the `explain()` plan, so we can show why the time changed, for example that the run before the broadcast join really used a shuffle join;
- each optimization is measured on its owner's computer, and the times go to `results/timings_<machine>.csv`. Times from the two computers are never compared with each other.

## Cleaning rules (Report 1)
Checked on all six months; the count for each rule is in the "Cleaned table" part of `data-dictionary.md`:
- keep trips whose pickup time is between 1 January and 31 March, in 2024 and 2025 (each file has 15 to 33 rows outside its own month);
- drop trips with drop-off at or before pickup, duration over 5 hours, distance of 0 or below, distance over 100 miles, a negative `total_amount`, or a `total_amount` over 2,000 dollars;
- keep trips with a negative amount but a `total_amount` that is not negative, and mark them with `has_negative_part`. Almost all of them are flex fare trips with a negative `fare_amount`. They stay in the demand counts (Q1, Q3) and are left out of the price queries (Q2, Q4);
- never read a missing `cbd_congestion_fee` in the 2024 rows as 0;
- keep the flex fare trips (`payment_type` 0), where `passenger_count`, `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` and `Airport_fee` are all missing, and mark them with `details_missing`;
- treat 0 passengers and the rate code 99 (unknown) as missing values;
- drop exact duplicate rows.

## Charts for Report 3
Q1 and Q2 save their grouped results as small files in `results/` during Report 2, so the charts for O1 and O2 can be drawn without running Spark again.
- Heat map: trips by hour of day and day of week (O1).
- Line chart: trips per day, January to March (O1).
- Line or box chart: tip percentage and speed by hour (O2).
- Bar chart: top pickup zones and busiest routes; borough flow table (O3).
- Bar chart: share of trips paying the zone charge by hour and zone (O4).
- Bar chart: execution time before and after each optimization.

## Optional extension
Spark MLlib, decided in W6: predict tip percentage for card payments (regression), or group zones by their hourly demand profile (clustering).

## Decisions
- We add January to March 2024 instead of December 2024 (30 October 2026). December has Christmas and New Year, which would mix with the effect of the charge, while the same season one year earlier gives a fairer comparison. The larger data should also make the effect of the optimizations easier to see.
- We drop only negative totals, not every row with a negative amount (5 November 2026). `cbd_congestion_fee` is negative in 90,956 rows of 2025, and `total_amount` is negative in all of them, so these are reversals and they are dropped. But 20,862 rows in 2024 and 315,192 in 2025 have a negative part and a total that is not negative. Our first draft of the rules dropped those too and removed 7.03% of 2025 against 3.64% of 2024, which would lower the 2025 demand only because of the data. The rules we use now, which also drop trips of 0 seconds, remove 4.46% and 3.43%.
- We drop a `total_amount` over 2,000 dollars (6 November 2026). The raw data has 13 rows above it, and 11 of them are dropped by the other rules too. The two left are from 2025, 863,380.37 and 132,555.41 dollars for trips under 3 miles, and the next largest amount is 1,021.99. Together they raised the 2025 mean by about 0.10 dollars, which is a large part of the difference between the years.
- We compute trip durations from New York local time (6 November 2026). The times in the files are New York clock times without a time zone. On 10 March 2024 and 9 March 2025 the clocks in New York jumped from 02:00 to 03:00, and no row has a time in that hour. The plain clock difference makes the 2,360 trips that cross it exactly one hour longer (median 75 minutes instead of 15). Reading the times as New York time and converting them to UTC corrects all of them and changes no other row, so we keep these trips instead of dropping them. The numbers come from `scripts/check_summer_time.py`.
- We fixed how the optimizations are measured before writing any of them (7 November 2026): five runs after a warm-up, the `explain()` plan for each case, caching measured on Q1 and Q2 together, and plain Parquet as the run before partitioning. We keep all three optimizations, but if two of them do not have a working before/after run by 29 November, the third becomes optional.

## Limitations
- When a negative total is dropped, the trip it reverses stays in the data. We call a kept trip reversed when a dropped row has the same `VendorID`, pickup and drop-off time, `PULocationID` and `DOLocationID`, and the opposite `total_amount`. This matches 90,868 kept trips in 2024 (0.98% of the rows, 0.93% of `total_amount`) and 148,495 in 2025 (1.39% and 1.47%).

## Open questions
- Which tool do we use for the dashboard in Report 3?
