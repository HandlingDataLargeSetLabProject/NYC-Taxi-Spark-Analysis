# Environment setup

How we set up Spark locally for this project. We run Spark in local mode (`local[*]`) on our own laptops, so there is no cluster to install. The steps were tested on Windows 11; on Linux or macOS skip the Windows-only step.

## Versions
| Component | Version | Why |
|---|---|---|
| Python | 3.12 | supported by PySpark 4.2 |
| Java | 17 (Eclipse Temurin) | Spark 4.x needs Java 17 or newer; Java 8 no longer works |
| PySpark | 4.2.0 (`requirements.txt`) | latest release when we started; bundles Spark 4.2.0 and the Hadoop 3.5.0 client |
| winutils | Hadoop 3.3.6 build | Windows only, needed to write files (see step 4) |
| Git | 2.53 | Git for Windows, its `sh` also runs our local hooks |

PySpark from pip already contains Spark itself, so we do not download Spark separately and do not set `SPARK_HOME`.

## Steps

### 1. Python
Install Python 3.12 from python.org and check it:
```
python --version
```

### 2. Java 17
Install Eclipse Temurin 17 (JDK) from adoptium.net. The ZIP version works without administrator rights: unpack it, for example to `C:\Users\<user>\.jdks\jdk-17`, and set the user variable `JAVA_HOME` to that folder. Spark uses `JAVA_HOME`, so another Java on `PATH` (in our case an old Java 8) does not matter.
```
setx JAVA_HOME "C:\Users\<user>\.jdks\jdk-17"
```
Open a new terminal afterwards; environment variables are only read when a terminal starts.

### 3. Virtual environment and PySpark
From the repository root:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
`.venv/` is in `.gitignore`. On Linux or macOS activate it with `source .venv/bin/activate`.

### 4. winutils (Windows only)
Spark writes local files through Hadoop's file system layer, and on Windows Hadoop needs `winutils.exe` and `hadoop.dll`. They are not part of the official Hadoop release. Without them Spark can still compute, but every `write` fails and the log shows `Did not find winutils.exe` and `HADOOP_HOME and hadoop.home.dir are unset`.

We used the Hadoop 3.3.6 build from the `cdarlint/winutils` repository on GitHub. There is no build for Hadoop 3.5 yet, and 3.3.6 works with the 3.5.0 client inside PySpark 4.2.0.
1. Put `winutils.exe` and `hadoop.dll` into `C:\Users\<user>\hadoop\bin`.
2. Set the user variable `HADOOP_HOME` to `C:\Users\<user>\hadoop`.
3. Add `%HADOOP_HOME%\bin` to the user `PATH`.

### 5. Data
```
python scripts/download_data.py
```
This downloads January to March of 2024 and 2025 and the zone lookup table into `data/raw/` (about 350 MB). The `data/` folder is never committed.

### 6. Check
Start Python in the virtual environment and run:
```python
import os, sys
os.environ["PYSPARK_PYTHON"] = sys.executable

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.master("local[*]").appName("check").getOrCreate()
print(spark.version)

df = spark.read.parquet("data/raw/yellow_tripdata_2025-01.parquet")
print(df.count())
df.printSchema()

df.limit(1000).write.mode("overwrite").parquet("data/check.parquet")
print(spark.read.parquet("data/check.parquet").count())

plus_one = F.udf(lambda x: x + 1, "long")
spark.range(3).select(plus_one("id")).show()
```
Expected: `4.2.0`, `3475226` rows for January, the schema with 20 columns, `1000` rows read back, and a small table with 1, 2, 3. The write checks winutils and the last line checks that Spark can start Python workers.

Row counts we got:
| File | Rows | Columns |
|---|---|---|
| `yellow_tripdata_2024-01.parquet` | 2,964,624 | 19 |
| `yellow_tripdata_2024-02.parquet` | 3,007,526 | 19 |
| `yellow_tripdata_2024-03.parquet` | 3,582,628 | 19 |
| `yellow_tripdata_2025-01.parquet` | 3,475,226 | 20 |
| `yellow_tripdata_2025-02.parquet` | 3,577,543 | 20 |
| `yellow_tripdata_2025-03.parquet` | 4,145,257 | 20 |
| `taxi_zone_lookup.csv` | 265 | 4 |

The six trip files have 20,752,804 rows together. The 2024 files have no `cbd_congestion_fee` column; all other columns and types are the same.

## Problems we met
| Problem | Cause | Fix |
|---|---|---|
| `df.write.parquet(...)` fails, log says `Did not find winutils.exe` | Hadoop needs native helpers on Windows | step 4 |
| Session does not start: `UnsupportedClassVersionError ... class file version 61.0`, then Python waits forever | `JAVA_HOME` was not set, so Spark used the old Java 8 on `PATH` | install Java 17 and set `JAVA_HOME` (step 2) |
| Python UDFs fail with `Python was not found`, while `count()` works | Spark workers look for `python3`, which Windows sends to the Microsoft Store shortcut | set `PYSPARK_PYTHON` to `sys.executable` before creating the session; `get_spark` in `src/hlds/session.py` does this |
| Warning `'Large' is not recognized as an internal or external command` at start | the project path contained spaces (`Handling Large Data Sets`) and PySpark's Windows start script does not quote it | harmless, but we moved the project to a path without spaces (`Desktop\HLDS`) and the warning is gone |
| Warning that Arrow optimization failed because PyArrow or Pandas is not installed | we only install PySpark for now | harmless; Spark falls back to normal UDFs |

## Machine used for Berke's measurements
| | |
|---|---|
| CPU | Intel Core i7-13650HX, 14 cores, 20 threads |
| RAM | 16 GB |
| OS | Windows 11 Pro |
| Spark | 4.2.0, local mode `local[*]`, driver memory 4g (`get_spark`), other settings default |
| Java | Temurin 17.0.20.1 |

All of Berke's timings in Report 2 come from this machine.

## Machine used for Alican's measurements
| | |
|---|---|
| CPU | Intel Core i7-14650HX, 16 cores, 24 threads |
| RAM | 32 GB |
| OS | Windows 11 Pro |
| Python | 3.14.7 |
| Spark | 4.2.0, local mode `local[*]`, driver memory 4g (`get_spark`), other settings default |
| Java | Microsoft OpenJDK 21.0.12.1 |

All of Alican's timings in Report 2 come from this machine. It already had Java 21, so we used it instead of installing Java 17, and Python 3.14 instead of 3.12. The check from step 6 passed with both: 3,475,226 rows for January, the Python UDF returned 1, 2, 3, and the write and read back of 1,000 rows worked with winutils.

## Screenshots
Screenshots for Report 1 are in `reports/screenshots/`:
- `env-versions.png`: `python --version`, `java -version` with `JAVA_HOME` and `pip show pyspark`
- `env-check.png`: the check from step 6 in the Python shell: Spark version, row count, schema, the write and read back, and the Python UDF
- `env-spark-ui.png`: the Spark UI at http://localhost:4040 while the check runs
- `env-data.png`: `data/raw/` with the downloaded files
