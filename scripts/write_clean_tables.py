"""Write the cleaned table twice for optimization O3: as plain Parquet and partitioned by pickup date.

Run once before `python scripts/run_benchmarks.py --machine <label> --case O3`. The copies go to data/derived/,
which is not committed. The write time is printed but not part of the O3 measurement.
"""

import sys
import time
from pathlib import Path

# Make the hlds package in src/ importable when this file is run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hlds.cleaning import clean_trips
from hlds.loading import load_trips
from hlds.session import get_spark
from hlds.storage import PARTITIONED_TABLE, PLAIN_TABLE, write_partitioned, write_plain


def folder_size(path):
    files = [file for file in path.rglob("*.parquet")]
    return len(files), sum(file.stat().st_size for file in files)


def main():
    spark = get_spark("write-clean-tables")
    spark.sparkContext.setLogLevel("ERROR")
    for name, write, path in [("plain", write_plain, PLAIN_TABLE), ("partitioned", write_partitioned, PARTITIONED_TABLE)]:
        start = time.perf_counter()
        write(clean_trips(load_trips(spark)), path)
        seconds = time.perf_counter() - start
        files, size = folder_size(path)
        print(f"{name}: {files} files, {size / 1024 ** 2:.1f} MB, written in {seconds:.1f} s")
    spark.stop()


if __name__ == "__main__":
    main()
