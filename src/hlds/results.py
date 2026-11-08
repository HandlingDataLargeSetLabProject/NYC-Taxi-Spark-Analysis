"""Write small aggregated Spark results to CSV, so the charts of Report 3 do not need Spark again."""

import csv


def write_csv(frame, path):
    """Collect `frame` to the driver and write it with a header. Only for small, already grouped results."""
    rows = frame.collect()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(frame.columns)
        writer.writerows(rows)
    return path
