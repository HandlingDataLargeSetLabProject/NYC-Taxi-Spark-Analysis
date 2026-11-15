# Report 2: sections by Alican

These sections go into the final Report 2 document. The numbers come from the files in `results/`, written by the scripts named under each table and run on all six months of the cleaned table. Where a table says "our grouping", we added up rows of such a file with a short script and did not run Spark again.

## 1. Introduction

*Written by Alican Kaya*

In Report 1 we loaded and cleaned the NYC yellow taxi trips of January to March 2024 and January to March 2025: 20,752,804 raw trips, of which 19,926,016 (96.0%) stay in the cleaned table. Our question is how demand, prices and tipping change by time and place in the first quarter of 2025 compared with the same quarter of 2024, and how much of the traffic is affected by the new congestion relief zone charge, which started on 5 January 2025.

Report 2 answers the four objectives of Report 1 with four queries and tries three optimizations on them:

- **Queries.** Q1 (demand over time) and Q2 (prices, speed and tips) are Alican's, Q3 (places and routes) and Q4 (the zone charge) are Berke's. Each query answers the objective with the same number: Q1 answers objective O1, and so on.
- **Optimizations.** O1 caches the cleaned table for Q1 and Q2, O2 broadcasts the zone table in the joins of Q3, and O3 stores the cleaned table partitioned by pickup date. The optimizations are also numbered O1 to O3, so where the two could be confused we write "objective O1" or "optimization O1".

Every query writes its grouped result as a small CSV file to `results/`. These files are the input for the charts of Report 3, so Spark does not have to run again during the holidays. Section 2 explains how we measured the optimizations, Sections 3 to 6 present the queries, Sections 7 to 9 the optimizations, and Sections 10 and 11 put the results together.

## 2. Environment and measuring method

*Written by Alican Kaya*

### 2.1 Machines and Spark settings

We still run Spark in local mode on our own laptops, as described in Report 1. Every script creates its session through `get_spark` in `src/hlds/session.py`, so the settings are the same everywhere: `local[*]`, 6 GB driver memory, session time zone UTC, and all other settings at their defaults. Adaptive query execution is on by default in our Spark version.

Table 2.1. The two laptops

| Item | Alican | Berke |
|---|---|---|
| CPU | Intel Core i7-14650HX, 16 cores, 24 threads | Intel Core i7-13650HX, 14 cores, 20 threads |
| RAM | 32 GB | 16 GB |
| OS | Windows 11 Pro | Windows 11 Pro |
| Spark | 4.2.0, `local[*]`, driver memory 6g | 4.2.0, `local[*]`, driver memory 6g |
| Java | Microsoft OpenJDK 21.0.12.1 | Temurin 17.0.20.1 |

Source: `docs/environment.md`.

### 2.2 How we measure

We fixed the method before writing any optimization, so that we could not choose it after seeing the results. All cases run through `scripts/run_benchmarks.py`, which uses `measure` from `src/hlds/timing.py`:

- **One warm-up run and five measured runs.** The first run of a query pays for things that later runs do not, for example starting the Java code paths and listing the files, so it is not counted. We report the median of the five runs, because one slow run moves the median much less than the mean, and we keep the minimum and maximum to show the spread.
- **The same start for every run.** Before each run we clear Spark's cache (`spark.catalog.clearCache()`). This step is not timed. Without it, a run could read data that an earlier run left in memory.
- **The plan after the runs.** Each case returns the DataFrame its action ran on, and we save its `explain()` plan after the measured runs. With adaptive query execution, a plan printed before the query has run is only the starting plan (`isFinalPlan=false`), and Spark can still change it, for example the join type. All our saved plans are final plans (`isFinalPlan=true`). Section 12.1 explains how we got this wrong at first.
- **One CSV per laptop.** The times go to `results/timings_alican.csv` or `results/timings_berke.csv`, together with the CPU, the number of threads, the RAM, the Spark version and the driver memory.
- **Nothing else running.** During a measurement no other program uses Spark or much CPU on the laptop (Section 12.2).

Each optimization is measured before and after on its owner's laptop, with the same data and the same settings. We never compare times between the two laptops, because they have different CPUs and memory.

