import os
import subprocess

from dask.distributed import Client, SSHCluster

RECIPES_DIR="/home/ubuntu/bioconda-recipes"
CONTAINERS_DIR="/home/ubuntu/containers"

from DaskPool import DaskPool


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


def list_recipes():
    return sorted(os.listdir(RECIPES_DIR + "/recipes"))


def strace_docker_build():
    """
    subprocess.Popen(
        "cd ; date > date.log",
        shell=True,
        stdin=None,
        stdout=None,
        stderr=None,
        close_fds=True,
    )
    """
    return subprocess.run(
        [
            "/home/ubuntu/secure-bioinformatics-reuse/src/bash/strace-docker-build.sh",
            "/home/ubuntu/containers/spectra-cluster-cli/v1.1.2",
            "spectra-cluster-cli",
            "v1.1.2",
        ],
        capture_output=True
    )


def inc(x):
    return x + 1


def add(x, y):
    return x + y


def run(cmd):
    return subprocess.run("date", capture_output=True)
    # return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def test_dask_cluster():
    daskPool = DaskPool()
    # daskPool.restart_pool()
    daskPool.maintain_pool()
    daskPool.checkout_branch()
    cluster = SSHCluster(
        [i.ip_address for i in daskPool.instances],
        connect_options={"known_hosts": None, "client_keys": ['~/.ssh/dask-01.pem']},
        worker_options={"nthreads": 2},
        scheduler_options={"port": 0, "dashboard_address": ":8797"}
    )
    client = Client(cluster)
    a = client.submit(inc, 1)
    b = client.submit(inc, 2)
    c = client.submit(add, a, b)
    print(c.result())
    d = client.submit(run, "date")
    print(d.result())
    e = client.submit(strace_docker_build)
    print(e.result())


if __name__ == "__main__":
    # dirpaths, packages, versions = list_dockerfiles()
    # recipes = list_recipes()
    test_dask_cluster()
    # result = strace_docker_build()
