# Project Background

The Secure Bioinformatics Reuse effort is a subproject of the Secure
Code Reuse Project focusing on, well, bioinformatics.

## Goal

The goal of the subproject is to assess security vulnerabilities in
open source bioinformatics software packages.

## Approach

Our approach is informed by the work of Duan, R. et al. "Towards
Measuring Supply Chain Attacks on Package Managers for Interpreted
Languages". arXiv:2002.01139 [cs] (2020) which involved analysis of
metadata, Abstract Syntax Trees (ASTs), dataflow, and dynamic
execution of JavaScript, Python, and Ruby from their respective
package managers.

In this subproject we
- Implement a simple metadata search of Bioconda recipes or
  BioContainers Dockerfiles
- Trace Bioconda package installs and BioContainers Dockerfile builds
- Trace execution of nf-core Nextflow pipelines
- Scan recent bioinformatics Python repositories using Aura, a Python
  tool developed by Martin Čarnogurský to analyze the AST of Python
  code

Bioconda is a channel for the conda package manager specializing in
bioinformatics software. Each package added to Bioconda also has a
corresponding Docker BioContainer automatically created and uploaded
to Quay.io. nf-core is a community effort to collect a curated set of
analysis pipelines built using Nextflow, software which enables
scalable and reproducible scientific workflows using software
containers.

## Objectives

We seek to answer the following questions:
- What Bioconda and BioContainer metadata exists? Is the data useful?
  If so, how can the data be used, and what does the data show?
- Can useful dynamic analysis be performed during conda installs and
  docker builds? If so, how can this dynamic analysis be done, and
  what does the analysis show?
- Can useful dynamic analysis be performed during nextflow pipeline
  runs? If so, how can this dynamic analysis be done, and what does
  the analysis show?
- What security vulnerabilities does Aura identify in recent
  bioinformatics repositories? Do the characterizes of vulnerabilities
  in bioinformatics Python packages differ from Python packages in
  general?

# Development Environment

The code in this repository requires Conda, Docker, Nextflow, nf-core,
Python (and associated requirements), and the AWS command line
interface (for configuration). Dask, an open source library for
parallel computing written in Python, is used to distribute processing
over a cluster. As a result, after creating an instance with all
requirements installed, an Amazon Machine Image is created and used
for launching images on the cluster. The following sections describe
installation details.

## Ubuntu

All images are based on Ubuntu 20.04 LTS.

## Conda

Conda is an open source package management system and environment
management system that runs on Windows, macOS and Linux.

See: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html

    diff Miniconda3-latest-Linux-x86_64.sh.sha256sum.actual Miniconda3-latest-Linux-x86_64.sh.sha256sum.expected
    bash Miniconda3-latest-Linux-x86_64.sh
    conda config --set auto_activate_base false

## Docker

Docker is a set of platform as a service (PaaS) products that use
OS-level virtualization to deliver software in packages called
containers.

See: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html, and
https://docs.docker.com/engine/install/linux-postinstall/

    sudo apt-get update
    sudo apt-get install \
         apt-transport-https \
         ca-certificates \
         curl \
         gnupg \
         lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io
    sudo docker run hello-world
    sudo groupadd docker
    sudo usermod -aG docker $USER
    newgrp docker 
    docker run hello-world
    sudo systemctl enable docker.service
    sudo systemctl enable containerd.service

## Nextflow

Nextflow is a reactive workflow framework and a programming DSL that
eases the writing of data-intensive computational pipelines.

See: https://www.nextflow.io/

    curl -s https://get.nextflow.io | bash

## nf-core

nf-core is a community effort to collect a curated set of analysis pipelines
built using Nextflow.

See: https://nf-co.re/

    conda config --add channels defaults
    conda config --add channels bioconda
    conda config --add channels conda-forge
    conda create --name nf-core python=3.7 nf-core nextflow

    conda activate nf-core
    nf-core list --json

## Python

Python is an interpreted high-level general-purpose programming
language.

