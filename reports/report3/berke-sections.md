# Report 3: sections by Berke

## 4. Dashboard

*Written by Berke Arda Türk*

The dashboard puts all results of the project on one page. It is a Streamlit app with Plotly charts (Report 2, Section 13) and runs with one command from the root of the repository:

```
streamlit run dashboard/app.py
```

It reads only the small CSV files that the Spark queries wrote to `results/`, with pandas. Spark does not run, so the dashboard opens in a few seconds on any laptop with the packages of `requirements.txt`. The PNG pictures in this report are drawn by the same chart functions (`scripts/export_charts.py`), so the report and the dashboard always show the same charts.

### 4.1 Structure

Table 4.1. The tabs of the dashboard

| Tab | Question | Charts |
|---|---|---|
| Key findings | What changed between Q1 2024 and Q1 2025, and what does it mean? | Five summary numbers, one chart for each of the five findings below |
| Q1 · Demand | When do people take a taxi? | Trips per day with 2024 lined up by weekday; hour by weekday heat maps of trips and of the change |
| Q2 · Prices and tips | How do prices, speed and tips differ by hour and payment group? | Trips by hour for each payment group; speed, price per mile and tip of card trips by hour |
| Q3 · Places | Where do the trips start and end? | Busiest pickup or drop-off zones; pickups by borough and payment group; borough flows |
| Q4 · Zone charge | Which trips pay the zone charge, when and where? | Summary numbers; share of paying trips by hour and in the busiest zones |
| Performance | Did the optimizations help? | Before and after times of O1 to O3, with every measured run |

The first tab is new in this report. A reader who opens the dashboard sees the answer to the project question first and can go to the tab of a query for the details. Every other tab starts with one sentence that says what it shows, the "In short" line. The sidebar explains the data (period, cleaning, the start of the zone charge) and shows the colour of each payment group and year.

### 4.2 Design choices

- **The same colour for the same thing everywhere.** Credit card is blue, flex fare orange, cash aqua and other yellow, and 2024 is grey and 2025 violet. The colours are defined once in `dashboard/colors.py`, and both of us import them. We checked the payment colours with a colour blindness simulation in the light and the dark theme. Aqua and yellow have less contrast than 3:1 on white, so no chart relies on colour alone: every chart has a legend or labels, a hover text and a table.
- **Flex fare on its own.** Report 2 (Section 11.4) showed that most of the new trips are flex fare, so every chart that compares the years shows flex fare as its own bar, line or colour. A chart of all trips together would show the growth without showing where it comes from.
- **The numbers behind every chart.** Under each chart the dashboard names its source file and has a *Show the numbers* table. The summary numbers and the sentences of the key findings tab are computed from the same files (`dashboard/findings.py`), so they change with the results and cannot drift away from the charts.
- **Light and dark theme.** The charts take the colours of the Streamlit theme, and the dark theme has its own payment and year colours with enough contrast on a dark background.
- **A few controls, not many.** The Q3 tab can switch between pickup and drop-off zones and show 5 to 20 zones, and the Q4 tab can show 5 to 25 zones. We left out filters by date or borough, because each result file is already grouped for one question and a filter would only hide rows of it.

### 4.3 Screenshots

The screenshots show each tab in the light theme at a width of 1440 pixels, from the top of the page to the last chart. The sidebar is open in all of them; the *Show the numbers* tables are closed. They were taken with Playwright (Chromium) from the final dashboard, including the key findings tab.

![The key findings tab: five summary numbers and one chart for each finding](screenshots/dashboard-key-findings.png)

![The Q1 tab: trips per day and the hour by weekday heat maps](screenshots/dashboard-q1-demand.png)

![The Q2 tab: trips by hour for each payment group and card trips by hour](screenshots/dashboard-q2-prices.png)

![The Q3 tab: busiest zones, pickups by borough and payment group, and borough flows](screenshots/dashboard-q3-places.png)

![The Q4 tab: summary numbers and the share of paying trips by hour and zone](screenshots/dashboard-q4-zone-charge.png)

![The performance tab: before and after times of O1 to O3](screenshots/dashboard-performance.png)

The dashboard has its own tests (`tests/test_dashboard.py`, `tests/test_dashboard_q1_q2.py`, `tests/test_findings.py`). One of them runs the whole app on the real result files with Streamlit's test tool. It found an error that the single chart tests did not: the same chart on two tabs got the same internal ID, and Streamlit stopped drawing the tabs after it. Each chart of the key findings tab now has its own key.

## 5. Key findings and their practical meaning

*Written by Berke Arda Türk*

The project asked what changed in New York yellow taxi trips between the first quarters of 2024 and 2025, the first winter of the Manhattan congestion relief zone charge. Here we give the five main answers and what they mean for two groups of readers: the city, which plans transport and set the charge, and taxi operators and drivers, who decide where and when to work. The charts of each finding are in the key findings tab of the dashboard; the interpretation of every chart is in Section 3.

Table 5.1. The five summary numbers of the key findings tab

