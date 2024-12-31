#!/usr/bin/env python3
import paramiko
import yaml
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
import os
import sys
import hashlib
import argparse
from config import OUTPUT_DIR, INVENTORY_FILE, KEY_FILE

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run system benchmarks on specified host group')
    parser.add_argument('--host-group', choices=['all', 'arm', 'x86'], default='all',
                      help='Host group to benchmark (default: all)')
    return parser.parse_args()

def generate_color(name):
    """Generate a color based on the hash of the hostname"""
    hash_object = hashlib.md5(name.encode())
    hash_hex = hash_object.hexdigest()
    # Use the first 6 characters of the hash for RGB values
    r = int(hash_hex[:2], 16) / 255.0
    g = int(hash_hex[2:4], 16) / 255.0
    b = int(hash_hex[4:6], 16) / 255.0
    return (r, g, b)

def check_key_permissions():
    key_file = KEY_FILE
    try:
        current_perms = oct(os.stat(key_file).st_mode)[-3:]
        if current_perms != '600':
            print(f"Fixing permissions for {key_file}")
            os.chmod(key_file, 0o600)
    except Exception as e:
        print(f"Error checking/setting key permissions: {e}")
        sys.exit(1)

def run_command(ssh, command, timeout=30):
    print(f"Executing command: {command}")
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        stdout_str = stdout.read().decode('utf-8')
        stderr_str = stderr.read().decode('utf-8')
        
        if stderr_str:
            print(f"Command stderr: {stderr_str}")
        
        return stdout_str
    except Exception as e:
        print(f"Error executing command: {e}")
        return ""

def run_benchmark(ssh, test_type, test_params):
    print(f"\nStarting {test_type} benchmark...")
    
    # Cleanup any previous test data
    #run_command(ssh, "sysbench --cleanup")
    
    # Prepare test if needed
    if test_type == "fileio":
        print("Preparing fileio test...")
        run_command(ssh, f"sysbench {test_type} {test_params} prepare")
    
    # Run the actual test
    print(f"Running {test_type} test with params: {test_params}")
    result = run_command(ssh, f"sysbench {test_type} {test_params} run")
    
    # Cleanup after test
    if test_type == "fileio":
        print("Cleaning up fileio test...")
        run_command(ssh, f"sysbench {test_type} {test_params} cleanup")
    
    return result

def parse_results(output, test_type):
    if not output:
        print(f"No output to parse for {test_type} test")
        return 0
        
    print(f"\nParsing results for {test_type}:")
    print(output)
    
    try:
        if test_type == "cpu":
            for line in output.split('\n'):
                if "events per second" in line:
                    return float(line.split(':')[1].strip())
        elif test_type == "memory":
            for line in output.split('\n'):
                if "MiB/sec" in line:
                    return float(line.split('(')[1].split()[0])
        elif test_type == "fileio":
            for line in output.split('\n'):
                if "read, MiB/s:" in line:
                    return float(line.split(':')[1].strip())
    except Exception as e:
        print(f"Error parsing results: {e}")
    return 0

def plot_test_results(test_type, results, hosts):
    """Create a separate plot for each test type with more padding"""
    plt.figure(figsize=(12, 8))  # Increased width for more hosts
    
    # Create bars with reduced width
    values = list(results.values())
    bars = plt.bar(range(len(hosts)), values, width=0.4)  # Reduced bar width
    
    # Color each bar based on host name
    for i, (bar, host) in enumerate(zip(bars, hosts)):
        bar.set_color(generate_color(host))
    
    titles = {
        'cpu': 'CPU Performance (events/sec)',
        'memory': 'Memory Performance (MiB/sec)',
        'fileio': 'File I/O Performance (MiB/sec)'
    }
    
    plt.title(titles[test_type], pad=20)  # Added padding to title
    plt.xticks(range(len(hosts)), hosts, rotation=45, ha='right')  # Rotated labels for better readability
    
    # Add padding around the plot
    ax = plt.gca()
    # Set x-axis limits to add horizontal padding
    plt.xlim(-0.8, len(hosts) - 0.2)
    
    # Set y-axis limits to add vertical padding
    max_value = max(values) if values else 0
    plt.ylim(0, max_value * 1.2)  # Add 20% padding above the highest bar
    
    # Add more padding to the layout
    plt.tight_layout(pad=3.0)
    
    # Save with extra padding around the entire figure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(f'{OUTPUT_DIR}/sys_benchmark_{test_type}.png', bbox_inches='tight', dpi=300, 
                pad_inches=0.5)  # Added padding around the saved figure
    plt.close()

def get_hosts_from_inventory(inventory, host_group):
    """Get all hosts from specified group(s) in inventory"""
    hosts = {}
    if host_group == 'all':
        # Combine hosts from all groups
        for group in inventory:
            hosts.update(inventory[group]['hosts'])
    else:
        # Get hosts from specific group
        hosts = inventory[host_group]['hosts']
    return hosts

def main(args=None):
    # Parse command line arguments if not provided
    if args is None:
        args = parse_arguments()
    host_group = args.host_group
    
    # Check SSH key permissions
    check_key_permissions()
    
    # Load inventory
    try:
        with open( INVENTORY_FILE, 'r') as f:
            inventory = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading inventory: {e}")
        sys.exit(1)

    # Get hosts based on selected group
    hosts = get_hosts_from_inventory(inventory, host_group)
    if not hosts:
        print(f"Error: No hosts found for group '{host_group}'")
        sys.exit(1)

    # Test configurations
    tests = {
        'cpu': '--test=cpu --cpu-max-prime=20000',
        'memory': '--test=memory --memory-block-size=1M --memory-total-size=10G',
        'fileio': '--test=fileio --file-test-mode=seqrd --file-total-size=2G'
    }

    results = {
        'cpu': {},
        'memory': {},
        'fileio': {}
    }

    # Connect to each host and run benchmarks
    for host, config in hosts.items():
        print(f"\nTesting {host}...")
        print(f"Connecting to {config['ansible_host']} as {config['ansible_user']}")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                config['ansible_host'],
                username=config['ansible_user'],
                key_filename='arm64',
                timeout=10
            )

            # Verify connection with simple command
            print("Testing connection...")
            output = run_command(ssh, "uname -a")
            if not output:
                print(f"Failed to connect to {host}, skipping...")
                continue
            print(f"Connected successfully: {output.strip()}")

            # Run each test
            for test_type, test_params in tests.items():
                print(f"\nRunning {test_type} test on {host}...")
                output = run_benchmark(ssh, test_type, test_params)
                results[test_type][host] = parse_results(output, test_type)
                sleep(2)  # Small delay between tests

        except Exception as e:
            print(f"Error connecting to {host}: {e}")
            continue
        finally:
            ssh.close()
            print(f"Closed connection to {host}")

    # Create separate graphs for each test if we have results
    if any(results.values()):
        host_list = list(hosts.keys())
        for test_type in tests:
            plot_test_results(test_type, results[test_type], host_list)
        print(f"\nResults saved to {OUTPUT_DIR}/benchmark_cpu.png, "
              f"{OUTPUT_DIR}/benchmark_memory.png, and {OUTPUT_DIR}/benchmark_fileio.png")
    else:
        print("\nNo results were collected, cannot generate graphs")

if __name__ == "__main__":
    main()
