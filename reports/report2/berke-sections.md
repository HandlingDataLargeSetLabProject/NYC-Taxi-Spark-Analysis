# Report 2: sections by Berke

These sections go into the final Report 2 document. The numbers come from the files in `results/`, written by the scripts named under each table and run on all six months of the cleaned table.

## 5. Q3 Places and routes

*Written by Berke Arda Türk*

Q3 answers objective O3: which zones and boroughs have the most pickups and drop-offs, and which routes and airport trips are the busiest. The trip table only has zone numbers (`PULocationID`, `DOLocationID`), so Q3 is where we need a join: `add_zone_names` in `src/hlds/places.py` joins the zone table twice, once for the pickup and once for the drop-off zone (Appendix A.1). We use a left join, so a trip would stay even if its zone were missing from the table; in our six months every zone number is in it. All rows of the cleaned table count here, including `has_negative_part`, because they are real trips. As in Q1, we compare the years by trips per day, because the first quarter has 91 days in 2024 and 90 in 2025.

Two zones need care. Zone 264 is called `Unknown` and zone 265 `Outside of NYC`; they are placeholders, not places. We leave them out of the zone and route rankings, but keep them in the borough flows, so their share stays visible: 0.92% of the trips in 2024 and 0.68% in 2025. We also group by zone number and not only by name, because three zone numbers share the name `Governor's Island/Ellis Island/Liberty Island`.

### 5.1 Pickup zones

Table 5.1. The ten zones with the most pickups in 2025

| Zone | Borough | 2024 per day | 2024 rank | 2025 per day | 2025 rank |
|---|---|---|---|---|---|
| Midtown Center | Manhattan | 4,863.2 | 1 | 5,492.5 | 1 |
| Upper East Side South | Manhattan | 4,728.9 | 2 | 5,300.9 | 2 |
| Upper East Side North | Manhattan | 4,481.5 | 4 | 4,922.9 | 3 |
| JFK Airport | Queens | 4,486.9 | 3 | 4,423.4 | 4 |
| Times Sq/Theatre District | Manhattan | 3,518.2 | 6 | 4,012.3 | 5 |
| Penn Station/Madison Sq West | Manhattan | 3,425.6 | 7 | 3,910.6 | 6 |
| Midtown East | Manhattan | 3,607.6 | 5 | 3,861.4 | 7 |
| Lincoln Square East | Manhattan | 3,388.9 | 8 | 3,577.7 | 8 |
| Union Sq | Manhattan | 2,759.7 | 13 | 3,347.7 | 9 |
| Murray Hill | Manhattan | 2,910.1 | 12 | 3,221.7 | 10 |

Source: `results/q3_pickup_zones.csv`, written by `scripts/query_places.py`.

The ranking hardly changes between the years. Nine of the ten zones are in Manhattan, and JFK is the only airport left in the top ten: LaGuardia (9th in 2024, 3,061.6 pickups a day) and Upper West Side South (10th) moved down. All trips together grew by about 17% per day, but not evenly. Among the zones with at least 1,000 pickups a day in 2024, the strongest growth is in lower Manhattan: Lower East Side +30%, Greenwich Village South +28%, West Chelsea/Hudson Yards +26%, East Village +25%, Union Sq +21% and TriBeCa/Civic Center +21%. Only three of these zones lost pickups: Central Park (-2.7%), JFK (-1.4%) and LaGuardia (-1.1%). The table cannot tell us why. Section 6 looks at whether the zone charge, which covers lower Manhattan, goes together with this.

### 5.2 Borough flows

Table 5.2. Trips between boroughs

| From | To | 2024 per day | 2024 share | 2025 per day | 2025 share |
|---|---|---|---|---|---|
| Manhattan | Manhattan | 85,784.3 | 84.6% | 99,380.9 | 83.6% |
| Queens | Manhattan | 5,123.7 | 5.05% | 5,267.9 | 4.43% |
| Manhattan | Queens | 2,673.7 | 2.64% | 2,545.7 | 2.14% |
| Queens | Queens | 1,794.2 | 1.77% | 2,675.6 | 2.25% |
| Manhattan | Brooklyn | 1,882.7 | 1.86% | 2,042.2 | 1.72% |
| Queens | Brooklyn | 1,306.4 | 1.29% | 1,509.3 | 1.27% |
| Brooklyn | Brooklyn | 487.2 | 0.48% | 1,887.3 | 1.59% |