See: https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment-on-an-ubuntu-20-04-server

    sudo apt-get install python3-venv
    pip install -r requirements.txt

## Greynoise

GreyNoise tells security analysts what not to worry about. They
collect, analyze and label data on IPs that saturate security tools
with noise. This unique perspective helps analysts confidently ignore
irrelevant or harmless activity, creating more time to uncover and
investigate true threats.

See: https://www.greynoise.io/,
https://developer.greynoise.io/reference/community-api, and
https://developer.greynoise.io/docs/libraries-sample-code

    greynoise setup -k UserAPIKey

## AWS

Amazon Web Services (AWS) is a subsidiary of Amazon providing
on-demand cloud computing platforms and APIs to individuals,
companies, and governments, on a metered pay-as-you-go basis. The AWS
Command Line Interface (CLI) is a unified tool to manage your AWS
services.

See: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html

    sudo apt install awscli
    aws configure

## Extra packages

### DTrace

An alternative to strace. Not currently used.

See: http://manpages.ubuntu.com/manpages/focal/man1/dtrace.1.html

    sudo apt install systemtap-sdt-dev

### Sysdig

An alternative to strace that produces JSON output. Not currently
used.

See: https://github.com/draios/sysdig/wiki/How-to-Install-Sysdig-for-Linux

    sudo apt install sysdig

### Emacs

The one true editor. For the old school, or old school at heart.

See: https://www.gnu.org/software/emacs/

    sudo snap install emacs --classic

# Running the scripts

The simple tools in this repository are written in bash and
distributed using Python. This section contains a summary of usage.

## aura-scan.sh

Use Aura to scan a Python path or Git repository.

### SYNOPSIS

    aura-scan [-R] [-H target-host] [-P] python-src scan-home

### DESCRIPTION

Uses Aura to scan a Python source, either a path or Git repository,
and produce JSON output in the scan home directory. The Python path
can be to an individual Python file, or to a directory containing
Python files.

Optionally recursively copy the output directory to the target host,
or purge the output directory.

### OPTIONS 

    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

## strace-conda-install.sh

Trace a conda install of a package.

### SYNOPSIS

    strace-conda-install [-c channel] [-s suffix] [-C] [-R] [-H target-host] [-P] package

### DESCRIPTION

Uses strace to trace the installation of a package fron a channel
using conda.

A directory is created to contain all output files, and each uses a
base name give by "strace-conda-install--".

Optionally recursively copy the output directory to the target host,
or purge the output directory.

### OPTIONS 

    -c    The conda channel containing the package, default: bioconda
    -s    The suffix of the base name for the output directory and
          files, default: ""
    -C    Clean conda environment
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

## strace-docker-build.sh

Trace a docker build.

### SYNOPSIS

    strace-docker-build [-s suffix] [-C] [-R] [-H target-host] [-P] build-directory package version

### DESCRIPTION

Uses strace to trace the build of the docker file in the build
directory with tag "ralatsdio/:".

A directory is created to contain all output files, and each uses a
base name give by "strace-docker-build--%{version}".

Optionally recursively copy the output directory to the target host,
or purge the output directory.

### OPTIONS 

    -s    The suffix of the base name for the output directory and
          files, default: ""
    -C    Clean up new Docker images
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

## strace-pipeline-run.sh

Trace run of nf-core pipeline.

### SYNOPSIS

    strace-pipeline-run [-R] [-H target-host] [-P] pipeline

### DESCRIPTION

Uses strace to trace the nextflow run of an nf-core pipeline.

Optionally recursively copy the output directory to the target host,
or purge the output directory.

### OPTIONS 

    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

## distribute.py

Run functions on a cluster.

### SYNOPSIS

    distribute.py [-h] [-C TARGET_COUNT] [-T INSTANCE_TYPE] [-s] [-t] [-R MAX_RUNS] [-F] [-a | -c | -d | -p]

### DESCRIPTION

