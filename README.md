# Experiments API

Training a deep neural network requires finding a good combination of model hyperparameters. The process of finding good values for each is called hyperparameter optimization. The number of jobs required for each such experiment typically ranges from the low ones into the hundreds.

Individual workflows for optimization vary, but this is typically an ad-hoc manual process including custom job submit scripts or even pen and paper.

This project provides an API to support machine learning experiments on Kubernetes. This is done by moving the experiment context into a shared API and standardizing experiment job metadata. This promotes sharing results and tool development. Decoupling parameter space search from job execution further promotes re-use. This project eases job integration with the experiment tracking system by providing a python client library.

[![overview figure](docs/images/overview.png)](https://docs.google.com/drawings/d/1CGDVt9finf_QC_H6lAIW9StmYiNOCLoemAmpNRN47tg/edit)

## Prerequisites

 - git
 - make
 - python (v3 is the only tested variant at the moment)
 - kubectl and a connected cluster (minikube or a full cluster)

## Installation

To install the most recent release, run the following:
```
$ pip install experiments
```

## Development

To check out and install the latest development release, run:
```
$ git clone https://github.com/IntelAI/experiments.git
$ cd experiments
$ pip install .
```
To test the Experiments API, run the following:
```
$ pip install -r requirements-dev.txt
$ make test
``` 

## Appendix

### Concepts

**Experiment** Describes a hyperparameter space and how to launch a job for a sample in that space. Has a unique name.

**Optimizer** A program that reads an experiment and creates jobs with different hyperparameter settings. This can be done all in one shot, or the optimizer could be a long-running coordinator that monitors the performance of various samples to direct the hyperparameter optimization process. This program is supplied by the user.

**Result** Encodes metadata about a single job run for an experiment. For example, a handful of high level metrics per training epoch and a pointer to an output directory on shared storage. There is one result resource per job. Each result has the same name as the job it represents.