Source: `results/q3_borough_flows.csv`, written by `scripts/query_places.py`. The shares are of all trips of the year; the flows of the table add up to the cleaned table (9,227,496 and 10,698,520 trips).

Yellow taxis are a Manhattan service: more than five of six trips start and end there in both years, and 89.9% (2024) and 88.2% (2025) of all pickups are in Manhattan. The flows between Manhattan and Queens are mostly airport trips. The largest relative change is inside Brooklyn, almost four times as many trips per day, and inside Queens (+49%). These are still small numbers next to Manhattan, but they show that the growth outside Manhattan is not only trips to and from it.

### 5.3 Routes and airports

Table 5.3. The five busiest routes (pickup zone to drop-off zone)

| Rank | Route | 2024 per day | 2025 per day |
|---|---|---|---|
| 1 | Upper East Side South to Upper East Side North | 698.9 | 781.0 |
| 2 | Upper East Side North to Upper East Side South | 619.6 | 677.9 |
| 3 | Upper East Side North to Upper East Side North | 494.9 | 533.9 |
| 4 | Upper East Side South to Upper East Side South | 458.5 | 513.6 |
| 5 | Midtown Center to Upper East Side South | 337.3 | 363.3 |

Source: `results/q3_top_routes.csv`, written by `scripts/query_places.py`, which keeps the 20 busiest routes of each year. The ranking is in Spark SQL with `ROW_NUMBER` per year (Appendix A.2).

The busiest routes are very short trips inside or between the two Upper East Side zones, and the first five are the same in both years. This fits the medians of Report 1: half of all trips are under about 1.8 miles.

Table 5.4. Trips from and to the three airports

| Airport | Direction | 2024 per day | 2025 per day |
|---|---|---|---|
| JFK Airport | from | 4,486.9 | 4,423.4 |
| JFK Airport | to | 961.9 | 918.7 |
| LaGuardia Airport | from | 3,061.6 | 3,026.9 |
| LaGuardia Airport | to | 1,111.0 | 1,100.1 |
| Newark Airport | from | 2.0 | 2.4 |
| Newark Airport | to | 239.7 | 219.8 |

Source: `results/q3_airport_trips.csv`, written by `scripts/query_places.py`. A trip from one airport to another counts in both directions.

Airport trips are the one group that did not grow: all six numbers are flat or slightly lower in 2025, while the city as a whole grew by 17%. Taxis pick up between four and five times as many passengers at JFK as they bring there, which fits the taxi lines at the terminals. Newark is in New Jersey, and yellow taxis almost never pick up there (about two trips a day).

## 6. Q4 Zone charge

*Written by Berke Arda Türk*

Q4 answers objective O4: what share of trips pays the congestion relief zone charge, where and when these trips happen, and how demand and prices compare with the same season before the charge. The charge, `cbd_congestion_fee`, is the per-trip charge for the MTA Congestion Relief Zone and started on 5 January 2025 [2]. The code is in `src/hlds/congestion.py` (Appendix A.3).

Three decisions shape this query:
- **The same calendar days in both years.** We compare 5 January to 31 March in both years: 87 days in 2024 and 86 in 2025. With the whole quarter, 1 to 4 January 2025 would count as charged although no charge applied yet. Q1 to Q3 keep the whole quarter, so the trips per day here differ slightly from theirs.
- **A missing charge is not a charge of 0.** The column does not exist in the 2024 files, so it is null there. We treat a missing value as "does not pay" and mark the period by date, never by reading null as 0 dollars.
- **Prices without `has_negative_part` and by medians.** As in Q2, we leave out the rows with a negative amount, because their amounts do not show what the trip cost, and we compare medians, because a few very expensive trips pull the means up.

### 6.1 Who pays the charge

Table 6.1. Trips and prices from 5 January to 31 March

