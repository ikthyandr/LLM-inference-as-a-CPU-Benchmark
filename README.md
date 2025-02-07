## LLM inference for ARM-based CPU benchmarking

Initially, I started writing this library to benchmark some Arm-based custom silicon offered by AWS, GCP & Azure. However, this library can be used to benchmark any set of aarch64 or x86_64 servers.

![LLM inferencing for custom ARM-based silicon](/benchmark_visuals/llm_benchmark.png)

The details of this experiment can be found on [my blog post](https://aarch64.cloud/arm-chip-benchmark-test-for-hyperscale-cloud-providers.html).


#### System reqirements
The benchmark test was run on servers running on ubuntu 22.04. The minimum recommended memory to run LLM inference tests are:\
    - 4GB RAM for 1 billion parameter models\
    - 6GB RAM for 3 billion parameter models\
    - 12GB RAM for 7 billion parameter models\
\
The following tests were run on 16GB RAM, irrespective of the model' size.

#### Experiment setup
This benchmark was run on target ARM-based and x86_64 chips running ubuntu 22.04.

To install the required python dependencies

    > pip install -r requirements.txt

#### Ansible inventory
'inventory.yaml' contains all the machines to be benchmarked. The inventory is devided in two 'Host Groups':\
    -   arm\
    -   x86\
You can run these benchmarks on either of these two groups or both of the groups at once.

#### Running Ansible playbook
```console
ssh-add <your-pem-keyfile-name>

ansible-playbook playbook.yaml -i inventory.yaml
```

#### Visualizing  the competitive benchmark
These experiments will run llama3.2:3b as the default model. The default model can be changed on 'config.py'. llama3.2:1b model can be used for only ARM-based host. However, models like llama3.1:7b can be used for both sets of hosts.

To run the experiments on all(i.e. both arm & x86) hosts

```console

python3 benchmarking.py

```

To run the experiments on arm/x86 hosts, like, for ARM-based hosts:

```console

python3 benchmarking.py --host-group arm

```