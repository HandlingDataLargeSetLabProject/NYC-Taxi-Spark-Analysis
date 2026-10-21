# Analysis plan (draft)

Draft for task R1-03 and R1-08. Both of us agree on it before Report 1; after that it stays the same for all three reports.

## Analytical problem
**How do demand, prices and tipping of NYC yellow taxi trips change by time and place in the first quarter of 2025, and how much of this traffic is affected by the new Manhattan congestion relief zone charge?**

Why this problem:
- The data covers time (pickup and drop-off timestamps), place (pickup and drop-off zones) and money (fare, tip, surcharges), so filtering, grouping, aggregation and a join all come up naturally.
- The zone lookup table is small (265 zones) while the trip table has millions of rows, which is the typical case for a broadcast join.
- The congestion relief zone charge (`cbd_congestion_fee`) started on 5 January 2025, so this quarter is the first one with it in the data.

## Objectives
1. **O1, demand over time:** when do people take taxis (hour of day, day of week) and how does daily demand move from January to March?
2. **O2, prices and tips:** how fare per mile, trip speed and tip percentage change by hour and by payment type.
3. **O3, places:** which zones and boroughs have the most pickups and drop-offs, and which zone-to-zone or airport routes are the busiest.
4. **O4, congestion relief zone:** what share of trips pays the zone charge, where and when these trips happen, and how their total price compares with trips that do not pay it.

## Queries for Report 2
| Query | Objective | Owner | Main operations |
|---|---|---|---|
| Q1 | O1 | Alican | filter valid trips, derive hour and weekday, group and count, sort; daily trend |
| Q2 | O2 | Alican | derived columns (duration, speed, fare per mile, tip %), group by hour and payment type, averages and percentiles |
| Q3 | O3 | Berke | join with the zone table for pickup and drop-off, group by borough and zone pair, top-N, airport trips |
| Q4 | O4 | Berke | filter trips with `cbd_congestion_fee > 0`, join with zones, share by zone and hour, compare total price with other trips |

Each query is written with the DataFrame API and, where it reads better, also as Spark SQL.

## Optimizations to test
| Optimization | Owner | Before | After | Where it should help |
|---|---|---|---|---|
| Caching / persistence | Alican | Q1–Q2 read and clean the raw files each time | clean once, `cache()` the result, reuse it | repeated queries on the same cleaned table |
| Broadcast join | Berke | shuffle join (automatic broadcast turned off) | `broadcast()` on the zone table | Q3 and Q4 |
| Partitioning / columnar storage | Berke | one large DataFrame, default partitions | cleaned data written as Parquet partitioned by pickup date, read with filters | queries that filter on dates or a few columns |

Before/after runs use the same data, the same Spark settings and the same computer, measured with `src/hlds/timing.py`.

## Cleaning rules (Report 1)
To be confirmed after the first look at the data:
- keep trips whose pickup time is between 1 January and 31 March 2025;
- drop trips with drop-off before pickup, duration over 5 hours, distance of 0 or below, or negative amounts;
- keep `passenger_count` missing values but count them, since they are reported by the driver;
- drop exact duplicate rows.

## Charts for Report 3 (first ideas)
- Heat map: trips by hour of day and day of week (O1).
- Line chart: trips per day, January to March (O1).
- Line or box chart: tip percentage and speed by hour (O2).
- Bar chart: top pickup zones and busiest routes; borough flow table (O3).
- Bar chart: share of trips paying the zone charge by hour and zone (O4).
- Bar chart: execution time before and after each optimization.

## Optional extension
Spark MLlib, decided in W8: predict tip percentage for card payments (regression), or group zones by their hourly demand profile (clustering).

## Open questions
- Is one quarter enough, or do we also add December 2024 so that O4 can compare trips before and after the zone charge started?
- Which tool do we use for the dashboard in Report 3?
