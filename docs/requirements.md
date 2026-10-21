# Course requirements (Project 2, Apache Spark)

Our summary of the project brief and of what was said in the first lab. The brief itself is the reference.

## General
- Individual or team of up to four students. Three stages, one report per stage.
- The same dataset and topic in all three reports. At least 100,000 records; larger is better.
- Source code is submitted as separate files together with each report.
- In a team, every report states what each member did.
- Every performance comparison uses the same dataset and the same computing environment.
- Visualizations are required in the final report.

## Environment
- Spark locally (or standalone), or in a cloud environment such as Databricks.
- Python / PySpark and Spark SQL. Parquet or ORC preferred; CSV and JSON where they fit.
- Visualization: Tableau, Power BI, Apache Superset or Python libraries.
- Optional: Spark MLlib, Kafka, Docker Compose, REST endpoints.

## Report 1: data preparation and environment (30 points)
- Choose the dataset and describe the analytical problem.
- Set up Spark and load the data.
- Clean the data: missing values, type conversions, duplicates, invalid entries.
- Show the structure and basic descriptive statistics; define the objectives for Reports 2 and 3.
- Include: dataset source and size, problem and objectives, environment description, screenshots of the setup and the loaded data, code excerpts, a summary table of statistics, problems met and how we solved them.
- Points: data preparation and loading 10, Spark setup 10, clarity of data, problem and statistics 5, report quality 5.

## Report 2: processing, analysis and optimization (40 points)
- Filtering, sorting, grouping, aggregation and at least one join where it makes sense, with Spark SQL and/or the DataFrame API.
- At least three meaningful queries that answer the objectives from Report 1.
- At least two optimizations, such as caching/persistence, partitioning, broadcast join, columnar storage.
- Execution time before and after each optimization, same data and same environment, preferably in a table.
- Explain why the time changed and whether the optimization really helped.
- Prepare aggregated outputs for Report 3. MLlib is an optional extension.
- Points: data operations and analysis 15, optimizations and comparison 10, interpretation 10, code and report quality 5.

## Report 3: visualization and summary (30 points)
- Use the aggregated Spark results to build several fitting charts or a dashboard.
- For each main chart: what it shows, why this chart type, what we learn from it.
- Summarize the whole project: problem, workflow, optimization results, conclusions, limitations, future improvements.
- Points: quality of visualizations 10, interpretation and conclusions 10, structure of the report 5, dashboard and visual presentation 5.

## Deadlines
- Report 1: 18 Nov 2026, 23:59
- Report 2: 23 Dec 2026, 23:59
- Report 3: 14 Jan 2027, 23:59