| Number | Value | Source |
|---|---|---|
| Trips per day, Q1 2025 | 118,872 (+17.2% on Q1 2024) | `results/q1_daily_average.csv` |
| Flex fare share of trips | 19.5% (7.0% in 2024) | `results/q2_borough_payment.csv` |
| Extra trips per day that are flex fare | 91.5% (15,993 of 17,471) | `results/q2_borough_payment.csv` |
| 2025 trips that pay the zone charge, from 5 January | 74% | `results/q4_overview.csv` |
| Median total price, from 5 January | 20.95 dollars (+0.45 on 2024) | `results/q4_overview.csv` |

### 5.1 More taxi trips, mostly outside working hours

There were 101,401 trips per day in Q1 2024 and 118,872 in Q1 2025, 17.2% more. The 7-day mean of 2025 is above the one of 2024 on every day but one in the first week of January. The growth is largest in the late evening, at night and at weekends: 69% of the extra trips per week fall outside 7:00 to 19:00 on Monday to Friday (`results/q1_hour_weekday.csv`).

- **For the city.** The zone charge started in a winter when taxi demand grew. Whatever the charge did, it did not make the total number of taxi trips fall.
- **For taxi operators.** There are more trips to serve than a year earlier, and most of the extra ones are in the evening, at night and at weekends, not in the busy working-day hours.

### 5.2 Nine in ten of the extra trips are flex fare

![Where the extra trips come from, by payment group](figures/findings_growth_by_payment.png)

Flex fare trips grew from 7,146 to 23,139 per day and are 91.5% of the extra trips. Card trips grew by 4% and cash trips fell by 16% (Figure, `results/q2_borough_payment.csv`). In 2025 the median recorded price per mile of a flex fare trip is 8.78 dollars, against 12.37 dollars for a card trip, and flex fare trips record no tip (`results/q2_by_payment.csv`). The data only tells us that these trips have `payment_type` 0, not how they were booked or paid.

- **For the city.** A count of all trips hides this change. Any report on taxi demand, and any study of the zone charge, should show flex fare on its own, because one group of trips grew while the others stayed almost flat.
- **For taxi operators.** The growth is in trips with a lower recorded price per mile and no recorded tip. More trips therefore do not mean the same growth in income, and an operator who looks only at the number of trips would overestimate it.

### 5.3 The fastest growth is outside Manhattan

Pickups grew by 229% in Brooklyn and by 214% in the Bronx, against 15% in Manhattan (Report 2, Table 11.1). They start from a small base, about 3,150 and 730 pickups per day in 2025, and about three in four of them are flex fare (74% in Brooklyn, 71% in the Bronx). The airports did not take part in the growth: trips from and to JFK, LaGuardia and Newark stayed flat or fell slightly.

- **For the city.** Yellow taxis now serve a new demand outside Manhattan. Plans for taxi pickups there, for example taxi stands or pickup rules at busy places in Brooklyn, should use 2025 data and not the years before.
- **For taxi operators.** The new pickups outside Manhattan are almost all flex fare trips. This is the part of the city where flex fare matters most, and where a driver can find new trips that did not exist a year earlier.

### 5.4 No sign that the zone charge lowered taxi demand

![Change in pickups, zones grouped by how many trips pay](figures/findings_zone_groups.png)

Three in four trips of 2025 pay the zone charge. We grouped the pickup zones by the share of their 2025 trips that pay (Report 2, Table 6.3). In the 39 zones where at least 90% of the trips pay, almost all of them in Manhattan, pickups grew by 13.5%, about as much as all zones together (+14.5%). The median total price rose by 0.45 dollars, less than the charge of 0.75 dollars that most trips pay.

- **For the city.** In the first winter, taxi trips that start inside the charge area did not move away from it. For taxi riders the charge is small next to the median price of a trip (20.95 dollars), which fits with the demand we see.
- **For taxi operators.** Riders kept taking taxis inside the zone, so there is no reason in these numbers to avoid it.

This finding has a clear limit. Two winters are not an experiment, and the growth of flex fare is much larger than any change we can link to the charge. We can say that demand in the charged zones did not fall, but not what it would have been without the charge.

### 5.5 Reading and cleaning the raw files is the main cost of the analysis

Each of the three optimizations made its query faster: caching by 33%, the broadcast join by 24% and partitioned storage by 42% (Report 2, Table 10.1). Caching saved the most seconds, because it avoids reading and cleaning the six raw files again, which takes about 30 seconds every time.

- **For the next analysis of these data.** Clean the raw files once, store the cleaned table as Parquet partitioned by pickup date, and read only that copy. A query on one month then reads one sixth of the files.
- **For a dashboard.** Do not run Spark behind the charts. Our dashboard reads small result files and opens in seconds; Spark is needed only when a new question needs a new grouping.

### 5.6 What the findings do not show

All findings compare two winters, January to March of 2024 and 2025. They describe what changed together with the zone charge and do not show what the charge caused. We do not know how flex fare trips are booked, so we describe their growth and do not explain it. The limitations and the improvements we would make are in Section 6.
