from __future__ import annotations

import csv
import datetime as DT
import sys
from pathlib import Path
from typing import TypedDict

from aw_client import ActivityWatchClient
from aw_client.client import Event  # type:ignore
from tqdm.auto import tqdm


class ManictimeEvent(TypedDict):
    Name: str
    Start: str
    # End: str
    Duration: str
    Process: str


class WindowEventData(TypedDict):
    # this is meant to be the executable name,
    # but manictime doesn't have that info,
    # so we just use the "Process" field
    app: str
    # window title
    title: str


def to_window_event(row: ManictimeEvent) -> Event:
    start = DT.datetime.fromisoformat(row["Start"])
    # the timestamps are all naive:
    assert start.tzinfo is None, start.tzinfo
    # so we assume UTC:
    start = start.astimezone(DT.UTC)
    duration_parts = row["Duration"].split(":")
    assert len(duration_parts) == 3, duration_parts
    duration = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
    window_data: WindowEventData = {"app": row["Process"], "title": row["Name"]}
    return Event(
        data=window_data,  # type:ignore
        timestamp=start,
        duration=duration,
    )


def main():
    if len(sys.argv) < 2:
        raise ValueError("Pass the path to the input file as a CLI argument")
    inp_path = Path(sys.argv[1]).resolve()
    if not inp_path.exists():
        raise ValueError("Path doesn't exist:", inp_path)

    print("Connecting to AW server...")
    client = ActivityWatchClient("aw-from-manictime")
    client.connect()

    bucket_name = f"aw-watcher-window_{client.client_hostname}"
    existing_buckets = client.get_buckets()
    if bucket_name not in existing_buckets:
        raise ValueError(
            f"Bucket {bucket_name} doesn't already exist, aborting. Existing buckets:", list(existing_buckets)
        )

    print("Reading input file...")
    # the manictime files I tested this on had a BOM at the start,
    # so utf-8-sig
    with inp_path.open(newline="", encoding="utf-8-sig") as fo:
        reader = csv.DictReader(fo)
        assert reader.fieldnames is not None
        assert {"Start", "Duration", "Process", "Name"} < set(reader.fieldnames), reader.fieldnames
        rows: list[ManictimeEvent] = list(reader)  # type:ignore
    print(f"Loaded {len(rows)} rows from the input CSV.")
    converted_rows = [to_window_event(row) for row in rows]
    print(f"Converted all rows to aw-watcher-window events")

    if (
        input(
            f"These events will now be submitted to the AW server into bucket {bucket_name!r}. Type 'yes' to confirm: "
        )
        .lower()
        .strip()
        != "yes"
    ):
        print("Aborted.")
        return
    print("Inserting events...")
    chunk_size = 100
    prog = tqdm(total=len(converted_rows))
    for i in range(0, len(converted_rows), chunk_size):
        chunk = converted_rows[i : i + chunk_size]
        client.insert_events(bucket_name, chunk)
        prog.update(len(chunk))
    prog.close()
    print("Done.")


if __name__ == "__main__":
    main()