As a reference point we first measured the shortest useful job: read the six files, clean them and count the rows. On Alican's laptop it took a median of 30.49 seconds (three runs, 26.01 to 46.25 seconds).

### 2.3 Approximate medians

We compute medians with `percentile_approx`, because an exact median of 20 million rows needs much more memory and time. The result can depend slightly on how the rows are split into tasks. When Alican ran Berke's Q4 script to check it, 19 of about 2,150 rows had a median that differed from Berke's file by at most 0.06 dollars, because the two laptops split the work into 24 and 20 tasks. All counts and shares were exactly the same.

## 3. Q1 Demand over time

*Written by Alican Kaya*

Q1 answers objective O1: when people take taxis, by hour of day and day of week, and how daily demand moves from January to March. All rows of the cleaned table count, including those marked `has_negative_part`, because they are real trips. We compare the years by trips per day, because the first quarter has 91 days in 2024 (a leap year) and 90 in 2025.

The code is in `src/hlds/demand.py`. `add_pickup_parts` adds the year, date, hour and weekday of the pickup. The pickup times in the files are New York clock times, so the hour and the date can be read directly. The daily counts and the average per year use the DataFrame API. The hour by weekday table is in Spark SQL: it counts the trips in each hour of each weekday and divides them by the number of days of that weekday in the quarter. We count the days from the dates, not from the trips of that hour, so an hour without any trip on one Monday would still count that Monday. In 2025 the quarter has only twelve Tuesdays, and the query divides by twelve for them.

### 3.1 From January to March

Table 3.1. Trips per day by month

| Month | 2024 days | 2024 per day | 2025 days | 2025 per day | Change |
|---|---|---|---|---|---|
| January | 31 | 92,586.8 | 31 | 107,197.2 | +15.8% |
| February | 29 | 100,158.8 | 28 | 122,168.8 | +22.0% |
| March | 31 | 111,377.4 | 31 | 127,570.4 | +14.5% |
| whole quarter | 91 | 101,401.1 | 90 | 118,872.4 | +17.2% |

Source: `results/q1_daily_average.csv` for the quarter and `results/q1_daily_trips.csv` for the months (our grouping), written by `scripts/query_demand.py`.

The first quarter of 2025 has 17.2% more trips per day than the same quarter of 2024. In both years demand grows from month to month, and March has about a fifth more trips per day than January. The quietest days are in early January, after the holidays: the quietest day of 2024 is Sunday 7 January (65,200 trips) and of 2025 Sunday 5 January (76,531), which is also the first day of the zone charge. The busiest days are Saturdays in March: 9 March 2024 (131,502) and 1 March 2025 (159,698). Single days can also drop for reasons the data does not show. Tuesday 13 February 2024 had only 67,175 trips, the second lowest of that year, and we did not check why, for example the weather.

### 3.2 Days of the week

Table 3.2. Trips per day by day of the week

| Day | 2024 days | 2024 per day | 2025 days | 2025 per day | Change |
|---|---|---|---|---|---|
| Monday | 13 | 84,167.4 | 13 | 96,886.1 | +15.1% |
| Tuesday | 13 | 96,705.0 | 12 | 113,622.6 | +17.5% |
| Wednesday | 13 | 106,452.4 | 13 | 119,346.4 | +12.1% |
| Thursday | 13 | 114,963.8 | 13 | 129,028.6 | +12.2% |
| Friday | 13 | 106,800.8 | 13 | 124,716.2 | +16.8% |
| Saturday | 13 | 110,663.3 | 13 | 136,721.3 | +23.5% |
| Sunday | 13 | 90,054.7 | 13 | 111,382.1 | +23.7% |

Source: `results/q1_daily_trips.csv`, written by `scripts/query_demand.py`; our grouping by weekday.

In 2024 Thursday is the busiest day and in 2025 Saturday. The weekend grew most (+23.5% and +23.7%), while the middle of the week grew least (about +12%). Monday and Sunday stay the quietest days in both years.

### 3.3 Hours of the day

Table 3.3. Trips per day by pickup hour, all days together

