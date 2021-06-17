# Run using "bash -i"

# Print usage
usage() {
    cat << EOF

NAME
    strace-conda-install - trace a conda install of a package

SYNOPSIS
    strace-conda-install [-c channel] [-s suffix] [-C] [-R] [-H target-host] [-P] package

DESCRIPTION
    Uses strace to trace the installation of a package fron a channel
    using conda.

    A directory is created to contain all output files, and each uses
    a base name give by "strace-conda-install-${package}-${suffix}".

    Optionally recursively copy the output directory to the target
    host, or purge the output directory.

OPTIONS 
    -c    The conda channel containing the package, default: bioconda
    -s    The suffix of the base name for the output directory and
          files, default: ""
    -C    Clean conda environment
    -R    Recursively copy the output directory to the target host
    -H    Set the target host IP address, default: 52.207.108.184
    -P    Purge output directory

EOF
}

# Parse command line options
channel="bioconda"
suffix=""
do_clean=0
do_recursive_copy=0
target_host=52.207.108.184
do_purge_output=0
while getopts ":c:s:CRH:Ph" opt; do
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
package="${1}"

# Setup
set -xe
strace_home="strace-conda-install-${package}${suffix}"
rm -rf ${strace_home}
mkdir -p ${strace_home}

# Work in strace home
pushd ${strace_home}

# Conda install
base_name="strace-conda-install-${package}${suffix}"
conda create -y --name ${package}-${suffix}
conda activate ${package}-${suffix}
rm -f ${base_name}.log
strace -o ${base_name}.log conda install -y -c ${channel} ${package}
conda deactivate
conda remove -y --name ${package}-${suffix} --all
if [ ${do_clean} == 1 ]; then
    conda clean -y --all
fi

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

# Conda install tracing child processes as they are created by
# currently traced processes as a result of the fork(2), vfork(2) and
# clone(2) system calls
base_name="strace-f-conda-install-${package}${suffix}"
conda create -y --name ${package}-${suffix}-f
conda activate ${package}-${suffix}-f
rm -f ${base_name}.log
strace -f -o ${base_name}.log conda install -y -c ${channel} ${package}
conda deactivate
conda remove -y --name ${package}-${suffix}-f --all
if [ ${do_clean} == 1 ]; then
    conda clean -y --all
fi

# Conda install tracing child processes as they are created by
# currently traced processes as a result of the fork(2), vfork(2) and
# clone(2) system calls and output to separate files
base_name="strace-ff-conda-install-${package}${suffix}"
conda create -y --name ${package}-${suffix}-ff
conda activate ${package}-${suffix}-ff
rm -f ${base_name}.log
strace -ff -o ${base_name}.log conda install -y -c ${channel} ${package}
conda deactivate
conda remove -y --name ${package}-${suffix}-ff --all
if [ ${do_clean} == 1 ]; then
    conda clean -y --all
fi

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
