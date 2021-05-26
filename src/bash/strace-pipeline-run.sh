# Run using "bash -i"

# Print usage
usage() {
    cat << EOF

NAME
    strace-pipeline-run - trace run of nf-core pipeline

SYNOPSIS
    strace-pipeline-run [-R] [-H target-host] [-P] pipeline

DESCRIPTION
    Uses strace to trace the nextflow run of an nf-core pipeline.

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
if [ "$#" -ne 1 ]; then
    echo "Only one argument required"
    exit 1
fi
pipeline="${1}"

# Setup
set -xe
strace_home="strace-pipeline-run-${pipeline}"
rm -rf ${strace_home}
mkdir ${strace_home}
conda activate nf-core

# Work in strace home
pushd ${strace_home}

# Pipeline run
base_name="strace-pipeline-run-${pipeline}"
rm -f ${base_name}.log
strace -o ${base_name}.log \
       nextflow run nf-core/${pipeline} -profile test,docker

# List unique command short descriptions
commands="$(cat ${base_name}.log \
		| cut -d "(" -f 1 \
		| grep -v "+++" \
		| grep -v -- "---" \
		| sort \
		| uniq)"
rm -f ${base_name}.cmd
for command in $commands; do
    man -f $command >> ${base_name}.cmd
done

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