| Year | Group | Trips per day | Share | Median `total_amount` | Median distance (miles) |
|---|---|---|---|---|---|
| 2024 | all trips | 102,048.6 | 100% | 20.50 | 1.74 |
| 2025 | all trips | 116,755.3 | 100% | 20.95 | 1.76 |
| 2025 | pays the charge | 86,393.3 | 74.0% | 21.54 | 1.80 |
| 2025 | does not pay | 30,361.9 | 26.0% | 18.45 | 1.64 |

Source: `results/q4_overview.csv`, written by `scripts/query_congestion.py`.

Three out of four trips in 2025 pay the charge. This matches the 74.01% of Report 1, which still included the `has_negative_part` rows. Demand did not fall: there are 14.4% more trips per day than in the same days of 2024, and the median price went up by only 45 cents. The paying trips have a higher median price than the others (21.54 against 18.45 dollars), but they are also slightly longer, so the difference is not only the charge itself, which is 0.75 dollars for most trips.

### 6.2 When the paying trips happen

Table 6.2. Share of trips that pay the charge by pickup hour, 2025, with median prices

| Hour | Trips per day | Share paying | Median total, paying | Median total, not paying | Median distance, not paying |
|---|---|---|---|---|---|
| 0 | 3,469.1 | 82.5% | 21.18 | 24.23 | 3.82 |
| 5 | 819.7 | 61.4% | 20.67 | 30.24 | 5.78 |
| 8 | 4,700.7 | 67.9% | 20.99 | 17.71 | 1.61 |
| 12 | 5,792.5 | 69.5% | 21.06 | 16.80 | 1.37 |
| 18 | 8,337.2 | 75.9% | 22.38 | 18.50 | 1.44 |
| 22 | 6,642.3 | 81.2% | 21.56 | 20.68 | 2.40 |

Source: `results/q4_by_hour.csv`, written by `scripts/query_congestion.py`, which has all 24 hours.

The share of paying trips is lowest in the early morning (61% at 5:00) and highest at night (above 80% from 22:00 to 3:00). The hours also show that the trips that do not pay are not one kind of trip. During the day they are short trips outside the zone, for example on the Upper East and Upper West Side, and cheaper than the paying ones (16.80 against 21.06 dollars at noon). At night and early in the morning they are longer (a median of 3.3 to 5.8 miles between midnight and 5:00) and more expensive than the paying ones. So comparing only "paying" and "not paying" would mix trip types, and the hourly table is the fairer view.

### 6.3 Where the paying trips start

Table 6.3. Pickup zones grouped by the share of their 2025 trips that pay the charge

| Share paying in 2025 | Zones | 2024 per day | 2025 per day | Change |
|---|---|---|---|---|
| 90% or more | 39 | 60,135.2 | 68,280.8 | +13.5% |
| 50% to 90% | 7 | 14,428.4 | 15,035.0 | +4.2% |
| 10% to 50% | 94 | 26,304.0 | 30,432.6 | +15.7% |
| below 10% | 117 | 833.7 | 2,746.4 | +229.4% |
| all zones | 257 | 101,701.3 | 116,494.8 | +14.5% |

Source: `results/q4_by_pickup_zone.csv`, written by `scripts/query_congestion.py`; the grouping is ours. Zones 264 and 265 and the three zones without trips in one of the years are left out.

In the 39 zones where at least 90% of the pickups pay, almost every trip crosses or stays in the charge area; 38 of them are in Manhattan, and Midtown Center, Times Square, Penn Station, Midtown East and Union Square are above 99%. Their pickups grew by 13.5%, about as much as all trips together. So from these numbers we cannot see that the charge pushed taxi trips out of the zone: if it had a negative effect on demand, other changes between the two years were larger. The seven zones where half to nine tenths of the trips pay grew least (+4.2%); they include LaGuardia (52% of its pickups pay) and Upper East Side South (52%), which lies next to the charge area. At JFK 41% of the pickups pay. In the 117 zones where almost no trip pays, 116 are outside Manhattan. Their trips tripled, but they are still only 2.4% of all trips; together with the growth inside Brooklyn in Table 5.2, this is something to look at in Report 3, but we have not checked its cause.

