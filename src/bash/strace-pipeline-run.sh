# Run using "bash -i"

# Print usage
usage() {
    cat << EOF

NAME
    strace-pipeline-run - trace run of nf-core pipeline

SYNOPSIS
    strace-pipeline-run pipeline

DESCRIPTION
    Uses strace to trace the nextflow run of an nf-core pipeline.

OPTIONS 
    None

EOF
}

# Parse command line options
do_clean=0
while getopts ":Ch" opt; do
    case $opt in
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
base_name="strace-pipeline-run-${pipeline}"
rm -rf ${base_name}
mkdir ${base_name}
pushd ${base_name}
conda activate nf-core

# Pipeline run
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

# Teardown
conda deactivate
popd
