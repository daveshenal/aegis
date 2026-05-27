"""
Batch evaluation runner.
Runs a set of test queries through the full research pipeline,
logs every run to MLflow, and prints a summary table at the end.

Usage:
    python scripts/run_eval_batch.py
    python scripts/run_eval_batch.py --queries-file ./eval_queries.json
    python scripts/run_eval_batch.py --max-revisions 2
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.research_service import run_research
from app.observability.logging import setup_logging, get_logger

setup_logging()
log = get_logger("run_eval_batch")

# Default test queries — replace or extend with your domain
DEFAULT_QUERIES = [
    "What are the key architectural differences between GPT-4 and Gemini?",
    "How does retrieval-augmented generation improve factual accuracy in LLMs?",
    "What are the main challenges in deploying reinforcement learning agents in production?",
    "How do vision-language models achieve cross-modal alignment?",
    "What evaluation metrics are used to assess RAG system quality?",
]


def run_batch(queries: list[str], max_revisions: int) -> list[dict]:
    results = []

    for i, query in enumerate(queries, 1):
        log.info(f"[{i}/{len(queries)}] Running: {query[:80]}")
        start = time.time()

        try:
            result = run_research(query=query)
            wall_latency = round(time.time() - start, 2)

            results.append({
                "query": query,
                "overall_score": result["overall_score"],
                "passed": result["passed_evaluation"],
                "revision_count": result["revision_count"],
                "wall_latency_s": wall_latency,
                "sources_used": len(result["sources_used"]),
                "dimension_scores": {
                    d["dimension"]: d["score"]
                    for d in result["dimension_scores"]
                },
                "error": None,
            })

            log.info(
                f"  Score: {result['overall_score']}/5.0 | "
                f"Passed: {result['passed_evaluation']} | "
                f"Revisions: {result['revision_count']} | "
                f"Latency: {wall_latency}s"
            )

        except Exception as e:
            wall_latency = round(time.time() - start, 2)
            log.error(f"  Failed: {e}")
            results.append({
                "query": query,
                "overall_score": 0.0,
                "passed": False,
                "revision_count": 0,
                "wall_latency_s": wall_latency,
                "sources_used": 0,
                "dimension_scores": {},
                "error": str(e),
            })

    return results


def print_summary(results: list[dict]) -> None:
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    avg_score = round(sum(r["overall_score"] for r in results) / total, 2)
    avg_latency = round(sum(r["wall_latency_s"] for r in results) / total, 2)
    avg_revisions = round(sum(r["revision_count"] for r in results) / total, 2)

    print("\n" + "=" * 72)
    print(f"  EVAL BATCH SUMMARY — {total} queries")
    print("=" * 72)
    print(f"  Pass rate:        {passed}/{total} ({round(passed/total*100)}%)")
    print(f"  Avg score:        {avg_score}/5.0")
    print(f"  Avg latency:      {avg_latency}s")
    print(f"  Avg revisions:    {avg_revisions}")
    print("=" * 72)

    # Per-dimension averages
    all_dimensions: dict[str, list[float]] = {}
    for r in results:
        for dim, score in r["dimension_scores"].items():
            all_dimensions.setdefault(dim, []).append(score)

    if all_dimensions:
        print("\n  Dimension averages:")
        for dim, scores in sorted(all_dimensions.items()):
            avg = round(sum(scores) / len(scores), 2)
            bar = "█" * int(avg) + "░" * (5 - int(avg))
            print(f"    {dim:<16} {bar}  {avg}/5.0")

    print()

    # Per-query results
    print("  Per-query results:")
    print(f"  {'#':<4} {'Score':<8} {'Pass':<6} {'Rev':<5} {'Latency':<10} Query")
    print("  " + "-" * 68)
    for i, r in enumerate(results, 1):
        status = "✓" if r["passed"] else "✗"
        error = " [ERROR]" if r["error"] else ""
        print(
            f"  {i:<4} {r['overall_score']:<8} {status:<6} "
            f"{r['revision_count']:<5} {r['wall_latency_s']:<10} "
            f"{r['query'][:45]}...{error}"
        )
    print()


def save_results(results: list[dict], output_path: str) -> None:
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"Results saved to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a batch of queries through the research pipeline."
    )
    parser.add_argument(
        "--queries-file",
        type=str,
        default=None,
        help="Path to a JSON file containing a list of query strings.",
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=3,
        help="Maximum revision loops per query (default: 3).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval_results.json",
        help="Path to save results JSON (default: eval_results.json).",
    )

    args = parser.parse_args()

    if args.queries_file:
        if not os.path.isfile(args.queries_file):
            log.error(f"Queries file not found: {args.queries_file}")
            sys.exit(1)
        with open(args.queries_file) as f:
            queries = json.load(f)
        if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
            log.error("Queries file must contain a JSON array of strings.")
            sys.exit(1)
    else:
        queries = DEFAULT_QUERIES

    log.info(f"Starting eval batch: {len(queries)} queries, max_revisions={args.max_revisions}")

    results = run_batch(queries=queries, max_revisions=args.max_revisions)

    print_summary(results)
    save_results(results, args.output)


if __name__ == "__main__":
    main()