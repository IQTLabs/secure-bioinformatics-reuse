from argparse import ArgumentParser
import json
import logging
import os
from pathlib import PurePath
import subprocess

from dask.distributed import Client, SSHCluster, as_completed

from DaskPool import DaskPool


KEY_DIR = "~/.ssh"
SHELL_CMD = "/usr/bin/bash"
SCRIPTS_DIR = "/home/ubuntu/secure-bioinformatics-reuse/src/bash"
RECIPES_DIR = "/home/ubuntu/bioconda-recipes"
CONTAINERS_DIR = "/home/ubuntu/containers"

root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
root.addHandler(ch)

logging.getLogger("asyncssh").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def list_repositories():
    """List repositories which have most lines of code in Python from
    the Bioinformatics download of 2020-11-11.
    """
    loc_path = (
        PurePath(os.path.realpath(__file__)).parents[2].joinpath("dat", "loc.json")
    )
    with open(loc_path, "r") as loc_fp:
        loc = json.load(loc_fp)
    repositories = []
    for d in loc:
        if list(d)[1] == "Python":
            repositories.append(d["git_url"])
    return repositories


def aura_scan(python_src, scan_home, options=""):
    """Run a script that uses Aura to scan a Python source, either a
    path or Git repository, and produce JSON output in the scan home
    directory. The Python path can be to an individual Python file, or
    to a directory containing Python files.

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

    OPTIONS
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory
    """
    try:
        completed_process = subprocess.run(
            [
                os.path.join(SCRIPTS_DIR, "aura-scan.sh"), options, python_src, scan_home,
            ],
            capture_output=True,
        )
    except Excetpion as e:
        logger.error(e)
    return completed_process


def list_recipes():
    """List recipes in git@github.com:IQTLabs/bioconda-recipes.git.
    """
    return sorted(os.listdir(os.path.join(RECIPES_DIR, "recipes")))


def strace_conda_install(package, options=""):
    """Run a script that uses strace to trace the installation of a
    package fron a channel using conda.

    A directory is created to contain all output files, and each uses
    a base name give by "strace-conda-install-${package}-${suffix}".

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

    OPTIONS
    -c    The conda channel containing the package, default: bioconda
    -s    The suffix of the base name for the output directory and
          files, default: ""
    -C    Clean conda environment
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory
    """
    try:
        completed_process = subprocess.run(
            [
                SHELL_CMD,
                "-i",
                os.path.join(SCRIPTS_DIR, "strace-conda-install.sh"),
                options,
                package,
            ],
            capture_output=True,
        )
    except Excetpion as e:
        logger.error(e)
    return completed_process


def list_dockerfiles():
    """List Dockerfiles in git@github.com:ralatsdc/containers.git.
    """
    dirpaths = []
    packages = []
    versions = []
    for dirpath, dirnames, filenames in os.walk(CONTAINERS_DIR):
        for filename in filenames:
            if filename == "Dockerfile":
                package = os.path.basename(os.path.dirname(dirpath))
                version = os.path.basename(dirpath)
                if package != "containers":
                    dirpaths.append(dirpath)
                    packages.append(package)
                    versions.append(version)
    return dirpaths, packages, versions


def strace_docker_build(package, version, options=""):
    """Runs a script that uses strace to trace the build of the docker
    file in the build directory with tag "package-version".

    A directory is created to contain all output files, and each uses
    a base name give by "strace-docker-build-${package}-%{version}${suffix}".

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

    OPTIONS
    -s    The suffix of the base name for the output directory and
          files, default: ""
    -C    Clean conda environment
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory
    """
    try:
        completed_process = subprocess.run(
            [
                os.path.join(SCRIPTS_DIR, "strace-docker-build.sh"),
                options,
                os.path.join(CONTAINERS_DIR, package, version),
                package,
                version,
            ],
            capture_output=True,
        )
    except Excetpion as e:
        logger.error(e)
    return completed_process


def list_pipelines():
    """List pipelines in the nf-core conda package.
    """
    completed_process = subprocess.run(
        [SHELL_CMD, "-i", os.path.join(SCRIPTS_DIR, "list-pipelines.sh"),],
        capture_output=True,
        text=True,
    )
    pipelines = completed_process.stdout.split("\n")
    pipelines.remove("")
    return pipelines


def strace_pipeline_run(pipeline, options):
    """Run a script that uses strace to trace the nextflow run of an
    nf-core pipeline.

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

    OPTIONS
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory
    """
    try:
        completed_process = subprocess.run(
            [
                SHELL_CMD,
                "-i",
                os.path.join(SCRIPTS_DIR, "strace-pipeline-run.sh"),
                options,
                pipeline,
            ],
            capture_output=True,
        )
    except Excetpion as e:
        logger.error(e)
    return completed_process


def test_distributed_strace():
    daskPool = DaskPool(instance_type="t3.large")
    daskPool.maintain_pool()
    daskPool.checkout_branch()
    cluster = SSHCluster(
        [i.ip_address for i in daskPool.instances],
        connect_options={
            "known_hosts": None,
            "client_keys": [os.path.join(KEY_DIR, "dask-01.pem")],
        },
        worker_options={"nthreads": 2},
        scheduler_options={"port": 0, "dashboard_address": ":8797"},
    )
    client = Client(cluster)
    return pool, cluster, client


def teardown_pool(pool):
    """Terminates all instances in the pool.
    """
    pool.terminate_pool()


def distribute_runs(run_case, max_runs=9, do_teardown_pool=False):
    """ Setup a DaskPool instance, select a function and corresponding
    function arguments list, run the functions on the corresponding
    Dask cluster, and terminate the pool, if requested.
    """
    # Setup a DaskPool instance
    pool, cluster, client = setup_pool()

    # Select a function and corresponding function arguments list
    if run_case == "aura_scan":
        run_function = aura_scan
        run_args_list = list_repositories() 

    elif run_case == "strace_conda_install":
        run_function = strace_conda_install
        run_args_list = list_recipes()

    elif run_case == "strace_docker_build":
        run_function = strace_docker_build
        run_args_list = list_dockerfiles()

    elif run_case == "strace_pipeline_run":
        run_function = strace_pipeline_run
        run_args_list = list_pipelines()

    # Submit the same number of functions to the cluster as the number
    # of pool instances
    n_futures = 0
    submitted_futures = []
    for run_args in run_args_list:
        submitted_futures.append(
            client.submit(run_function, *run_args, options="-RP")
        )
        n_futures += 1
        if n_futures == len(pool.instances):
            break

    # Submit another function to the cluster whenever a previously
    # submitted function completes
    as_completed_futures = as_completed(submitted_futures)
    for future in as_completed_futures:
        n_futures += 1
        if n_futures < max_runs:
            as_completed_futures.add(
                client.submit(run_function, *run_args_list[n_futures], options="-RP")
            )

    # Terminate the pool, if requested.
    if do_teardown_pool:
        teardown_pool(pool)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run functions on a cluster")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--aura-scan", action="store_true")
    group.add_argument("-c", "--strace-conda-install", action="store_true")
    group.add_argument("-d", "--strace-docker-build", action="store_true")
    group.add_argument("-p", "--strace-pipeline-run", action="store_true")
    args = parser.parse_args()
    if args.aura_scan:
        distribute_runs("aura_scan")
    if args.strace_conda_install:
        distribute_runs("strace_conda_install")
    if args.strace_docker_build:
        distribute_runs("strace_docker_build")
    if args.strace_pipeline_run:
        distribute_runs("strace_pipeline_run")