| Hour | 2024 | 2025 | Change |
|---|---|---|---|
| 0 | 2,814.3 | 3,611.9 | +28.3% |
| 4 | 583.1 | 802.4 | +37.6% |
| 8 | 3,944.1 | 4,772.6 | +21.0% |
| 12 | 5,431.5 | 5,849.3 | +7.7% |
| 15 | 6,190.0 | 6,963.3 | +12.5% |
| 18 | 7,347.2 | 8,453.1 | +15.1% |
| 21 | 5,856.0 | 7,517.7 | +28.4% |
| 23 | 4,046.2 | 5,186.1 | +28.2% |

Source: `results/q1_hour_weekday.csv`, written by `scripts/query_demand.py`, which has all 24 hours for every weekday; here the seven weekdays are added up and divided by the days of the year (our grouping).

The daily shape is the same in both years: the fewest trips at 4:00 and the most at 18:00. But the growth is not spread evenly over the day. Around noon there are only about 8% more trips than in 2024, while in the late evening and at night (20:00 to 1:00) there are 25% to 30% more. The early morning grew even more in percentage terms, but from a small base.

Table 3.4. Trips per day in selected hours, working days against weekends

| Hour | 2024 Mon–Fri | 2024 Sat–Sun | 2025 Mon–Fri | 2025 Sat–Sun |
|---|---|---|---|---|
| 1 | 845.7 | 4,472.5 | 955.8 | 5,912.5 |
| 8 | 4,771.4 | 1,875.8 | 5,830.0 | 2,188.2 |
| 12 | 5,373.6 | 5,576.2 | 5,728.4 | 6,147.0 |
| 18 | 7,751.2 | 6,336.9 | 8,557.1 | 8,193.4 |
| 23 | 3,804.6 | 4,650.0 | 4,713.9 | 6,286.8 |

Source: `results/q1_hour_weekday.csv`; each value is the mean of the trips per day of the five working days or the two weekend days in that hour (our grouping).

Working days and weekends have different shapes, so we think the hour by weekday table is worth a heat map in Report 3. On working days there is a morning peak at 8:00 and the highest peak at 18:00, which fits trips to and from work. At the weekend there are few trips in the morning, and at 1:00 there are five to six times as many trips as on a working day; Sunday's busiest hour is midnight, which is still Saturday night. The busiest single hour of the week moved from Thursday at 18:00 in 2024 (8,991.5 trips per day) to Saturday at 19:00 in 2025 (9,925.0).

Taken together, Q1 shows that the 2025 growth comes mostly from evenings, nights and weekends, and much less from working hours. Section 4.3 shows that most of these extra trips are flex fare trips, and Section 11 comes back to this.

### 3.4 Outputs for Report 3

`scripts/query_demand.py` writes three files: `q1_daily_trips.csv` (181 days, for the line chart from January to March), `q1_daily_average.csv` (one row per year) and `q1_hour_weekday.csv` (2 × 7 × 24 = 336 rows, for the heat map).

## 4. Q2 Prices, speed and tips

*Written by Alican Kaya*

Q2 answers objective O2: how duration, speed, price per mile and tip percentage change by hour and by payment type. The code is in `src/hlds/prices.py`. Unlike Q1, Q2 leaves out the rows with `has_negative_part`, because their amounts do not show what the trip cost, so 9,206,634 trips remain in 2024 and 10,383,328 in 2025. The measures were fixed in Report 1:

- **Duration.** Both times are read as New York time and converted to UTC first, so the 2,360 trips across the summer time change are not one hour too long.
- **Speed** is `trip_distance` divided by the duration in hours, and **price per mile** is `total_amount` divided by `trip_distance`. Both use `try_divide`, which gives a missing value instead of stopping the query when it would divide by zero.
- **Tip percentage** is `tip_amount` divided by (`total_amount` minus `tip_amount`), only for credit card payments, because cash tips are not recorded.

We group by year and payment type and by year, hour and payment type. Flex fare trips (`payment_type` 0) are their own group, credit card (1) and cash (2) are the other two large groups, and the remaining codes, such as no charge and dispute, are grouped together as "other". For each group we compute the mean and the median of every measure.

### 4.1 Payment types

Table 4.1. Trips and medians by payment type (means of price per mile and tip in brackets)

