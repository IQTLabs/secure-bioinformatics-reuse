#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    strace-docker-build - trace a docker build

SYNOPSIS
    strace-docker-build [-s suffix] build-directory package

DESCRIPTION
    Uses strace to trace the build of the docker file in the build
    directory.

    A directory is created to contain all output files, and each uses
    a base name give by "strace-docker-build-${package}-${suffix}.

OPTIONS 
    -s    The suffix of the base name for the output directory and
          files, default: ""

EOF
}

# Parse command line options
suffix=""
do_clean=0
while getopts ":s:Ch" opt; do
    case $opt in
	s)
	    suffix="-${OPTARG}"
	    ;;
	C)
	    do_clean=1
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
build_directory="${1}"
package="${2}"

# Setup
set -xe
base_name="strace-docker-build-${package}${suffix}"
rm -rf ${base_name}
mkdir ${base_name}
output_directory="${PWD}/${base_name}"
pushd ${build_directory}

# Docker build
base_name="strace-conda-install-${package}${suffix}"
rm -f ${base_name}.log
docker images | tr -s " " | sort > original_images.txt
strace -o ${base_name}.log docker build --tag ${package} .
if [ ${do_clean} == 1 ]; then
    docker images | tr -s " " | sort > current_images.txt
    images=$(comm -13 original_images.txt current_images.txt \
		 | cut -d " " -f 1-2 | tr " " ":")
    for image in ${images}; do
	docker rmi ${image}
    done
    docker system prune --volumes -f
fi

# List unique command short descriptions
commands=$(cat ${base_name}.log | cut -d "(" -f 1 \
	       | grep -v "+++" | grep -v -- "---" | sort | uniq)
rm -f ${base_name}.cmd
for command in $commands; do
    man -f $command >> ${base_name}.cmd
done
mv ${base_name}.log ${output_directory}
mv ${base_name}.cmd ${output_directory}

# Teardown
popd
