#!/usr/bin/env python3
import argparse
import sys
from benchmarks import sys_bench, llm_bench

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run both system and LLM benchmarks on specified host group')
    parser.add_argument('--host-group', choices=['all', 'arm', 'x86'], default='all',
                      help='Host group to benchmark (default: all)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    host_group = args.host_group

    print(f"Starting benchmarks for host group: {host_group}")

    # Create namespace object with host_group for compatibility
    benchmark_args = argparse.Namespace(host_group=host_group)

    try:
        # Run system benchmarks
        print("\nRunning system benchmarks...")
        sys_bench.main(benchmark_args)
        
        # Run LLM benchmarks
        print("\nRunning LLM benchmarks...")
        llm_bench.main(benchmark_args)
        
        print("\nAll benchmarks completed successfully")
    except Exception as e:
        print(f"Error running benchmarks: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
