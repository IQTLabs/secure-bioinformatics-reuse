#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    grep-containers - search for commands in Dockerfiles

SYNOPSIS
    grep-containers [-d containers-directory] [-c commands]

DESCRIPTION
    Uses grep to search for a space separated list of commands in
    BioContainers Dockerfiles.

    An output files is created for each command named
    "grep-containers-${command}.log".

OPTIONS 
    -d    The containers directory
    -c    A space separated list of commands, default:
              "ssh sftp scp wget curl"

EOF
}

# Parse command line options
containers_dir="/home/ubuntu/containers"
commands="ssh sftp scp wget curl"
while getopts ":d:c:h" opt; do
    case $opt in
	d)
	    containers_dir="${OPTARG}"
	    ;;
	c)
	    commands="-${OPTARG}"
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
if [ "$#" -ne 0 ]; then
    echo "No arguments required"
    exit 1
fi

# Setup
set -e

# Find and search recipes in background subshells
for command in ${commands}; do
    $(find ${containers_dir} -name "Dockerfile" \
	   -exec grep -Hn ${command} {} \; \
	  | tee grep-containers-${command}.log \
		> /dev/null) &
done

# Teardown
# Nothing required