Run bash scripts as a subprocess functions on a Dask cluster.

### OPTIONS 

    -h, --help            show this help message and exit
    -C TARGET_COUNT, --target-count TARGET_COUNT
                          target count of machines in cluster
    -T INSTANCE_TYPE, --instance-type INSTANCE_TYPE
                          instance type for machines in cluster
    -s, --start-pool      start instances in cluster
    -t, --terminate-pool  terminate instances in cluster
    -R MAX_RUNS, --max-runs MAX_RUNS
                          maximum number of runs
    -F, --run-function    run function locally for testing
    -a, --aura-scan       run Aura scans
    -c, --strace-conda-install
                          trace conda installs
    -d, --strace-docker-build
                          trace docker builds
    -p, --strace-pipeline-run
                          trace pipeline runs

# Contributing to Bioconda

Directions for contributing to Bioconda are collected here so that
simple exploits can be attempted.

## Build and test a recipe locally

1. Create a Fork of the IQT Labs Bioconda recipes repository

        git@github.com:IQTLabs/bioconda-recipes.git

1. Create a local “clone”

        git clone git@github.com:IQTLabs/bioconda-recipes.git
        cd bioconda-recipes
        git remote add upstream https://github.com/bioconda/bioconda-recipes.git

1. Create a branch

        # Make sure our master is up to date with Bioconda
        git checkout master
        git pull upstream master
        git push origin master

        # Create and checkout a new branch for our work
        git checkout -b ralatsdc/recipe-for-apc
        git push -u origin ralatsdc/recipe-for-apc

1. Make some edits

1. Test recipes locally using the Circle CI client

    You can execute an almost exact copy of the Bioconda Linux build
    pipeline by installing the CircleCI client locally and running it
    from the folder where your copy of bioconda-recipes resides:

        # Ensure the build container is up-to-date
        docker pull quay.io/bioconda/bioconda-utils-build-env:latest

        # Run the build locally
        circleci build

    You can use Docker volume bind-mounts to capture the local package
    channel with the newly built packages:

        mkdir -p conda-bld
        rm -rf conda-bld/*
        circleci build --volume $PWD/conda-bld:/opt/conda/conda-bld

    After a successful build, you can then install from the local
    channel by providing the path to it:

        conda install -c file://$PWD/conda-bld your-package

    For the apc package, for example, after modifying any of the files
    in recipes/apc, run these commands:

        conda activate apc
        cd ~/bioconda_recipes
        mkdir -p conda-bld

        conda remove apc
        conda clean --all
        sudo rm -rf conda-bld/*
        circleci build --volume $PWD/conda-bld:/opt/conda/conda-bld
        conda install -c file://$PWD/conda-bld apc

    Note that a hash, preferably sha256, is required to verify the
    integrity of the source package. Generate the hash using, for
    example:

        wget -O- https://github.com/ralatsdc/apc/archive/refs/tags/v0.1.2.tar.gz | shasum -a 256

## Build and test a recipe remotely

1. Push changes

1. Create a pull request

    Once you have opened a PR, the Bioconda build system will start
    testing your changes. The recipes you have added or modified will
    be linted and built. Unless you are very lucky, you will encounter
    some errors during the build you will have to fix. Repeat 2. Make
    Some Edits and 3. Push Changes as often as needed.

    Eventually, your build will “turn green”. If you are a member of
    Bioconda, you can now add the please review & merge label to
    submit your PR for review. Otherwise, just ask on Gitter or ping
    @bioconda/core.

    Once you changes have been approved, they will be “merged” into
    the Bioconda main repository and the altered packages uploaded to
    our channel.

1. Delete your branch

1. Install your package

# Tool Documentation

## conda

See: https://conda.io/projects/conda/en/latest/index.html
See: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

## strace

See: https://man7.org/linux/man-pages/man1/strace.1.html

## dtrace

See: http://dtrace.org/blogs/about/

## sysdig

See: https://github.com/draios/sysdig