These are comparisons of two winters, not an experiment. Prices, apps and travel habits also changed between them, so we describe what changed together with the charge and do not claim that the charge caused it.

## 8. O2 Broadcast join

*Written by Berke Arda Türk*

### 8.1 What we changed

Q3 and Q4 join the cleaned trip table (about 20 million rows) with the zone table (265 rows), twice. Spark can do such a join in two main ways. In a **sort merge join**, both tables are shuffled so that rows with the same zone number end up in the same task, then sorted and matched. In a **broadcast hash join**, the small table is sent whole to every task, each task builds a hash table from it and matches its own trips locally, so the large table is neither shuffled nor sorted for the join.

To measure the difference we wrote `zone_pair_counts` in `src/hlds/joins.py`: it joins the zone table for both ends, as Q3 does, and counts trips per year and zone pair. Both cases set `spark.sql.autoBroadcastJoinThreshold` to -1, so Spark does not choose a broadcast join by itself, and put the old value back afterwards (Appendix A.4). The only difference is the `broadcast()` hint on the zone table in the after case. With the threshold at -1, adaptive query execution also cannot change the join into a broadcast join while the query runs, so the before case really stays a sort merge join.

### 8.2 Results

Table 8.1. O2 before and after on Berke's laptop

| Case | Join | Median (s) | Min (s) | Max (s) |
|---|---|---|---|---|
| before | sort merge join | 24.45 | 24.09 | 24.52 |
| after | broadcast hash join | 18.67 | 18.39 | 18.87 |

Source: `results/timings_berke.csv`, written by `scripts/run_benchmarks.py --machine berke --case O2`; one warm-up and five measured runs each, nothing else running on the laptop (Intel Core i7-13650HX, 20 threads, 16 GB RAM, 6 GB driver memory, Spark 4.2.0).

The broadcast join is 5.8 seconds or about 24% faster, and the five runs of each case are within half a second of each other, so the difference is clearly larger than the noise.

### 8.3 Why the time changed

The saved plans (`results/plans/berke/O2_before.txt` and `O2_after.txt`) show where the time goes. The before plan, shortened:

```text
SortMergeJoin LeftOuter
:- Sort
:  +- ShuffleQueryStage, Statistics(sizeInBytes=1421.9 MiB, rowCount=1.99E+7)
:     +- SortMergeJoin LeftOuter
:        :- Sort
:        :  +- ShuffleQueryStage, Statistics(sizeInBytes=608.1 MiB, rowCount=1.99E+7)
```

For each of the two joins, the 19.9 million cleaned trips are written out as shuffle files (608 MiB and 1.4 GiB), read back and sorted by zone number. The after plan has no shuffle and no sort for the joins:

```text
BroadcastHashJoin LeftOuter BuildRight
:- BroadcastHashJoin LeftOuter BuildRight
:  +- BroadcastQueryStage, Statistics(sizeInBytes=64.0 MiB, rowCount=265)
+- BroadcastQueryStage, Statistics(sizeInBytes=64.0 MiB, rowCount=265)
   +- ReusedExchange
```

The 265 zone rows are sent to the tasks once and reused for the second join (`ReusedExchange`). Both plans are the final plans after the query ran (`isFinalPlan=true`).

The saving is "only" a quarter because both cases still read the six files, clean them and remove duplicates; that step has its own shuffle of 3.6 GiB and is the same in both plans. In local mode a shuffle costs disk and CPU but no network, so on a real cluster we would expect the broadcast join to save more, but we did not measure this.

### 8.4 Does it help in practice?

Yes, but with a limit we should be honest about. Spark's default `spark.sql.autoBroadcastJoinThreshold` is 10 MB, and our zone table is about 12 KB, so with the default settings Spark should choose a broadcast join for it by itself. Turning the automatic broadcast off made the before case possible to measure; it is not how our query scripts run. The explicit `broadcast()` hint is useful when Spark cannot estimate the size of the small side well, for example after a filter or an aggregation, or when the setting has been changed. What the measurement shows is how much a shuffle join of 20 million rows costs on our laptop, and why a small lookup table should be broadcast.