| Year | Payment | Trips per day | Share | Duration (min) | Speed (mph) | Price per mile ($) | Tip (%) |
|---|---|---|---|---|---|---|---|
| 2024 | credit card | 79,036.5 | 78.12% | 12.02 | 9.58 | 11.88 (16.20) | 20.0 (17.79) |
| 2024 | cash | 14,021.4 | 13.86% | 11.53 | 9.21 | 10.50 (21.28) | |
| 2024 | flex fare | 6,916.7 | 6.84% | 14.63 | 10.32 | 8.87 (12.60) | |
| 2024 | other | 1,197.2 | 1.18% | 10.00 | 9.31 | 11.25 (76.84) | |
| 2025 | credit card | 82,203.3 | 71.25% | 11.72 | 9.49 | 12.37 (17.08) | 20.0 (17.53) |
| 2025 | cash | 11,818.6 | 10.24% | 11.18 | 9.14 | 10.93 (22.78) | |
| 2025 | flex fare | 19,637.1 | 17.02% | 14.13 | 10.46 | 8.78 (48.26) | |
| 2025 | other | 1,711.4 | 1.48% | 10.83 | 9.31 | 11.33 (62.91) | |

Source: `results/q2_by_payment.csv`, written by `scripts/query_prices.py`; trips per day and shares are ours (trips divided by 91 and 90 days).

The largest change in this table is not a price. Trips per day in Q2 grew by 14.0%, but almost all of this growth comes from flex fare: flex fare trips almost tripled (+183.9%), credit card trips grew by only 4.0%, and cash trips fell by 15.7%. Of the extra trips per day, 89.6% are flex fare trips. The data only tells us that these trips have `payment_type` 0; it does not tell us how they were booked or paid.

The typical trip changed little. The median duration is about 11 to 12 minutes for card and cash and about 14 minutes for flex fare, and the median speed stays between 9 and 10.5 miles per hour in all groups, which shows how slow city traffic is. Card trips cost 4.1% more per mile than in 2024 (12.37 against 11.88 dollars), cash trips 4.1% more, and flex fare trips are the cheapest per mile in both years.

For card payments the median tip is exactly 20% in both years, while the mean fell slightly from 17.79% to 17.53%. A median of exactly 20.0, both overall and in almost every hour (Section 4.2), means that many card payments tip exactly 20%. We think these payments use one of the fixed tip choices on the payment screen in the taxi, but the data cannot show it, so we treat it as an assumption.

The means in brackets show why we compare medians. For flex fare in 2025 the mean price per mile is 48.26 dollars, but the median is 8.78. When the distance is close to 0, the price per mile becomes very large, and a small number of such trips pulls the mean far up (Section 12.4).

### 4.2 Hours of the day

Table 4.2. Credit card trips by pickup hour: medians of speed and price per mile, mean tip

| Hour | Speed 2024 | Speed 2025 | Price per mile 2024 | Price per mile 2025 | Mean tip 2024 | Mean tip 2025 |
|---|---|---|---|---|---|---|
| 0 | 12.03 | 11.98 | 10.17 | 10.57 | 17.43% | 17.05% |
| 5 | 16.59 | 16.05 | 8.22 | 8.58 | 15.75% | 15.60% |
| 8 | 9.33 | 9.19 | 11.69 | 12.23 | 17.43% | 17.16% |
| 12 | 8.52 | 8.51 | 12.43 | 12.89 | 18.03% | 17.83% |
| 15 | 8.38 | 8.44 | 12.24 | 12.59 | 18.00% | 17.74% |
| 17 | 8.53 | 8.62 | 13.44 | 13.86 | 17.76% | 17.55% |
| 22 | 11.17 | 10.90 | 10.57 | 11.09 | 17.96% | 17.69% |

Source: `results/q2_by_hour_payment.csv`, written by `scripts/query_prices.py`, which has all 24 hours for all four payment groups. Speeds in miles per hour, prices in dollars.

