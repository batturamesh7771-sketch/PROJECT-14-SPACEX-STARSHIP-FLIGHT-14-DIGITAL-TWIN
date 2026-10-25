"""
Command-Line Interface (CLI) for Phase 11: End-to-End Mission Verification & Uncertainty Quantification.
Starship Flight 14 Digital Engineering Lab.

Supported commands:
  python -m src.phase11 uq [--samples 200] [--seed 42]
  python -m src.phase11 verify
  python -m src.phase11 all
"""

import os
import sys
import argparse
import json
import unittest

from src.verification.uq_engine import execute_uq_pipeline, validate_uq_config


def cmd_uq(args) -> int:
    """Executes Monte Carlo uncertainty quantification, sensitivity screening, and convergence analysis."""
    print(f"[Phase 11] Executing Uncertainty Quantification pipeline ({args.samples} samples, seed: {args.seed})...")
    try:
        execute_uq_pipeline(sample_count=args.samples, seed=args.seed)
        print("[Phase 11] UQ analysis completed successfully.")
        return 0
    except Exception as e:
        print(f"[Phase 11 ERROR] UQ execution failed: {e}", file=sys.stderr)
        return 1


def cmd_verify(args) -> int:
    """Runs automated Phase 11 verification checks."""
    print("[Phase 11] Running automated verification checks...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_phase11_verification")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


def cmd_all(args) -> int:
    """Executes UQ analysis, generates reports, and runs verification checks."""
    ret_uq = cmd_uq(args)
    if ret_uq != 0:
        return ret_uq
    return cmd_verify(args)


def main():
    parser = argparse.ArgumentParser(description="Phase 11: End-to-End Mission Verification & UQ CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # UQ
    p_uq = subparsers.add_parser("uq", help="Run Monte Carlo UQ and sensitivity analysis")
    p_uq.add_argument("--samples", type=int, default=200, help="Number of Monte Carlo samples (default: 200)")
    p_uq.add_argument("--seed", type=int, default=42, help="Random number generator seed (default: 42)")

    # Verify
    p_verify = subparsers.add_parser("verify", help="Run Phase 11 verification test suite")

    # All
    p_all = subparsers.add_parser("all", help="Execute complete Phase 11 pipeline and tests")
    p_all.add_argument("--samples", type=int, default=200, help="Number of Monte Carlo samples (default: 200)")
    p_all.add_argument("--seed", type=int, default=42, help="Random number generator seed (default: 42)")

    args = parser.parse_args()
    if args.command == "uq":
        sys.exit(cmd_uq(args))
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "all":
        sys.exit(cmd_all(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
