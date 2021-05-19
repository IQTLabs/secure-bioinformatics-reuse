#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    aura-scan - scan a Python file

SYNOPSIS
    aura-scan path-to-python-file path-to-scan-home

DESCRIPTION
    Uses Aura to scan a python file and produce JSON output.

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
	    echo "Option -${OPTARG} requires an argument." >&2
	    usage
	    exit 1
	    ;;
    esac
done

# Parse command line arguments
shift `expr ${OPTIND} - 1`
if [ "$#" -ne 2 ]; then
    echo "Two arguments required."
    exit 1
fi
file_home=$(dirname "${1}")
file_name=$(basename "${1}")
scan_home="${2}"

# Setup
set -xe

# Scan a python file and produce JSON output
scan_name=$(echo "${file_name}" | sed s/.py/.json/)
docker run \
       -v ${file_home}:/home \
       --rm sourcecodeai/aura:dev scan \
       /home/${file_name} -v -f json \
       > ${scan_home}/${scan_name}

# Teardown
# Nothing required