## 9. O3 Partitioned storage

*Written by Berke Arda Türk*

### 9.1 What we changed

Until now every query started from the six raw files and cleaned them again. For O3 we store the cleaned table on disk in two ways and read it back with the same query (`src/hlds/storage.py`, Appendix A.5):
- **before:** plain Parquet. Each file holds trips from all days, in the order the cleaning step leaves them.
- **after:** Parquet partitioned by `pickup_date`, the date of the pickup. Every day gets its own folder, such as `pickup_date=2025-03-01`, and we repartition by the date before writing, so each folder has one file.

`scripts/write_clean_tables.py` writes both copies once, before the measurement; the writing is not timed as part of O3. Both copies have the same rows and columns.

Table 9.1. The two copies of the cleaned table

| Copy | Files | Size | Write time |
|---|---|---|---|
| plain Parquet | 22 | 450 MB | 27.1 s |
| partitioned by `pickup_date` | 181 | 446 MB | 29.3 s |

Source: output of `scripts/write_clean_tables.py`, one run each, including the cleaning.

The query reads one copy and computes the trips and the median `total_amount` per day for March 2025, which is about a sixth of the data. This is the kind of query Report 3 needs, for example for a chart of one month.

### 9.2 Results

Table 9.2. O3 before and after on Berke's laptop

| Case | Read from | Median (s) | Min (s) | Max (s) |
|---|---|---|---|---|
| before | plain Parquet | 1.98 | 1.90 | 2.53 |
| after | partitioned by `pickup_date` | 1.15 | 1.12 | 1.22 |

Source: `results/timings_berke.csv`, written by `scripts/run_benchmarks.py --machine berke --case O3`; same laptop, settings and method as Table 8.1.

The partitioned copy answers the query about 42% faster.

### 9.3 Why the time changed

The difference is in how the date filter reaches the files. In the after plan, the filter on `pickup_date` is a partition filter:

```text
Location: InMemoryFileIndex [file:/<project>/data/derived/clean_by_pickup_date]
PartitionFilters: [isnotnull(pickup_date#2034), (pickup_date#2034 >= 2025-03-01), (pickup_date#2034 <= 2025-03-31)]
```

Spark decides from the folder names alone which folders to open, so it reads only the 31 March folders and never touches the other 150 days (partition pruning). In the before plan there is no partition filter; the filter only reaches the Parquet reader:

```text
Location: InMemoryFileIndex [file:/<project>/data/derived/clean_plain]
PushedFilters: [IsNotNull(pickup_date), GreaterThanOrEqual(pickup_date,2025-03-01), LessThanOrEqual(pickup_date,2025-03-31)]
```

A Parquet file keeps the smallest and largest value of each column per block of rows, so the reader could skip blocks that hold no March date. But in our plain copy every block holds trips from all days, so nothing can be skipped and all 22 files are read.

The time did not fall to a sixth, though. The query is short, and a large part of its two seconds is fixed work for every query: planning, starting the jobs and listing the files. Both copies also already gain from columnar storage, because Parquet lets Spark read only the two columns the query needs out of 24.

### 9.4 Does it help in practice?

For queries that filter on dates, yes. The cost is small here: 181 files instead of 22 and two seconds more when writing. It would grow with a finer partition, for example by hour, which would give more than 4,000 small files, and a query that does not filter on the date gains nothing from the folders. The measurement also shows a larger effect we did not plan as a case: reading the cleaned table from Parquet takes about two seconds for this query, while cleaning the six raw files and counting the rows takes about 30 seconds (pilot run in `results/timings_berke.csv`). The two queries are not the same, so this is only a rough comparison, but it suggests that Report 3 should read the stored cleaned table and not clean the raw files again.

## 12. Problems and solutions

*Written by Berke Arda Türk*

### 12.5 Slow tests with a few hand-made rows

*Problem.* The eight tests of Q3 use nine hand-made trips, but they took seven minutes. Every result read the rows again from Python, and Spark split them over 20 tasks, one per thread, each with its own start-up cost.

