#!/usr/bin/env python3
import paramiko
import yaml
import matplotlib.pyplot as plt
import numpy as np
from time import sleep
import os
import sys
import json
import hashlib
import argparse
from config import DEFAULT_MODEL, KEY_FILE, INVENTORY_FILE, NUM_OF_ITERATIONS, OUTPUT_DIR

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run LLM benchmarks on specified host group')
    parser.add_argument('--host-group', choices=['all', 'arm', 'x86'], default='arm',
                      help='Host group to benchmark (default: arm)')

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

def run_command(ssh, command, timeout=1800):
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

def run_llm_benchmark(ssh):
    print(f"\nStarting LLM benchmark with model: {DEFAULT_MODEL}")
    
    # Ensure model is pulled
    print("Pulling model...")
    run_command(ssh, f"ollama pull {DEFAULT_MODEL}")
    
    # Run benchmark
    result = run_command(ssh, 'python3 /opt/llm/inferencing_script.py')
    
    try:
        data = json.loads(result)
        # Calculate average tokens/second
        avg_tokens_per_second = np.mean([r['tokens_per_second'] for r in data])
        return avg_tokens_per_second
    except Exception as e:
        print(f"Error parsing benchmark results: {e}")
        return 0

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

def plot_results(results):
    """Create plot with improved styling"""
    plt.figure(figsize=(12, 8))  # Increased width for more hosts
    
    # Create bars with reduced width
    hosts = list(results.keys())
    values = list(results.values())
    bars = plt.bar(range(len(hosts)), values, width=0.4)  # Reduced bar width
    
    # Color each bar based on host name
    for i, (bar, host) in enumerate(zip(bars, hosts)):
        bar.set_color(generate_color(host))
    
    plt.title(f'LLM Inference Performance\n{DEFAULT_MODEL} Model', fontsize=14, pad=20)
    plt.ylabel('Tokens per Second')
    plt.xticks(range(len(hosts)), hosts, rotation=45, ha='right')
    
    # Add padding around the plot
    # Set x-axis limits to add horizontal padding
    plt.xlim(-0.8, len(hosts) - 0.2)
    
    # Set y-axis limits to add vertical padding
    max_value = max(values) if values else 0
    #plt.ylim(0, max_value * 1.2)  # Add 20% padding above the highest bar
    
    # Add more padding to the layout
    plt.tight_layout(pad=3.0)
    
    # Save with extra padding around the entire figure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(f'{OUTPUT_DIR}/llm_benchmark.png', bbox_inches='tight', dpi=300,
                pad_inches=0.5)
    plt.close()

def main(args=None):
    # Parse command line arguments if not provided
    if args is None:
        args = parse_arguments()
    
    # Check SSH key permissions
    check_key_permissions()
    
    # Load inventory
    try:
        with open(INVENTORY_FILE, 'r') as f:
            inventory = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading inventory: {e}")
        sys.exit(1)

    # Get hosts based on selected group
    hosts = get_hosts_from_inventory(inventory, args.host_group)
    if not hosts:
        print(f"Error: No hosts found for group '{args.host_group}'")
        sys.exit(1)

    results = {}

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
                key_filename= KEY_FILE,
                timeout=10
            )

            # Verify connection
            print("Testing connection...")
            output = run_command(ssh, "uname -a")
            if not output:
                print(f"Failed to connect to {host}, skipping...")
                continue
            print(f"Connected successfully: {output.strip()}")

            # Run LLM benchmark
            tokens_per_second = run_llm_benchmark(ssh)
            results[host] = tokens_per_second

        except Exception as e:
            print(f"Error connecting to {host}: {e}")
            continue
        finally:
            ssh.close()
            print(f"Closed connection to {host}")

    # Create visualization if we have results
    if results:
        plot_results(results)
        print(f"\nResults saved to {OUTPUT_DIR}/llm_benchmark.png")
        
        # Print numeric results
        print("\nDetailed Results:")
        for host, tokens in results.items():
            print(f"{host}: {tokens:.2f} tokens/second")
    else:
        print("\nNo results were collected, cannot generate visualization")

if __name__ == "__main__":
    main()
