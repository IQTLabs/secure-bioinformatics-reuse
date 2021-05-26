#!/usr/bin/env bash

# Print usage
usage() {
    cat << EOF

NAME
    strace-docker-build - trace a docker build

SYNOPSIS
    strace-docker-build [-s suffix] [-C] [-R] [-H target-host] [-P] build-directory package version

DESCRIPTION
    Uses strace to trace the build of the docker file in the build
    directory with tag "package-version".

    A directory is created to contain all output files, and each uses
    a base name give by "strace-docker-build-${package}-%{version}${suffix}".

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

OPTIONS 
    -s    The suffix of the base name for the output directory and
          files, default: ""
    -C    Clean conda environment
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

EOF
}

# Parse command line options
suffix=""
do_clean=0
do_recursive_copy=0
target_host=52.207.108.184
do_purge_output=0
while getopts ":s:CRH:Ph" opt; do
    case $opt in
	s)
	    suffix="-${OPTARG}"
	    ;;
	C)
	    do_clean=1
	    ;;
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
if [ "$#" -ne 3 ]; then
    echo "Three arguments required"
    exit 1
fi
build_directory="${1}"
package="${2}"
version="${3}"

# Setup
set -xe
strace_home="strace-docker-build-${package}-$version${suffix}"
rm -rf ${strace_home}
mkdir ${strace_home}
output_directory="${PWD}/${strace_home}"

# Work in build directory
pushd ${build_directory}

# Docker build
base_name="strace-docker-build-${package}-${version}${suffix}"
rm -f ${base_name}.log
docker images \
    | tr -s " " \
    | sort > original_images.txt
strace -o ${base_name}.log docker build --tag ${package}-${version} .
if [ ${do_clean} == 1 ]; then
    docker images \
	| tr -s " " \
	| sort > current_images.txt
    images=$(comm -13 original_images.txt current_images.txt \
		 | cut -d " " -f 1-2 \
		 | tr " " ":")
    for image in ${images}; do
	docker rmi ${image}
    done
    docker system prune --volumes -f
fi

# List unique command short descriptions
commands=$(cat ${base_name}.log \
	       | cut -d "(" -f 1 \
	       | grep -v "+++" \
	       | grep -v -- "---" \
	       | sort \
	       | uniq)
rm -f ${base_name}.cmd
for command in $commands; do
    man -f $command >> ${base_name}.cmd
done
mv ${base_name}.log ${output_directory}
mv ${base_name}.cmd ${output_directory}

# Work in original directory
popd

# Recursively copy the output directory to the target host
if [ $do_recursive_copy == 1 ]; then
    scp \
	-i ~/.ssh/sbr-01.pem \
	-o "StrictHostKeyChecking no" \
	-r ${strace_home} \
	ubuntu@${target_host}:~/target
fi

# Teardown
if [ ${do_purge_output} == 1 ]; then
    rm -rf ${strace_home}
fi
