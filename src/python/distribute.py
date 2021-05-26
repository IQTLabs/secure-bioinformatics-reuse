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
    completed_process = subprocess.run(
        [
            os.path.join(SCRIPTS_DIR, "aura-scan.sh"), options, python_src, scan_home,
        ],
        capture_output=True,
    )
    return completed_process


def list_recipes():
    return sorted(os.listdir(os.path.join(RECIPES_DIR, "recipes")))


def strace_conda_install(package, options=""):
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
    return completed_process


def list_dockerfiles():
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
    return completed_process


def list_pipelines():
    completed_process = subprocess.run(
        [SHELL_CMD, "-i", os.path.join(SCRIPTS_DIR, "list-pipelines.sh"),],
        capture_output=True,
        text=True,
    )
    pipelines = completed_process.stdout.split("\n")
    pipelines.remove("")
    return pipelines


def strace_pipeline_run(pipeline, options):
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
    a = client.submit(aura_scan, "git@github.com:Public-Health-Bioinformatics/kipper.git", "scan", options="-RP")
    print(a.result())
    b = client.submit(strace_conda_install, "velvet", options="-RP")
    print(b.result())
    c = client.submit(strace_docker_build, "spectra-cluster-cli", "v1.1.2", options="-RP")
    print(c.result())
    """
    d = client.submit(strace_pipeline_run, "rnaseq", options="-RP")
    print(d.result())
    """


def test_as_completed():
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

    recipes = list_recipes()

    futures = []
    for n_futures in range(len(daskPool.instances)):
        futures.append(
            client.submit(strace_conda_install, recipes[n_futures], options="-RP")
        )

    seq = as_completed(futures)
    for future in seq:
        n_futures += 1
        seq.add(
            client.submit(strace_conda_install, recipes[n_futures], options="-RP")
        )
        if n_futures == 6:
            break


if __name__ == "__main__":

    """
    repositories = list_repositories()
    print(repositories)

    recipes = list_recipes()
    print(recipes)

    dirpaths, packages, versions = list_dockerfiles()
    print(packages)

    pipelines = list_pipelines()
    print(pipelines)

    aura_scan("git@github.com:Public-Health-Bioinformatics/kipper.git", "scan", options="-RP")
    strace_conda_install("velvet", options="-RP")
    strace_docker_build("spectra-cluster-cli", "v1.1.2", options="-RP")
    strace_pipeline_run("rnaseq", options="-RP")

    test_istributed_strace()
    """

    test_as_completed()
