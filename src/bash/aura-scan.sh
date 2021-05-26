#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    aura-scan - Use Aura to scan a Python path or Git repository

SYNOPSIS
    aura-scan [python-path|git-url] scan-home

DESCRIPTION
    Uses Aura to scan a Python path or Git repository and produce JSON
    output in the scan home directory. The Python path can be to an
    individual Python file, or to a directory containing Python files.

OPTIONS 
    None

EOF
}

# Parse command line options
while getopts ":h" opt; do
    case $opt in
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

# Teardown
# Nothing required
if [ -n "${git_url}" ]; then
    rm -rf ${python_name}
fi
