from argparse import ArgumentParser
import json
import logging
import os
from pathlib import Path
import subprocess

from dask.distributed import Client, SSHCluster, as_completed

from DaskPool import DaskPool


KEY_DIR = "~/.ssh"
SHELL_CMD = "/usr/bin/bash"
SCRIPTS_DIR = "/home/ubuntu/secure-bioinformatics-reuse/src/bash"
RECIPES_DIR = "/home/ubuntu/bioconda-recipes"
CONTAINERS_DIR = "/home/ubuntu/containers"
TARGET_DIR = "/home/ubuntu/target"

root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
root.addHandler(ch)

logging.getLogger("asyncssh").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)

logger = logging.getLogger("distribute")


def list_repositories():
    """List repositories which have most lines of code in Python from
    the Bioinformatics download of 2020-11-11.
    """
    loc_path = Path(os.path.realpath(__file__)).parents[2].joinpath("dat", "loc.json")
    with open(loc_path, "r") as loc_fp:
        loc = json.load(loc_fp)
    repositories = []
    for d in loc:
        if list(d)[1] == "Python":
            repositories.append((d["git_url"],))
    return repositories


def aura_scan(python_src, scan_home="scan", options=""):
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
                os.path.join(SCRIPTS_DIR, "aura-scan.sh"),
                options,
                python_src,
                scan_home,
            ],
            capture_output=True,
        )
    except Exception as e:
        logger.error(e)
    return completed_process


def list_recipes():
    """List recipes in git@github.com:IQTLabs/bioconda-recipes.git.
    """
    recipes = []
    for recipe in sorted(os.listdir(os.path.join(RECIPES_DIR, "recipes"))):
        recipes.append((recipe,))
    return recipes


