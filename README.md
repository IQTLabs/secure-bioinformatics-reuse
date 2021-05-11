# Installation notes

## Ubuntu

Installed Ubuntu 20.04 LTS.

## Emacs

    sudo snap install emacs --classic

## Conda

See: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html

    diff Miniconda3-latest-Linux-x86_64.sh.sha256sum.actual Miniconda3-latest-Linux-x86_64.sh.sha256sum.expected
    bash Miniconda3-latest-Linux-x86_64.sh
    conda config --set auto_activate_base false

## Docker

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

    curl -s https://get.nextflow.io | bash

## nf-core

    conda config --add channels defaults
    conda config --add channels bioconda
    conda config --add channels conda-forge

    conda create --name nf-core python=3.7 nf-core nextflow
    conda activate nf-core
    nf-core list --json

## DTrace

    sudo apt install systemtap-sdt-dev

## Sysdig

    sudo apt install sysdig

## Python

    sudo apt-get install python3-venv
    pip install -r requirements.txt

## AWS

    sudo apt install awscli
    aws configure

# Contributing to Bioconda

## Build and test a recipe locally

1. Create a Fork of our Recipes Repo

        git@github.com:IQTLabs/bioconda-recipes.git

1. Create Local “Clone”

        git clone git@github.com:IQTLabs/bioconda-recipes.git
        cd bioconda-recipes
        git remote add upstream https://github.com/bioconda/bioconda-recipes.git

1. Create a Branch

        # Make sure our master is up to date with Bioconda
        git checkout master
        git pull upstream master
        git push origin master

        # Create and checkout a new branch for our work
        git checkout -b ralatsdc/recipe-for-apc
        git push -u origin ralatsdc/recipe-for-apc

1. Make Some Edits

1. Testing Recipes Locally Using the Circle CI Client

    You can execute an almost exact copy of our Linux build pipeline
    by installing the CircleCI client locally and running it from the
    folder where your copy of bioconda-recipes resides:

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

    Note that a hash, preferrably sha256, is required to verify the
    integrity of the source package. Generate the hash using, for
    example:

        wget -O- https://github.com/ralatsdc/apc/archive/refs/tags/v0.1.2.tar.gz | shasum -a 256

## Build and test a recipe remotely

1. Push Changes
1. Create a Pull Request

    Once you have opened a PR, our build system will start testing
    your changes. The recipes you have added or modified will be
    linted and built. Unless you are very lucky, you will encounter
    some errors during the build you will have to fix. Repeat 2. Make
    Some Edits and 3. Push Changes as often as needed.

    Eventually, your build will “turn green”. If you are a member of
    Bioconda, you can now add the please review & merge label to
    submit your PR for review. Otherwise, just ask on Gitter or ping
    @bioconda/core.

    Once you changes have been approved, they will be “merged” into
    our main repository and the altered packages uploaded to our
    channel.

1. Delete your Branch
1. Install Your Package

# Testing notes

## conda

See: https://conda.io/projects/conda/en/latest/index.html
See: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

## strace

See: https://man7.org/linux/man-pages/man1/strace.1.html

## dtrace

See: http://dtrace.org/blogs/about/

## sysdig

See: https://github.com/draios/sysdig
