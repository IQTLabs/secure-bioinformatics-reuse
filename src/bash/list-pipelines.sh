#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    list-pipelines - list nf-core pipelines

SYNOPSIS
    list-pipelines

DESCRIPTION
    List nf-core Nextflow pipelines.

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
if [ "$#" -ne 0 ]; then
    echo "No arguments required."
    exit 1
fi

# Setup
set -e
conda activate nf-core

# List pipelines
n_lines=$(nf-core list --sort stars 2> /dev/null | wc -l)
let t_lines=n_lines-3
let h_lines=n_lines-4
nf-core list --sort stars 2> /dev/null \
    | tail -n ${t_lines} - \
    | head -n ${h_lines} - \
    | tr "│" " " \
    | tr -s " " \
    | cut -d " " -f 2

# Teardown
conda deactivate