def strace_conda_install(package, options=""):
    """Run a script that uses strace to trace the installation of a
    package from a channel using conda.

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
    except Exception as e:
        logger.error(e)
    return completed_process


def list_dockerfiles():
    """List Dockerfiles in git@github.com:ralatsdc/containers.git.
    """
    dockerfiles = []
    for dirpath, dirnames, filenames in os.walk(CONTAINERS_DIR):
        for filename in filenames:
            if filename == "Dockerfile":
                package = os.path.basename(os.path.dirname(dirpath))
                version = os.path.basename(dirpath)
                if package != "containers":
                    dockerfiles.append((package, version))
    return dockerfiles


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
    -C    Clean up new Docker images
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
    except Exception as e:
        logger.error(e)
    return completed_process


def list_pipelines():
    """List pipelines in the nf-core conda package.
    """
    completed_process = subprocess.run(
        [SHELL_CMD, "-i", os.path.join(SCRIPTS_DIR, "list-pipelines.sh")],
        capture_output=True,
        text=True,
    )
    lines = completed_process.stdout.split("\n")
    lines.remove("")
    pipelines = []
    for line in lines:
        pipelines.append((line,))
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
    except Exception as e:
        logger.error(e)
    return completed_process


def setup_pool(target_count=3, instance_type="t3.large"):
    """Setup a DaskPool instance by maintaining the target count of
    instances, and checking out the required branch. Return the
    DaskPool instance and the Dask SSHCluster, and Client instances.
    """
    pool = DaskPool(target_count=target_count, instance_type=instance_type)
    pool.maintain_pool()
    pool.checkout_branch()
    cluster = SSHCluster(
        [i.ip_address for i in pool.instances],
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


def distribute_runs(
    run_case, max_runs=9, target_count=3, instance_type="t3.large", teardown_pool=False,
):
    """ Setup a DaskPool instance, select a function and corresponding
    function arguments list, run the functions on the corresponding
    Dask cluster, and terminate the pool, if requested.
    """
    # TODO: mkdir -p ~/target/scan
    # Setup a DaskPool instance
    pool, cluster, client = setup_pool(
        target_count=target_count, instance_type=instance_type
    )

    # Select a function and corresponding function arguments list
    logger.info("Run function: {0}".format(run_case))
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
    # of pool instances, less one for the scheduler
    n_run_args = 0
    n_futures = 0
    submitted_futures = []
    for run_args in run_args_list:
        # Set options, and skip runs for which the output paths exist
        n_run_args += 1
        if run_case == "aura_scan":
            options = "-RP"
            output_path = os.path.join(
                TARGET_DIR,
                "scan",
                os.path.basename(run_args[0]).replace(".git", ".json"),
            )
        elif run_case == "strace_conda_install":
            options = "-RP"
            output_path = os.path.join(
                TARGET_DIR, "strace-conda-install-{0}".format(run_args[0])
            )
        elif run_case == "strace_docker_build":
            options = "-RPC"
            output_path = os.path.join(
                TARGET_DIR,
                "strace-docker-build-{0}-{1}".format(run_args[0], run_args[1]),
            )
        elif run_case == "strace_pipeline_run":
            options = "-RP"
            output_path = os.path.join(
                TARGET_DIR, "strace-pipeline-run-{0}".format(run_args[0])
            )
        if os.path.exists(output_path):
            logger.info("Skipping run: {0}{1}".format(run_case, run_args))
            continue
        else:
            if run_case != "aura_scan":
                # Make the output directory
                os.mkdir(output_path)
            # Indicate attempt
            Path(output_path).touch()
        logger.info("Submitting run: {0}{1}".format(run_case, run_args))
        submitted_futures.append(
            client.submit(run_function, *run_args, options=options)
        )
        n_futures += 1
        if n_futures == max_runs or n_futures == len(pool.instances) - 1:
            break

    # Submit another function to the cluster whenever a previously
    # submitted function completes
    as_completed_futures = as_completed(submitted_futures)
    for future in as_completed_futures:
        logger.debug(future.result())
        n_run_args += 1
        if n_futures < max_runs and n_run_args <= len(run_args_list):
            logger.info(
                "Submitting run: {0}{1}".format(run_case, run_args_list[n_run_args - 1])
            )
            as_completed_futures.add(
                client.submit(
                    run_function, *run_args_list[n_run_args - 1], options=options
                )
            )
            n_futures += 1
    logger.info("Submitted {0} runs".format(n_futures))

    # Terminate the pool, if requested.
    if teardown_pool:
        teardown_pool(pool)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run functions on a cluster")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-C",
        "--target-count",
        default=3,
        type=int,
        help="target count of machines in cluster",
    )
    parser.add_argument(
        "-T",
        "--instance-type",
        default="t3.large",
        help="instance type for machines in cluster",
    )
    parser.add_argument(
        "-s", "--start-pool", action="store_true", help="start instances in cluster",
    )
    parser.add_argument(
        "-t",
        "--terminate-pool",
        action="store_true",
        help="terminate instances in cluster",
    )
    parser.add_argument(
        "-R", "--max-runs", default=9, type=int, help="maximum number of runs"
    )
    parser.add_argument(
        "-F",
        "--run-function",
        action="store_true",
        help="run function locally for testing",
    )
    group.add_argument("-a", "--aura-scan", action="store_true", help="run Aura scans")
    group.add_argument(
        "-c", "--strace-conda-install", action="store_true", help="trace conda installs"
    )
    group.add_argument(
        "-d", "--strace-docker-build", action="store_true", help="trace docker builds"
    )
    group.add_argument(
        "-p", "--strace-pipeline-run", action="store_true", help="trace pipeline runs"
    )
    args = parser.parse_args()

    # Start instances in the pool, if requested.
    if args.start_pool:
        pool = DaskPool(
            target_count=args.target_count, instance_type=args.instance_type
        )
        pool.maintain_pool()
        pool.checkout_branch()

    # Terminate instances in the pool, if requested.
    if args.terminate_pool:
        pool = DaskPool(
            target_count=args.target_count, instance_type=args.instance_type
        )
        pool.terminate_pool()

    # Run the selected function locally, or on the cluster
    run_case = ""
    if args.aura_scan:
        run_case = "aura_scan"
    if args.strace_conda_install:
        run_case = "strace_conda_install"
    if args.strace_docker_build:
        run_case = "strace_docker_build"
    if args.strace_pipeline_run:
        run_case = "strace_pipeline_run"
    if run_case != "":
        if args.run_function:
            # Run the selected function locally
            if run_case == "aura_scan":
                python_src = "git@github.com:Public-Health-Bioinformatics/kipper.git"
                logger.info(f"Running Aura scan on {python_src}")
                aura_scan(
                    python_src, "scan", options="-RP",
                )
            elif run_case == "strace_conda_install":
                package = "velvet"
                logger.info(f"Tracing conda install of {package}")
                strace_conda_install(package, options="-RP")
            elif run_case == "strace_docker_build":
                package = "spectra-cluster-cli"
                version = "v1.1.2"
                logger.info(f"Tracing docker build of ralatsdio/{package}:{version}")
                strace_docker_build(package, version, options="-RPC")
            elif run_case == "strace_pipeline_run":
                pipeline = "rnaseq"
                logger.info(f"Tracing nextflow run of {pipeline}")
                strace_pipeline_run(pipeline, options="-RP")
        else:
            # Run the selected function on the cluster
            distribute_runs(
                run_case,
                max_runs=args.max_runs,
                target_count=args.target_count,
                instance_type=args.instance_type,
                teardown_pool=args.terminate_pool,
            )
