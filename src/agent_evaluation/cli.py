"""
CLI for discovering and running evaluation samples.

Auto-discovers evaluation samples by scanning for experiment.yaml files
in the evaluations/offline directory. Users can list, select, and run
samples without remembering long command paths.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional

import yaml


# Root of the project (two levels up from this file)
ROOT_DIR = Path(__file__).resolve().parents[2]
SAMPLES_DIR = ROOT_DIR / "src" / "evaluations" / "offline"
EXCLUDE_DIRS = {"reports", "utils", "__pycache__"}


def discover_samples() -> List[Dict[str, str]]:
    """Discover all evaluation samples by finding experiment.yaml files."""
    samples = []
    for path in sorted(SAMPLES_DIR.iterdir()):
        if not path.is_dir() or path.name in EXCLUDE_DIRS:
            continue
        config_file = path / "experiment.yaml"
        if not config_file.exists():
            continue

        # Read metadata from experiment.yaml
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        app_name = config.get("app_name", path.name)
        experiment_name = config.get("experiment_name", path.name)
        version = config.get("version", "")
        pipeline_steps = config.get("pipeline", [])
        stages = [step.get("config_key", "unknown") for step in pipeline_steps]

        samples.append({
            "name": path.name,
            "app_name": app_name,
            "experiment_name": experiment_name,
            "version": version,
            "config_path": str(config_file.relative_to(ROOT_DIR)),
            "stages": stages,
        })
    return samples


def print_samples_table(samples: List[Dict[str, str]]) -> None:
    """Print a formatted table of available samples."""
    if not samples:
        print("No evaluation samples found.")
        return

    print()
    print("=" * 70)
    print("  Available Evaluation Samples")
    print("=" * 70)
    print(f"  {'#':<4} {'Sample Name':<40} {'Stages'}")
    print(f"  {'-'*3:<4} {'-'*38:<40} {'-'*20}")

    for i, sample in enumerate(samples, 1):
        stages_str = " → ".join(sample["stages"])
        print(f"  {i:<4} {sample['name']:<40} {stages_str}")

    print("=" * 70)
    print()


def run_sample(sample: Dict[str, str], extra_args: Optional[List[str]] = None) -> int:
    """Run a selected evaluation sample."""
    from src.agent_evaluation.agentic_ops.runner import run_pipeline, parse_args

    config_path = sample["config_path"]
    print(f"\n{'='*70}")
    print(f"  Running: {sample['name']}")
    print(f"  Config:  {config_path}")
    print(f"  Stages:  {' → '.join(sample['stages'])}")
    print(f"{'='*70}\n")

    # Build args for the runner
    argv = ["--config_file", config_path]
    if extra_args:
        argv.extend(extra_args)

    # Temporarily override sys.argv for parse_args
    original_argv = sys.argv
    sys.argv = ["runner"] + argv
    try:
        args = parse_args()
        run_pipeline(args.config_file, args)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    finally:
        sys.argv = original_argv


def interactive_select(samples: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Prompt the user to select a sample interactively."""
    print_samples_table(samples)
    while True:
        try:
            choice = input("  Select a sample to run (number or name, 'q' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if choice.lower() in ("q", "quit", "exit"):
            return None

        # Try as a number
        try:
            idx = int(choice)
            if 1 <= idx <= len(samples):
                return samples[idx - 1]
            print(f"  Invalid number. Choose between 1 and {len(samples)}.")
            continue
        except ValueError:
            pass

        # Try as a name (partial match)
        matches = [s for s in samples if choice.lower() in s["name"].lower()]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print(f"  Multiple matches: {', '.join(m['name'] for m in matches)}")
            print("  Please be more specific.")
        else:
            print(f"  No sample found matching '{choice}'.")


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the 'list' command."""
    samples = discover_samples()
    print_samples_table(samples)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Handle the 'run' command."""
    samples = discover_samples()
    if not samples:
        print("No evaluation samples found.")
        return 1

    # If a sample is specified, find and run it
    if args.name:
        target = args.name.lower()
        # Try exact match first
        match = next((s for s in samples if s["name"].lower() == target), None)
        # Then try partial match
        if not match:
            matches = [s for s in samples if target in s["name"].lower()]
            if len(matches) == 1:
                match = matches[0]
            elif len(matches) > 1:
                print(f"  Ambiguous name '{args.name}'. Matches:")
                for m in matches:
                    print(f"    - {m['name']}")
                return 1
        if not match:
            # Try by number
            try:
                idx = int(args.name)
                if 1 <= idx <= len(samples):
                    match = samples[idx - 1]
            except ValueError:
                pass

        if not match:
            print(f"  Sample '{args.name}' not found. Use 'list' to see available samples.")
            return 1

        extra = []
        if args.sample:
            extra.extend(["--sample", str(args.sample)])
        if args.index_fname:
            extra.extend(["--index_fname", args.index_fname])
        return run_sample(match, extra)

    # Interactive selection
    selected = interactive_select(samples)
    if selected is None:
        print("  No sample selected.")
        return 0

    extra = []
    if args.sample:
        extra.extend(["--sample", str(args.sample)])
    if args.index_fname:
        extra.extend(["--index_fname", args.index_fname])
    return run_sample(selected, extra)


def cmd_run_all(args: argparse.Namespace) -> int:
    """Handle the 'run-all' command."""
    samples = discover_samples()
    if not samples:
        print("No evaluation samples found.")
        return 1

    print(f"\n  Running all {len(samples)} evaluation samples...\n")
    results = []
    for sample in samples:
        exit_code = run_sample(sample)
        status = "PASS" if exit_code == 0 else "FAIL"
        results.append((sample["name"], status, exit_code))

    # Summary
    print(f"\n{'='*70}")
    print("  Run All Summary")
    print(f"{'='*70}")
    print(f"  {'Sample':<42} {'Status':<8}")
    print(f"  {'-'*40:<42} {'-'*6:<8}")
    for name, status, _ in results:
        marker = "✓" if status == "PASS" else "✗"
        print(f"  {name:<42} {marker} {status}")
    print(f"{'='*70}")

    passed = sum(1 for _, s, _ in results if s == "PASS")
    print(f"  {passed}/{len(results)} passed\n")
    return 0 if all(code == 0 for _, _, code in results) else 1


def cmd_info(args: argparse.Namespace) -> int:
    """Handle the 'info' command — show details about a sample."""
    samples = discover_samples()
    target = args.name.lower()

    match = next((s for s in samples if s["name"].lower() == target), None)
    if not match:
        matches = [s for s in samples if target in s["name"].lower()]
        if len(matches) == 1:
            match = matches[0]

    if not match:
        print(f"  Sample '{args.name}' not found.")
        return 1

    config_path = ROOT_DIR / match["config_path"]
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print(f"\n{'='*70}")
    print(f"  Sample: {match['name']}")
    print(f"{'='*70}")
    print(f"  App Name:        {match['app_name']}")
    print(f"  Experiment:      {match['experiment_name']}")
    print(f"  Version:         {match['version']}")
    print(f"  Config:          {match['config_path']}")
    print(f"  Pipeline Stages: {' → '.join(match['stages'])}")

    # Show evaluators if available
    eval_config = config.get("evaluation", {})
    evaluators = eval_config.get("evaluators", {})
    if evaluators:
        print(f"\n  Evaluators:")
        for key, factory in evaluators.items():
            print(f"    • {key}: {factory}")

    # Show dataset info
    input_path = eval_config.get("input_path", "")
    input_file = eval_config.get("input_file", "")
    if input_path and input_file:
        full_path = ROOT_DIR / input_path / input_file
        exists = "✓" if full_path.exists() else "✗ (missing)"
        print(f"\n  Dataset: {input_path}{input_file} {exists}")

    print(f"\n  Run command:")
    print(f"    python -m agent_evals run {match['name']}")
    print(f"{'='*70}\n")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="python -m agent_evals",
        description="Evaluation Framework CLI — discover and run evaluation samples.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # list command
    subparsers.add_parser("list", help="List all available evaluation samples")

    # run command
    run_parser = subparsers.add_parser("run", help="Run an evaluation sample")
    run_parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Sample name or number (interactive if omitted)",
    )
    run_parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Number of samples to test (0 = all)",
    )
    run_parser.add_argument(
        "--index_fname",
        type=str,
        default=None,
        help="Specific index for re-run",
    )

    # run-all command
    subparsers.add_parser("run-all", help="Run all evaluation samples sequentially")

    # info command
    info_parser = subparsers.add_parser("info", help="Show details about a sample")
    info_parser.add_argument("name", help="Sample name")

    args = parser.parse_args()

    if args.command is None:
        # No command given — show interactive menu
        samples = discover_samples()
        if not samples:
            print("No evaluation samples found.")
            sys.exit(1)
        selected = interactive_select(samples)
        if selected:
            sys.exit(run_sample(selected))
        sys.exit(0)

    handlers = {
        "list": cmd_list,
        "run": cmd_run,
        "run-all": cmd_run_all,
        "info": cmd_info,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