We show credit card trips here because they are the largest group and the only one with tips. Speed and price per mile move against each other. Early in the morning taxis are fastest (about 16 miles per hour at 5:00) and cheapest per mile, and in the afternoon they are slowest (about 8.4 miles per hour at 15:00). The price per mile is highest at 17:00, when traffic is still slow. This fits a meter that also charges for time in slow traffic, but we did not split the price into its parts, because the parts do not add up to the total in the same way for every vendor (Report 1). The median tip is 20% in every hour except 5:00 and 6:00, where it is just below. The mean tip is lowest at 5:00 and highest in the afternoon and the evening.

The two years have almost the same shape. In 2025 the price per mile is higher and the mean tip slightly lower in each of the hours of Table 4.2.

### 4.3 Where the growth of Q1 comes from

Table 4.3. Trips per day in Q2 by pickup hour, and the flex fare part

| Hour | All 2024 | All 2025 | Change | Flex fare 2024 | Flex fare 2025 | Card change |
|---|---|---|---|---|---|---|
| 2 | 1,228.7 | 1,474.2 | +20.0% | 133.2 | 449.3 | -5.0% |
| 8 | 3,934.4 | 4,584.5 | +16.5% | 339.0 | 1,045.9 | +0.1% |
| 12 | 5,425.6 | 5,751.8 | +6.0% | 205.3 | 511.4 | +3.2% |
| 17 | 6,949.3 | 7,722.5 | +11.1% | 388.7 | 852.3 | +7.4% |
| 22 | 5,273.4 | 6,528.2 | +23.8% | 519.6 | 1,729.6 | +2.8% |

Source: `results/q2_by_hour_payment.csv`; our grouping (trips divided by 91 and 90 days).

This table links Q1 and Q2. The hours that grew most in Q1, the late evening and the night, are the hours where flex fare grew most. Between 23:00 and 3:00 the card trips even fell slightly, so all of the growth in these hours, and more, comes from flex fare. From 20:00 to 22:00 card trips grew by 3% to 8%, but flex fare still makes up 78% to 96% of the growth. In the afternoon card trips also grew by about 7%, and there flex fare makes up between a half and two thirds of the growth. The share of flex fare among the Q2 trips of one hour ranges from 3.3% (10:00) to 22.3% (4:00) in 2024, and from 7.7% (16:00) to 41.0% (4:00) in 2025.

Because the mix of payment types changed so much, an average over all trips would change even if no single group changed. This is why we keep the groups apart and why Report 3 should show flex fare as its own line.

### 4.4 Outputs for Report 3

`scripts/query_prices.py` writes `q2_by_payment.csv` (8 rows) and `q2_by_hour_payment.csv` (2 years × 24 hours × 4 payment groups = 192 rows). Both have the means and the medians, so the charts can show either.

## 7. O1 Caching

*Written by Alican Kaya*

### 7.1 What we changed

Q1 and Q2 produce five results: the daily trips, the daily average per year and the hour by weekday table of Q1, and the two summaries of Q2. Spark is lazy and keeps nothing between actions by default, so each of the five results reads the six Parquet files and cleans them again, including the removal of duplicate rows, which needs a shuffle of all rows. All five use the same cleaned table, so this is the case where caching should help.

`run_q1_and_q2` in `src/hlds/caching.py` builds the five results from one cleaned table and collects them one after the other. The two cases differ only in one call:

```python
def q1_q2_without_cache(spark):
    return run_q1_and_q2(clean_trips(load_trips(spark)))


def q1_q2_with_cache(spark):
    # The time to fill the cache is part of the run, because a real run pays for it too.
    return run_q1_and_q2(clean_trips(load_trips(spark)).cache())
```

With `cache()`, the first result fills the cache and the other four read the cleaned rows from memory. The time to fill the cache is part of the measured run. Before every run the cache is cleared (Section 2.2), so each run starts empty and fills it again.

### 7.2 Results

Table 7.1. O1 before and after on Alican's laptop

| Case | Median (s) | Min (s) | Max (s) | The five runs in order (s) |
|---|---|---|---|---|
| before, no cache | 281.52 | 230.15 | 349.92 | 230.1, 281.5, 281.4, 337.6, 349.9 |
| after, `cache()` | 187.67 | 175.61 | 191.66 | 175.6, 184.4, 191.7, 188.9, 187.7 |

