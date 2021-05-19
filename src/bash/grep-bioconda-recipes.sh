#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    grep-bioconda-recipes - search for commands in build scripts

SYNOPSIS
    grep-bioconda-recipes [-d bioconda-recipes-directory] [-c commands]

DESCRIPTION
    Uses grep to search for a space separated list of commands in
    Bioconda recipes build scripts.

    An output files is created for each command named
    "grep-bioconda-recipes-${command}.log".

OPTIONS 
    -d    The bioconda-recipes directory
    -c    A space separated list of commands, default: "ssh sftp scp
          wget curl"

EOF
}

# Parse command line options
BIOCONDA_RECIPES_DIR="/home/ubuntu/bioconda-recipes"
COMMANDS="ssh sftp scp wget curl"
while getopts ":d:c:h" opt; do
    case $opt in
	d)
	    BIOCONDA_RECIPES_DIR="${OPTARG}"
	    ;;
	c)
	    COMMANDS="-${OPTARG}"
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
for command in ${COMMANDS}; do
    $(find ${BIOCONDA_RECIPES_DIR} -name "*.sh" \
	   -exec grep -Hn ${command} {} \; \
	  | tee grep-bioconda-recipes-${command}.log \
		> /dev/null) &
done

# Teardown
# Nothing required
