# Run using "bash -i"

# Print usage
usage() {
    cat << EOF

NAME
    strace-conda-install - trace a conda install of a package

SYNOPSIS
    strace-conda-install [-c channel] [-s suffix] package

DESCRIPTION
    Uses strace to trace the installation of a package fron a channel
    using conda.

    A directory is created to contain all output files, and each uses
    a base name give by "strace-conda-install-${package}-${suffix}.

OPTIONS 
    -c    The conda channel containing the package, default: bioconda
    -s    The suffix of the base name for the output directory and
          files, default: ""

EOF
}

# Parse command line options
channel="bioconda"
suffix=""
do_clean=0
while getopts ":c:s:Ch" opt; do
    case $opt in
	c)
	    channel="${OPTARG}"
	    ;;
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
package="${1}"

# Setup
set -xe
base_name="strace-conda-install-${package}${suffix}"
rm -rf ${base_name}
mkdir ${base_name}
pushd ${base_name}

# Conda install
base_name="strace-conda-install-${package}${suffix}"
conda create -y --name sbr
conda activate sbr
rm -f ${base_name}.log
strace -o ${base_name}.log conda install -y -c ${channel} ${package}
conda deactivate
conda remove -y --name sbr --all
if [ ${do_clean} == 1 ]; then
    conda clean -y --all
fi

# List unique command short descriptions
commands="$(cat ${base_name}.log | cut -d "(" -f 1 | grep -v "+++" | grep -v -- "---" | sort | uniq)"
rm -f ${base_name}.cmd
for command in $commands; do
    man -f $command >> ${base_name}.cmd
done

# Conda install tracing child processes as they are created by
# currently traced processes as a result of the fork(2), vfork(2) and
# clone(2) system calls
base_name="strace-f-conda-install-${package}${suffix}"
conda create -y --name sbr
conda activate sbr
rm -f ${base_name}.log
strace -f -o ${base_name}.log conda install -y -c ${channel} ${package}
conda deactivate
conda remove -y --name sbr --all
if [ ${do_clean} == 1 ]; then
    conda clean -y --all
fi

# Conda install tracing child processes as they are created by
# currently traced processes as a result of the fork(2), vfork(2) and
# clone(2) system calls and output to separate files
base_name="strace-ff-conda-install-${package}${suffix}"
conda create -y --name sbr
conda activate sbr
rm -f ${base_name}.log
strace -ff -o ${base_name}.log conda install -y -c ${channel} ${package}
conda deactivate
conda remove -y --name sbr --all
if [ ${do_clean} == 1 ]; then
    conda clean -y --all
fi

# Teardown
popd
