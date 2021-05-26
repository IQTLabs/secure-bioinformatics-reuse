#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    aura-scan - Use Aura to scan a Python path or Git repository

SYNOPSIS
    aura-scan [-R] [-H target-host] [-P] python-src scan-home

DESCRIPTION
    Uses Aura to scan a Python source, either a path or Git
    repository, and produce JSON output in the scan home
    directory. The Python path can be to an individual Python file, or
    to a directory containing Python files.

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

OPTIONS 
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

EOF
}

# Parse command line options
do_recursive_copy=0
target_host=52.207.108.184
do_purge_output=0
while getopts ":RH:Ph" opt; do
    case $opt in
	R)
	    do_recursive_copy=1
	    ;;
	H)
	    target_host=${OPTARG}
	    ;;
	P)
	    do_purge_output=1
	    ;;
	h)
	    usage
	    exit 0
	    ;;
	\?)
	    echo "Invalid option: -${OPTARG}" >&2
	    usage
	    exit 1
	    ;;
	\:)
	    echo "Option -${OPTARG} requires an argument" >&2
	    usage
	    exit 1
	    ;;
    esac
done

# Parse command line arguments
shift `expr ${OPTIND} - 1`
if [ "$#" -ne 2 ]; then
    echo "Two arguments required"
    exit 1
fi
if [ "${1: -4}" == ".git" ]; then
    git_url="${1}"
    python_name=$(basename "${1}" | sed s/.git//)
    python_home=$(realpath ${python_name} | xargs dirname)
    scan_name="${python_name}.json"
else
    git_url=""
    python_name=$(realpath "${1}" | xargs basename)
    python_home=$(realpath "${1}" | xargs dirname)
    scan_name="$(echo "${python_name}" | sed s/.py//).json"
fi
scan_home="${2}"

# Setup
set -xe
if [ -n "${git_url}" ]; then
    rm -rf ${python_name}
    git clone ${git_url}
fi
mkdir -p ${scan_home}

# Use Aura to Scan a python file and produce JSON output
docker run \
       -v ${python_home}:/home \
       --rm sourcecodeai/aura:dev scan \
       /home/${python_name} -v -f json \
       > ${scan_home}/${scan_name}

# Recursively copy the output directory to the target host
if [ $do_recursive_copy == 1 ]; then
    scp \
	-i ~/.ssh/sbr-01.pem \
	-o "StrictHostKeyChecking no" \
	-r ${scan_home} \
	ubuntu@${target_host}:~/target
fi

# Teardown
if [ -n "${git_url}" ]; then
    rm -rf ${python_name}
fi
if [ ${do_purge_output} == 1 ]; then
    rm -rf ${scan_home}
fi
