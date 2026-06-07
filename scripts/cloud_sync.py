#!/usr/bin/env python3
"""
Chunked cloud sync helper for scraped paper JSON.
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests

DEFAULT_CLOUD_URL = "https://research-tracker-466018.uc.r.appspot.com"
TRANSIENT_STATUS_CODES = {500, 502, 503, 504}


def normalize_cloud_url(cloud_url: Optional[str]) -> str:
    cloud_url = (cloud_url or "").strip() or DEFAULT_CLOUD_URL
    if not cloud_url.startswith(("http://", "https://")):
        cloud_url = "https://" + cloud_url
    return cloud_url.rstrip("/")


def _positive_int(value: Optional[str], default: int) -> int:
    try:
        parsed = int(value) if value is not None else default
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _post_sync_chunk(
    session: requests.Session,
    cloud_url: str,
    chunk: List[Dict],
    chunk_number: int,
    total_chunks: int,
    timeout: int,
    max_retries: int,
) -> Optional[Dict]:
    endpoint = f"{cloud_url}/api/sync-papers"

    for attempt in range(1, max_retries + 1):
        try:
            response = session.post(
                endpoint,
                json=chunk,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            if attempt < max_retries:
                wait_seconds = min(60, 5 * attempt)
                print(
                    f"Chunk {chunk_number}/{total_chunks} request failed on attempt "
                    f"{attempt}/{max_retries}: {exc}. Retrying in {wait_seconds}s..."
                )
                time.sleep(wait_seconds)
                continue
            print(f"Cloud sync request failed for chunk {chunk_number}/{total_chunks}: {exc}")
            return None

        if response.status_code == 200:
            return response.json()

        response_text = response.text[:1000]
        if response.status_code in TRANSIENT_STATUS_CODES and attempt < max_retries:
            wait_seconds = min(60, 5 * attempt)
            print(
                f"Chunk {chunk_number}/{total_chunks} failed with {response.status_code} "
                f"on attempt {attempt}/{max_retries}. Retrying in {wait_seconds}s..."
            )
            print(f"Response: {response_text}")
            time.sleep(wait_seconds)
            continue

        print(f"Cloud sync failed for chunk {chunk_number}/{total_chunks}: {response.status_code}")
        print(f"Response: {response_text}")
        return None

    return None


def sync_to_cloud(
    papers_data: List[Dict],
    cloud_url: Optional[str] = None,
    chunk_size: Optional[int] = None,
    max_retries: Optional[int] = None,
    timeout: Optional[int] = None,
) -> bool:
    cloud_url = normalize_cloud_url(cloud_url or os.getenv("CLOUD_URL"))
    chunk_size = chunk_size or _positive_int(os.getenv("SYNC_CHUNK_SIZE"), 50)
    max_retries = max_retries or _positive_int(os.getenv("SYNC_MAX_RETRIES"), 3)
    timeout = timeout or _positive_int(os.getenv("SYNC_TIMEOUT_SECONDS"), 180)

    print(f"Syncing {len(papers_data)} papers to cloud database...")
    print(f"Cloud URL: {cloud_url}")
    print(f"Chunk size: {chunk_size}; max retries: {max_retries}; timeout: {timeout}s")

    if not papers_data:
        print("No papers to sync.")
        return True

    totals = {
        "synced_papers": 0,
        "updated_papers": 0,
        "skipped_papers": 0,
        "total_processed": 0,
    }
    total_chunks = (len(papers_data) + chunk_size - 1) // chunk_size

    with requests.Session() as session:
        for start in range(0, len(papers_data), chunk_size):
            chunk = papers_data[start:start + chunk_size]
            chunk_number = start // chunk_size + 1
            print(f"Posting chunk {chunk_number}/{total_chunks} ({len(chunk)} papers)...")

            result = _post_sync_chunk(
                session=session,
                cloud_url=cloud_url,
                chunk=chunk,
                chunk_number=chunk_number,
                total_chunks=total_chunks,
                timeout=timeout,
                max_retries=max_retries,
            )

            if result is None:
                return False

            for key in totals:
                totals[key] += result.get(key, 0)

            print(
                f"Chunk {chunk_number}/{total_chunks} synced: "
                f"{result.get('synced_papers', 0)} new, "
                f"{result.get('updated_papers', 0)} updated, "
                f"{result.get('skipped_papers', 0)} skipped"
            )

        print("Cloud sync successful.")
        print(f"   Synced: {totals['synced_papers']} new papers")
        print(f"   Updated: {totals['updated_papers']} existing papers")
        print(f"   Skipped: {totals['skipped_papers']} papers")
        print(f"   Total processed: {totals['total_processed']} papers")

        try:
            stats_response = session.get(f"{cloud_url}/api/database-stats", timeout=30)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print("Updated cloud database stats:")
                print(f"   Total papers: {stats.get('total_papers', 0)}")
                for journal, count in stats.get("journal_stats", {}).items():
                    print(f"   {journal}: {count} papers")
        except requests.RequestException:
            print("Cloud database stats not available.")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync scraped paper JSON to the cloud database.")
    parser.add_argument("papers_json", help="Path to the scraped papers JSON file.")
    parser.add_argument("--cloud-url", default=os.getenv("CLOUD_URL", DEFAULT_CLOUD_URL))
    parser.add_argument("--chunk-size", type=int, default=None)
    parser.add_argument("--max-retries", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args()

    with open(args.papers_json, "r") as file:
        papers_data = json.load(file)

    return 0 if sync_to_cloud(
        papers_data,
        cloud_url=args.cloud_url,
        chunk_size=args.chunk_size,
        max_retries=args.max_retries,
        timeout=args.timeout,
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