*Solution.* In the test setup we keep the rows in memory as one partition with `coalesce(1).cache()`. The same tests then took about a minute, and we used this in the Q4, O2 and O3 tests too. Alican's tests are also slow, so the same change may help there.

### 12.6 Our own folders in the saved plans

*Problem.* `explain()` names the data files with their full local path, so the saved plans put our Windows user folders into the repository. Berke noticed it in Alican's first trial plan.

*Solution.* Alican changed `save_plan` to write the project folder as `<project>`, with a test, and Berke fixed his own trial plan the same way. The older commits keep the paths, because we do not rewrite history that is already on GitHub.

### 12.7 Zones that are not places and names that are not unique

*Problem.* Two rows of the zone table are not places (264 `Unknown` and 265 `Outside of NYC`), and three zone numbers share one name. Ranking them as places, or grouping by name alone, would have given wrong rankings without any error.

*Solution.* Q3 and Q4 group by zone number and keep the name only as a label, and they leave zones 264 and 265 out of the rankings but keep them in the borough flows (Section 5).

### 12.8 Tests that were wrong, not the code

*Problem.* Two of our tests failed although the code was right. The shares of the borough flows are rounded to four places, so they added up to 1.0001 and not exactly 1. And we expected the plan of the plain Parquet copy to show an empty partition filter, but such a plan has no partition filter line at all.

*Solution.* We looked at the actual numbers and plans before changing anything, then fixed the tests: the shares are compared to three places, and the O3 test checks that the plain plan has no partition filter but does push the date filter to the Parquet reader. This also made the difference between the two plans clearer to us (Section 9.3).

## 13. Dashboard tool for Report 3

*Written by Berke Arda Türk*

We will build the charts and the dashboard of Report 3 in Python with **Plotly** for the charts and **Streamlit** for the dashboard. The course allows Tableau, Power BI, Apache Superset or Python libraries, and we chose Python for these reasons:
- **It reads our results directly.** Every query already writes small CSV files to `results/`, and the dashboard only needs to read them; Spark does not have to run again.
- **It stays in the repository.** The dashboard is a Python file that both of us can run with one command, review in a pull request and change in small commits. Power BI and Tableau save binary files whose changes we cannot see in Git.
- **It is light.** Apache Superset would need Docker and a database on our laptops, which is a lot of setup for a few small tables.
- **Plotly charts are interactive.** In Streamlit we can add a choice of year or hour next to a chart, and the same Plotly charts can be saved as pictures for the report.

The planned views follow the objectives: the hour by weekday heat map and the daily line of O1, prices and tips by hour for O2, the top zones and borough flows for O3, the share of paying trips by hour and zone for O4, and a bar chart of the times before and after each optimization. Streamlit and Plotly are not in `requirements.txt` yet; we will add them with fixed versions when we start Report 3.

## Appendix A. Code excerpts

*Written by Berke Arda Türk*

The full code is in the repository. These excerpts show the joins, the two queries and the two optimizations of this report.

### A.1 Joining the zone table (Q3, Q4, O2)

The zone table is joined twice, once for each end of the trip. With `broadcast_zones` the zone table is sent whole to every task (O2).

```python
def add_zone_names(trips, zones, broadcast_zones=False):
    """Join the zone table twice, for the pickup and the drop-off zone.

    With `broadcast_zones` the zone table is sent whole to every task (optimization O2); without it,
    Spark decides the join type itself.
    """
    named = trips.withColumn("year", F.year("tpep_pickup_datetime"))
    for side, id_column in SIDES.items():
        names = zones.select(F.col("LocationID").alias(id_column), F.col("Borough").alias(f"{side}_borough"),
                             F.col("Zone").alias(f"{side}_zone"))
        if broadcast_zones:
            names = F.broadcast(names)
        # A left join keeps a trip even if its zone id were missing from the table (none is in our six months).
        named = named.join(names, id_column, "left")
    return named
```

### A.2 The busiest routes in Spark SQL (Q3)

`ROW_NUMBER` ranks the routes inside each year; zone numbers break ties, so the order is the same on every run. Zones 264 and 265 are left out.