Source: `results/timings_alican.csv`, written by `scripts/run_benchmarks.py --machine alican --case O1`; one warm-up and five measured runs each, nothing else running on the laptop (Table 2.1).

With the cache, Q1 and Q2 together take 93.9 seconds (33.3%) less time (median against median). Even the fastest run without cache (230.1 s) is slower than the slowest run with cache (191.7 s), so the cache clearly helps.

The size of the saving is less certain. The runs without cache became slower from run to run, from 230 to 350 seconds, while the runs with cache stayed within 16 seconds of each other. Berke's measurements of O2 and O3 do not show this. We do not know the cause; memory filling up over the runs, temporary shuffle files or the laptop getting warm are possible, but we did not check them. If we compare the median with cache against the fastest and the slowest run without it, the saving is between 18% and 46%, so we only claim that it is large, about a third.

### 7.3 Why the time changed

The saved plans (`results/plans/alican/O1_before.txt` and `O1_after.txt`) are the final plans of the last of the five results, the Q2 summary by hour. Without the cache, the plan starts from the Parquet files and has the shuffle of the duplicate removal (3.5 GiB of rows). The plan is shortened here:

```text
ShuffleQueryStage (8), Statistics(sizeInBytes=3.5 GiB, rowCount=1.96E+7)
+- Exchange (7)
   +- * HashAggregate (6)
      +- * Project (5)
         +- * Project (4)
            +- * Filter (3)
               +- * ColumnarToRow (2)
                  +- Scan parquet  (1)
```

With the cache, the same result starts from the table in memory:

```text
TableCacheQueryStage (20), Statistics(sizeInBytes=2.4 GiB, rowCount=1.99E+7)
+- InMemoryTableScan (1)
      +- InMemoryRelation (2)
```

The plan with cache also shows the Parquet scan and the duplicate removal below `InMemoryRelation`, but this is the plan that filled the cache, and it runs only for the first result. The cached table has 19.9 million rows and about 2.4 GiB, and its storage level is memory and disk, so rows that did not fit in memory would be written to disk instead of being computed again.

A rough check with the reference job of Section 2.2: reading and cleaning the six files takes about 30 seconds. The cache saves this step for four of the five results, which would be about 120 seconds, while the measured saving is about 94 seconds. The rest is probably the cost of building the cache and of reading from it, but we did not measure these parts on their own.

### 7.4 Does it help in practice?

Yes, when the same cleaned table is used several times in one Spark session, as in Q1 and Q2. With one result there is nothing to reuse, and the cache only costs time and memory. It also needs memory: 2.4 GiB of the 6 GB driver memory is a large part, and with more data or less memory Spark would have to keep parts of it on disk. A cache also disappears when the session ends. For Report 3, where the dashboard reads results again on another day, storing the cleaned table as Parquet, as in O3, is the better choice; the cache is for repeated work inside one session.

## 10. Before and after the optimizations

*Written by Alican Kaya*

Table 10.1. The three optimizations, each measured before and after on its owner's laptop

| Optimization | Laptop | Before, median (s) | After, median (s) | Saved (s) | Change | Spread before / after (s) |
|---|---|---|---|---|---|---|
| O1 caching (Q1 and Q2) | Alican | 281.52 | 187.67 | 93.85 | -33.3% | 119.78 / 16.05 |
| O2 broadcast join (zone joins) | Berke | 24.45 | 18.67 | 5.78 | -23.6% | 0.43 / 0.48 |
| O3 partitioned storage (March 2025) | Berke | 1.98 | 1.15 | 0.83 | -42.0% | 0.63 / 0.10 |

Source: `results/timings_alican.csv` and `results/timings_berke.csv`, written by `scripts/run_benchmarks.py`; one warm-up and five measured runs per case. The spread is the slowest minus the fastest of the five runs. The changes are ours, computed from the medians.

All three optimizations made their query faster, and in all three the difference between before and after is larger than the spread of the runs. O1 is the only case with a large spread, and Section 7.2 explains why we still trust its direction but give its size as a range.

The rows of the table should not be compared with each other. Each optimization was measured on a different query, and O1 on a different laptop than O2 and O3. What we can compare is what each optimization removes from its query:

