## LLM inference for ARM-based CPU benchmarking

This library was initially written to benchmark a bunch of ARM-based cusom silicon offered by hyperscale cloud providers. However, this library can be used to benchmark any set of aarch64 or x86_64 servers.

![LLM inferencing for custom ARM-based silicon](/benchmark_visuals/llm_benchmark.png)

#### Experiment setup
This benchmark was run on target ARM-based and x86_64 chips running ubuntu 22.04.

To install the required python dependencies

    > pip install -r requirements.txt

#### Ansible inventory
'inventory.yaml' contains all the machines to be benchmarked. The inventory is devided in two 'Host Groups':
    -   arm
    -   x86
You can run these benchmarks on either of these two groups or both of the groups at once.

#### Running Ansible playbook
```console
ssh-add <your-pem-keyfile-name>

ansible-playbook playbook.yaml -i inventory.yaml
```

#### Visualzing the competetive benchmark
These experiments will run llama3.2:3b as the default model. However, it can be changed on 'config.py'.

For only ARM-based host, llama3.2:1b model can be used. While models like llama3.1:7b can be used for both sets of hosts.

To run the experiments on all(i.e. both arm & x86) hosts

```console

python3 benchmarking.py

```

To run the experiments on arm/x86 hosts, like, for ARM-based hosts:

```console

python3 benchmarking.py --host-group arm

```