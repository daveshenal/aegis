"""
One-off script to seed Pinecone with sample documents for local development and testing.

Usage:
    python scripts/ingest_sample_docs.py --dir ./sample_docs
    python scripts/ingest_sample_docs.py --file ./sample_docs/paper.pdf
"""

import argparse
import os
import sys
import time

# Add project root to path so app imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval.ingestion import ingest_from_local
from app.observability.logging import setup_logging, get_logger

setup_logging()
log = get_logger("ingest_sample_docs")

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def ingest_file(file_path: str) -> None:
    ext = os.path.splitext(file_path)[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        log.warning(f"Skipping unsupported file type: {file_path}")
        return

    log.info(f"Ingesting: {file_path}")
    start = time.time()

    try:
        chunk_count = ingest_from_local(file_path)
        latency = round(time.time() - start, 2)
        log.info(f"Done: {file_path} — {chunk_count} chunks in {latency}s")
    except Exception as e:
        log.error(f"Failed to ingest {file_path}: {e}")


def ingest_directory(dir_path: str) -> None:
    files = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if os.path.splitext(f)[-1].lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        log.warning(f"No supported files found in: {dir_path}")
        return

    log.info(f"Found {len(files)} files in {dir_path}")

    for file_path in sorted(files):
        ingest_file(file_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed Pinecone with sample documents."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to a single file to ingest.")
    group.add_argument("--dir",  type=str, help="Path to a directory of files to ingest.")

    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            log.error(f"File not found: {args.file}")
            sys.exit(1)
        ingest_file(args.file)

    elif args.dir:
        if not os.path.isdir(args.dir):
            log.error(f"Directory not found: {args.dir}")
            sys.exit(1)
        ingest_directory(args.dir)


if __name__ == "__main__":
    main()