- **O1** removes the reading and cleaning of the six files for four of the five results. This is the largest saving in seconds, because reading and cleaning is the most expensive step we have (about 30 seconds each time on both laptops).
- **O2** removes the shuffle and the sort of 20 million rows for each of the two zone joins. The reading, cleaning and duplicate removal stay, so we save about a quarter of the time and no more.
- **O3** lets Spark skip five sixths of the stored files. In percentage terms this is the largest saving, but the query is so short that we save less than a second, and much of what is left is fixed work for every query.

We learned two things from putting them together. First, the most expensive step in our project is reading and cleaning the raw files again and again, not a join or a grouping. O1 avoids it inside one session and O3 avoids it for good by reading a cleaned copy, so for Report 3 we will clean once, store the result as Parquet and read only that. Second, local mode hides some costs. A shuffle on one laptop moves data through the local disk, not through a network, so on a real cluster O2 would probably save more. We did not measure combinations either, for example caching a partitioned copy.

## 11. What the queries show together

*Written by Alican Kaya*

Each query answered its own objective. Here we put their results side by side to answer the question of the project: what changed between the first quarters of 2024 and 2025, and how the zone charge fits into it. To link Q2 with the places of Q3 and Q4, we added one more grouping, `pickup_borough_by_payment` in `src/hlds/prices.py`: it joins the zone table and counts the trips by year, pickup borough and payment group. Like Q1 and Q3 it counts all rows of the cleaned table.

### 11.1 More trips, and most of the new ones are flex fare

There are 17.2% more taxi trips per day in 2025 (Q1). Section 4.3 showed that most of the extra trips are flex fare trips, and Table 11.1 shows that this is true in every borough.

Table 11.1. Pickups per day by borough, with the flex fare part

| Pickup borough | All 2024 | All 2025 | Change | Flex fare share 2024 | Flex fare share 2025 | Flex fare part of the growth | Credit card change |
|---|---|---|---|---|---|---|---|
| Manhattan | 91,176.6 | 104,801.6 | +14.9% | 7.2% | 17.8% | 88.9% | +4.3% |
| Queens | 8,683.4 | 9,916.9 | +14.2% | 2.3% | 16.2% | 114.3% | -0.5% |
| Brooklyn | 959.2 | 3,152.6 | +228.7% | 33.2% | 73.9% | 91.8% | +31.8% |
| Bronx | 232.6 | 729.2 | +213.5% | 26.6% | 71.4% | 92.4% | +22.8% |
| outside Manhattan | 9,879.2 | 13,811.1 | +39.8% | 5.8% | 32.3% | 98.9% | +2.4% |
| all trips | 101,401.2 | 118,872.5 | +17.2% | 7.0% | 19.5% | 91.5% | +4.0% |

Source: `results/q2_borough_payment.csv`, written by `scripts/query_borough_payment.py`; the shares, changes and the "outside Manhattan" row (Queens, Brooklyn, Bronx, Staten Island and Newark Airport) are our grouping. The pickups in zones 264 and 265 count only in "all trips".

Of all extra trips per day, 91.5% are flex fare trips. Their share of all trips grew from 7.0% to 19.5%, the same numbers as in Report 1. Credit card trips grew by only 4%. Outside Manhattan the change is even clearer: almost all of the growth (98.9%) comes from flex fare, and in Brooklyn and the Bronx about three out of four pickups are now flex fare trips. The data only tells us that these trips have `payment_type` 0. It does not tell us how they were booked, so we describe the change and do not explain it.

### 11.2 When and where the growth happens

The queries agree on where the new trips are:

- **Time (Q1, Q2).** The growth is largest in the late evening, at night and at weekends, and these are the hours where flex fare grew most (Section 4.3). Around noon on working days, when most trips are paid by card, demand grew by less than 10%.
- **Places outside Manhattan (Q3, Q4, Table 11.1).** Trips inside Brooklyn almost quadrupled and trips inside Queens grew by 49% (Table 5.2). The 117 zones where almost no trip pays the zone charge, 116 of them outside Manhattan, have three times as many pickups (Table 6.3). Table 11.1 shows that the pickups outside Manhattan grew almost only through flex fare, so these findings describe the same change.
- **Places in Manhattan (Q3).** Several busy zones of lower Manhattan grew by 21% to 30% (Section 5.1), more than Manhattan as a whole. We grouped payment types by borough and not by zone, so we cannot say how much of this is flex fare.
- **Airports (Q3).** Trips from and to JFK, LaGuardia and Newark stayed flat or fell slightly, while the city grew by 17%.