```python
TOP_ROUTES_SQL = """
WITH routes AS (
    SELECT year, PULocationID, pickup_borough, pickup_zone, DOLocationID, dropoff_borough, dropoff_zone,
           COUNT(*) AS trips
    FROM q3_trips
    WHERE PULocationID NOT IN ({unknown}) AND DOLocationID NOT IN ({unknown})
    GROUP BY year, PULocationID, pickup_borough, pickup_zone, DOLocationID, dropoff_borough, dropoff_zone
),
ranked AS (
    -- Zone ids break ties, so the order is the same on every run.
    SELECT *, ROW_NUMBER() OVER (PARTITION BY year ORDER BY trips DESC, PULocationID, DOLocationID) AS rank_in_year
    FROM routes
)
SELECT r.year, r.rank_in_year, r.PULocationID AS pickup_zone_id, r.pickup_borough, r.pickup_zone,
       r.DOLocationID AS dropoff_zone_id, r.dropoff_borough, r.dropoff_zone, r.trips,
       ROUND(r.trips / d.days, 1) AS trips_per_day
FROM ranked r
JOIN q3_days d ON r.year = d.year
WHERE r.rank_in_year <= {top}
ORDER BY r.year, r.rank_in_year
"""
```

### A.3 The charge period (Q4)

Both years start on 5 January. A missing charge, as in all of 2024, means "does not pay", never 0 dollars.

```python
def charge_window(trips):
    pickup = F.col("tpep_pickup_datetime")
    return (trips
            .filter(~F.col("has_negative_part"))
            .filter(F.dayofyear(pickup) >= CHARGE_START_DAY)
            .withColumn("year", F.year(pickup))
            .withColumn("hour", F.hour(pickup))
            # The 2024 files have no charge column, so a missing value means "does not pay", never 0 dollars paid.
            .withColumn("pays_charge", F.coalesce(F.col("cbd_congestion_fee") > 0, F.lit(False))))
```

### A.4 The O2 cases

Both cases turn the automatic broadcast off and put the setting back afterwards; only the `broadcast()` hint differs.

```python
@contextmanager
def automatic_broadcast_off(spark):
    """Stop Spark from turning small joins into broadcast joins by itself, then restore the old setting.

    With the threshold at -1 adaptive query execution cannot switch to a broadcast join while the query runs
    either, so a join without `broadcast()` stays a sort merge join.
    """
    old_value = spark.conf.get(AUTO_BROADCAST)
    spark.conf.set(AUTO_BROADCAST, "-1")
    try:
        yield
    finally:
        spark.conf.set(AUTO_BROADCAST, old_value)


def zone_joins_shuffle(spark):
    # Both O2 cases run with automatic broadcast off, so the only difference is the broadcast() hint.
    with automatic_broadcast_off(spark):
        return zone_pair_counts(clean_trips(load_trips(spark)), load_zones(spark), broadcast_zones=False)


def zone_joins_broadcast(spark):
    with automatic_broadcast_off(spark):
        return zone_pair_counts(clean_trips(load_trips(spark)), load_zones(spark), broadcast_zones=True)
```

### A.5 The O3 copies and query

The partitioned copy is repartitioned by the date first, so each day folder holds one file. The same query runs on both copies.

```python
def write_partitioned(trips, path):
    # Without the repartition every task would write its own small file into every day folder.
    dated = add_pickup_date(trips).repartition(PARTITION_COLUMN)
    dated.write.mode("overwrite").partitionBy(PARTITION_COLUMN).parquet(str(path))


def daily_summary(trips, start=FILTER_START, end=FILTER_END):
    """Trips and median total per day between `start` and `end`, collected; returns the DataFrame that ran."""
    day = F.col(PARTITION_COLUMN)
    summary = (trips.filter((day >= F.lit(start).cast("date")) & (day <= F.lit(end).cast("date")))
               .groupBy(PARTITION_COLUMN)
               .agg(F.count("*").alias("trips"),
                    F.round(F.percentile_approx("total_amount", MEDIAN), 2).alias("median_total_amount"))
               .orderBy(PARTITION_COLUMN))
    summary.collect()
    return summary
```
