import logging
import os
import subprocess

from dask.distributed import Client, SSHCluster

from DaskPool import DaskPool


RECIPES_DIR="/home/ubuntu/bioconda-recipes"
CONTAINERS_DIR="/home/ubuntu/containers"
SCRIPTS_DIR="/home/ubuntu/secure-bioinformatics-reuse/src/bash"


root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

logging.getLogger("asyncssh").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


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


def strace_docker_build(package, version):
    completed_process = subprocess.run(
        [
            os.path.join(SCRIPTS_DIR, "strace-docker-build.sh"),
            os.path.join(CONTAINERS_DIR, package, version),
            package,
            version,
        ],
        capture_output=True
    )
    return completed_process.returncode

def inc(x):
    return x + 1


def add(x, y):
    return x + y


def run(cmd):
    return subprocess.run("date", capture_output=True)


def test_one():
    daskPool = DaskPool()
    # daskPool.restart_pool()
    daskPool.maintain_pool()
    daskPool.checkout_branch()
    daskPool.checkout_branch()
    

def test_two():
    daskPool = DaskPool()
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
    print(d.result().stdout)
    e = client.submit(strace_docker_build, "spectra-cluster-cli", "v1.1.2")
    print(e.result())


if __name__ == "__main__":

    # dirpaths, packages, versions = list_dockerfiles()
    # recipes = list_recipes()
    # result = strace_docker_build()
    test_two()