### 11.3 Prices and the zone charge

Three out of four trips in 2025 pay the zone charge (Q4). The prices moved only a little: the median total price rose by 45 cents (Table 6.1), and card trips cost 0.49 dollars or 4.1% more per mile (Table 4.1). For a rough idea of the size, a charge of 0.75 dollars on the median trip of 1.76 miles (Table 6.1) is about 0.43 dollars per mile. So the rise per mile is about the same size as the charge. This is only a rough comparison, because medians cannot be added or divided like this, and other parts of the price could have changed too. Tipping did not change in a way we can see: the median card tip is 20% in both years.

We see no sign that the charge lowered taxi demand. Pickups in the zones where at least 90% of the trips pay grew by 13.5%, about as much as all zones (+14.5%, Table 6.3). At the same time, the change in flex fare is much larger than any change we can link to the charge, and both happened between the same two winters. Because this is not an experiment, we cannot separate the effect of the charge from the growth of flex fare or from other changes such as prices, apps or travel habits.

### 11.4 What this means for Report 3

- Flex fare should be its own line or color in every chart that compares the years. A chart of all trips together would show growth without showing where it comes from.
- The heat map of hour by weekday (Q1) and a bar chart of pickups by borough and payment group (Table 11.1) together show when and where the new trips happen.
- The charts can read the CSV files in `results/` directly. If we need a new grouping, we will read the stored cleaned table instead of cleaning the raw files again (Section 10).

## 12. Problems and solutions

*Written by Alican Kaya*

### 12.1 A saved plan that was not the final plan

*Problem.* The first plan we saved in a trial run had `isFinalPlan=false`. We had measured `trips.count()` and then printed the plan of `trips`. But `count()` starts a new query with its own plan, so the plan of `trips` itself never ran, and with adaptive query execution an unfinished plan can still show a join that Spark later changes.

*Solution.* We wrote `count_rows`, which counts with `groupBy().count()`, collects the result and returns this counting DataFrame. Every case now returns the DataFrame its action ran on, and the plan is saved after the measured runs. A test with real Spark checks that the saved plan is final, and we checked that the old way gives `false`, so the test does not pass by accident.

### 12.2 A measurement disturbed by our own tests

*Problem.* Our first reference run took 46.43, 46.45 and 51.39 seconds. At the same time the test suite was running in the background, and it also uses Spark and the CPU.

*Solution.* We stopped the tests, removed these three rows from the timings file because we knew they were wrong, and measured again with nothing else running: a median of 30.49 seconds. Since then nothing else runs during a measurement (Section 2.2). Even then one of the three runs took 46.25 seconds, which is one reason why the real measurements use five runs after a warm-up.

### 12.3 A Spark job for every check in the tests

*Problem.* The tests of Q1 took 246 seconds for a few hand-made rows, because every check that reads a result starts a Spark job, and each job has a fixed start-up cost.

*Solution.* The tests now build the results once in `setUpClass` and check them in several tests, which brought them down to 151 seconds. We used the same setup for Q2. In the O1 tests Berke's idea of one cached partition did not help (Section 12.5), so these tests are still slow.

### 12.4 Means pulled up by very short trips

*Problem.* In the output of Q2 the mean price per mile of flex fare trips rose from 12.60 dollars in 2024 to 48.26 in 2025, which looked like a huge price change. The median, however, fell slightly, from 8.87 to 8.78. The mean of "other" payments (76.84 and 62.91) had the same problem. Trips with a distance close to 0 get a very large price per mile, and a few of them are enough to pull the mean up.

*Solution.* We compare medians in the text and in the tables, and we keep the means in the CSV files and in brackets in Table 4.1, so the difference stays visible. We did not add a new cleaning rule, because these trips passed the rules of Report 1 and their totals may be correct.
