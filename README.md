# CDBench

CDBench is a benchmark for the coding skills of Large Language Models (LLMs) with a focus on software testing.

## Reproducing the benchmark

In the following we describe the steps to reproduce our results. Everything we describe works as is on Ubuntu 24.04 LTS. 

### Setting up the environment

First, checkout the repository from GitHub:

```bash
git clone git@github.com:aieng-lab/cd-bench.git
cd cd-bench
```

We recommend using a virtual environment to run the benchmark. To create a virtual environment, run the following command:

```bash
python3 -m venv .venv
```

We can now activate the virtual environment and install the required packages:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Installation of CodeDefenders

For reproduction of the results, it is necessary to have CodeDefenders deployed locally, please follow the respective installation routine on https://github.com/CodeDefenders/CodeDefenders

### Installation of Postgres

To store the experiments data, an instance of Postgres is used. The expected setup is presented in `postgres/docker-compose.yaml`

### Experimental classes

The source code for the classes that are used in the benchmark are provided in `classes/`.

### Creating setups

Before running experiments, setups should be created. This can be done by running the `experiments/create_setups.ipynb` notebook. Keep in mind that the names of class aliases should exactly match those of imported in CodeDefenders. LLMs label names should be actualized from their respective vendors as they are subject to change. 

### Running experiments

The following config files with respective keys are expected to exist at that point: `experiments/config/llm_api_keys.json`, `experiments/config/codedefenders_users.json`, and `experiments/config/postgres_user.json`. For the files structure refer to the respective example files placed in the folder.

The experiments can be conducted by running `experiments/experiments.ipynb`.

### Processing results

The experiments' logs can be extracted via `metrics/turns extraction.ipynb` and metrics computations are done for mutants and diagnostics with `metrics/mutants metrics.ipynb` and `metrics/diagnostic metrics.ipynb` respectively.

The results of our run can be found in `metrics/data`.

### Visualizations

The visualizations can be reproduced by running `metrics/visualizations.ipynb`.

### Manual Analysis

The notebooks used for the manual annotations and analysis can be found in the `manual_analysis/` folder.