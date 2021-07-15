from glob import glob
import json
import logging
from pathlib import Path
from pprint import pprint
import re

from matplotlib import pyplot as plt
from matplotlib import ticker
import numpy as np
import pandas as pd

# TARGET_DIR = Path("/home/ubuntu/target")
TARGET_DIR = Path("/Users/raymondleclair/target-2021-07-07")

SCAN_RESULTS_DIR = TARGET_DIR / "scan"
SCAN_RESULTS_FILE = TARGET_DIR / Path(SCAN_RESULTS_DIR.name + "-results").with_suffix(
    ".json"
)
SCAN_COUNTS_FILE = TARGET_DIR / Path(SCAN_RESULTS_DIR.name + "-counts").with_suffix(
    ".json"
)
SCAN_SUMMARY_FILE = TARGET_DIR / Path(SCAN_RESULTS_DIR.name + "-summary").with_suffix(
    ".csv"
)

STRACE_RESULTS_DIR = TARGET_DIR
STRACE_RESULTS_FILE = TARGET_DIR / Path(
    STRACE_RESULTS_DIR.name + "-results"
).with_suffix(".json")
STRACE_COUNTS_FILE = TARGET_DIR / Path(STRACE_RESULTS_DIR.name + "-counts").with_suffix(
    ".json"
)

root = logging.getLogger()
root.setLevel(logging.INFO)

if not root.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    root.addHandler(ch)

logger = logging.getLogger("analyze")


def load_strace_results(target_dir=TARGET_DIR, force=False):
    """Read and search strace results and retain internet addresses
    with ports and executed files.  Collect the strace results and
    serialize to JSON for faster deserialization.
    """
    if STRACE_RESULTS_FILE.exists() and not force:
        logger.info("Loading strace results file: {0}".format(STRACE_RESULTS_FILE))
        with STRACE_RESULTS_FILE.open("r") as fp:
            strace_results = json.load(fp)
    else:
        # Define patterns for finding internet addresses
        # TODO: identify how to handle IPv6 as well as IPv4 addresses
        p_inet_addr = re.compile('inet_addr\("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"\)')
        # p_connect - covered by pattern above
        # p_getpeername - covered by pattern above
        # p_getsockname - covered by pattern above
        # p_recvfrom - does not appear to be needed
        # p_recvmsg - covered by pattern above
        # p_sendmsg - does not appear to be needed
        # p_sendto - does not appear to be needed

        # Define pattern for finding port numbers
        p_htons = re.compile("htons\((\d{1,5})\)")

        # Define pattern for finding files whose mode has been changed
        # p_chmod - does not appear to be needed

        # Define pattern for finding files to be executed
        p_exec_file = re.compile('^exec.*\("(.*?)"')

        # Collect the strace results
        strace_results = []
        for log_file in glob(str(target_dir) + "/*/strace-*.log"):
            strace_result = {}
            strace_result["log_file"] = log_file

            strace_result["inet_addrs"] = []
            strace_result["exec_files"] = []
            with open(log_file, "r") as fp:
                logger.info("Loading strace log file: {0}".format(log_file))
                line = fp.readline()
                while len(line) > 0:

                    # Find internet addresses
                    s_inet_addr = p_inet_addr.findall(line)
                    if len(s_inet_addr) > 0:
                        # Find ports, if specified
                        s_htons = p_htons.findall(line)
                        if len(s_inet_addr) == len(s_htons) or len(s_htons) == 0:
                            # Found nonzero and an equal number of
                            # addresses and ports, or only addresses,
                            # as for recvmsg()
                            inet_addr = {}
                            inet_addr["line"] = line
                            inet_addr["addrs"] = s_inet_addr
                            inet_addr["ports"] = s_htons
                            strace_result["inet_addrs"].append(inet_addr)
                        else:
                            # Found nonzero but an unequal number of
                            # addresses and ports, which is unexpected
                            logger.error(
                                "Found {0} addresses and {1} ports, which is unexpected".format(
                                    len(s_inet_addr), len(s_htons)
                                )
                            )

                    # Find exectuted files
                    s = p_exec_file.search(line)
                    if s is not None:
                        exec_file = {}
                        exec_file["line"] = line
                        exec_file["file"] = s.group(1)
                        strace_result["exec_files"].append(exec_file)

                    line = fp.readline()

            strace_results.append(strace_result)

        logger.info("Dumping strace results file: {0}".format(STRACE_RESULTS_FILE))
        with STRACE_RESULTS_FILE.open("w") as fp:
            json.dump(strace_results, fp, indent=4)

    return strace_results


def load_scan_results(force=False):
    """Deserialize Aura scan results and retain detections with a
    non-zero score. Collect the scan results and serialize to JSON for
    faster deserialization.
    """
    if SCAN_RESULTS_FILE.exists() and not force:
        logger.info("Loading scan results file: {0}".format(SCAN_RESULTS_FILE))
        with SCAN_RESULTS_FILE.open("r") as fp:
            scan_results = json.load(fp)
    else:
        # Collect the scan results
        scan_results = []
        for scan_path in SCAN_RESULTS_DIR.iterdir():
            logger.info("Loading Aura scan path: {0}".format(scan_path))
            scan_result = json.loads(scan_path.read_text())
            detections = []
            scores = []
            for detection in scan_result["detections"]:
                score = detection["score"]
                if score > 0:
                    detections.append(detection)
                    scores.append(score)
            scan_result["detections"] = detections
            scan_result["scores"] = scores

            scan_results.append(scan_result)

        logger.info("Dumping scan results file: {0}".format(SCAN_RESULTS_FILE))
        with SCAN_RESULTS_FILE.open("w") as fp:
            json.dump(scan_results, fp, indent=4)

    return scan_results


def count_strace_results(strace_results):
    """Collect strace internet addresses and executed files by strace
    type ("conda install", "docker build", or "pipeline run").
    """
    strace_counts = {}

    # Compile patterns for identifying scan type
    p_conda_install = re.compile("-conda-install-")
    p_docker_build = re.compile("-docker-build-")
    p_pipeline_run = re.compile("-pipeline-run-")

    # Consider each strace result
    for strace_result in strace_results:

        # Identify strace type
        log_file = strace_result["log_file"]
        if p_conda_install.search(log_file) is not None:
            strace_type = "conda_install"
            logger.debug("Log file {0} is strace of conda install".format(log_file))
        elif p_docker_build.search(log_file) is not None:
            strace_type = "docker_build"
            logger.debug("Log file {0} is strace of docker build".format(log_file))
        elif p_pipeline_run.search(log_file) is not None:
            strace_type = "pipeline_run"
            logger.debug("Log file {0} is strace of pipeline run".format(log_file))
        else:
            raise Exception("Unexpected log file: {0}".format(log_file))

        # Initialize collected results
        if strace_type not in strace_counts:
            strace_counts[strace_type] = {}
        if "addrs" not in strace_counts[strace_type]:
            strace_counts[strace_type]["addrs"] = {}
        if "files" not in strace_counts[strace_type]:
            strace_counts[strace_type]["files"] = {}

        # Collect internet addresses
        for inet_addr in strace_result["inet_addrs"]:
            for addr in inet_addr["addrs"]:
                if addr not in strace_counts[strace_type]["addrs"]:
                    strace_counts[strace_type]["addrs"][addr] = 0
                strace_counts[strace_type]["addrs"][addr] += 1

        # Collect executed files
        for exec_file in strace_result["exec_files"]:
            file = exec_file["file"]
            if file not in strace_counts[strace_type]["files"]:
                strace_counts[strace_type]["files"][file] = 0
            strace_counts[strace_type]["files"][file] += 1

    with open(STRACE_COUNTS_FILE, "w") as fp:
        pprint(strace_counts, stream=fp)

    return strace_counts


def count_scan_results(scan_results):
    """Collect Aura scan scores for all detections, and for each
    detection by type.
    """
    scan_counts = {}
    scan_counts["scores_for_all"] = []
    scan_counts["scores_for_types"] = {}
    for scan_result in scan_results:
        for detection in scan_result["detections"]:
            score = detection["score"]
            type = detection["type"]
            scan_counts["scores_for_all"].append(score)
            if type not in scan_counts["scores_for_types"]:
                scan_counts["scores_for_types"][type] = []
            scan_counts["scores_for_types"][type].append(score)

    with open(SCAN_COUNTS_FILE, "w") as fp:
        pprint(strace_counts, stream=fp)

    return scan_counts


def summarize_scan_results(scan_results):
    """Write aura scan results to a file for review.
    """
    with SCAN_SUMMARY_FILE.open("w") as fp:
        fp.write("score,detection type,severity,location,line number\n")
        for scan_result in scan_results:
            detections = scan_result["detections"]
            scores = np.array(scan_result["scores"])
            if len(scores) == 0:
                continue
            for i_det in np.nonzero(scores == max(scores))[0]:
                detection = detections[i_det]
                score = detection["score"]
                det_type = detection["type"]
                severity = detection["severity"]
                if "line_no" in detection:
                    line_no = detection["line_no"]
                else:
                    line_no = "NA"
                location = detection["location"].replace("/home/", "")
                fp.write(f"{score},{det_type},{severity},{location},{line_no}\n")


def plot_strace_counts(strace_counts):
    """Plot strace counts as a bar plot.
    """
    counts = pd.DataFrame.from_dict(
        strace_counts["conda_install"]["addrs"], orient="index", columns=["counts"]
    ).sort_values(by=["counts"])
    n_rows = 20
    bar_plot_counts(
        counts.head(n_rows).loc[:, "counts"].values,
        counts.head(n_rows).index,
        "Least frequently occuring IP addresses",
    )
    bar_plot_counts(
        counts.tail(n_rows).loc[:, "counts"].values,
        counts.tail(n_rows).index,
        "Most frequently occuring IP addresses",
    )
    return counts


def plot_scan_counts(scan_counts):
    """Plot scan counts as a heatmap.
    """
    unique_types = np.array(list(scan_counts["scores_for_types"].keys()))
    unique_scores = np.unique(np.array(scan_counts["scores_for_all"]))
    bin_edges = np.append(unique_scores, 2 * max(unique_scores))
    counts = pd.DataFrame(0, index=sorted(unique_types), columns=sorted(unique_scores))
    for unique_type in unique_types:
        counts.loc[unique_type, :] = np.log10(
            np.histogram(
                np.array(scan_counts["scores_for_types"][unique_type]), bins=bin_edges
            )[0]
        )
    img_plot_counts(counts, title="Detection Scores", cbarlabel="$log_{10}(Counts)$")

    return counts


def bar_plot_counts(height, xticklabels, title=""):
    """Create counts bar plot.
    """
    x = np.arange(len(height))
    fig, ax = plt.subplots()
    ax.bar(x, height)
    ax.set_xticks(np.arange(len(x)))
    ax.set_xticklabels(xticklabels, rotation=-90)
    ax.set_ylabel("Count")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(title.replace(" ", "-") + ".png")
    plt.show()

    return fig, ax


def img_plot_counts(data, title="", cbarlabel=""):
    """Create counts heatmap.
    """
    fig, ax = plt.subplots()
    im, cbar = heatmap(
        # data.transpose().iloc[::-1, ::-1],
        data,
        ax=ax,
        cmap="BuPu",
        cbarlabel=cbarlabel,
        # aspect="auto",
    )
    # texts = annotate_heatmap(im, valfmt="{x:.1f} t")
    if len(title) > 0:
        ax.set_title(title)
    ax.set_xlabel("Score")
    pos_im = ax.get_position()
    pos_cb = cbar.ax.get_position()
    fig.set_figwidth(fig.get_figwidth() * (pos_cb.xmax - pos_im.xmin + 0.33))
    plt.tight_layout()
    plt.savefig(title.replace(" ", "-") + ".png")
    plt.show()

    return fig, ax, im, cbar


def heatmap(data, ax=None, cbar_kw={}, cbarlabel="", **kwargs):
    """Create a heatmap from a numpy array and two lists of labels.

    Parameters
    ----------
    data
        A 2D numpy array of shape (N, M).
    ax
        A `matplotlib.axes.Axes` instance to which the heatmap is plotted.  If
        not provided, use current axes or create a new one.  Optional.
    cbar_kw
        A dictionary with arguments to `matplotlib.Figure.colorbar`.  Optional.
    cbarlabel
        The label for the colorbar.  Optional.
    **kwargs
        All other arguments are forwarded to `imshow`.
    """
    if not ax:
        ax = plt.gca()

    # Plot the heatmap
    im = ax.imshow(data, **kwargs)

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    # We want to show all ticks...
    ax.set_xticks(np.arange(data.shape[1]))
    ax.set_yticks(np.arange(data.shape[0]))
    # ... and label them with the respective list entries.
    ax.set_xticklabels(data.columns.to_list())
    ax.set_yticklabels(data.index.to_list())

    # Let the horizontal axes labeling appear on top.
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-45, ha="right", rotation_mode="anchor")

    # Turn spines off and create white grid.
    for edge, spine in ax.spines.items():
        # spine.set_visible(False)
        spine.set_color("w")

    ax.set_xticks(np.arange(data.shape[1] + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0] + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="w", linestyle="-", linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)

    return im, cbar


def annotate_heatmap(
    im,
    data=None,
    valfmt="{x:.2f}",
    textcolors=["black", "white"],
    threshold=None,
    **textkw,
):
    """A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A list or array of two color specifications.  The first is used for
        values below a threshold, the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """
    if not isinstance(data, (list, np.ndarray)):
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(data.max()) / 2.0

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center", verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts


if __name__ == "__main__":

    strace_results = load_strace_results()
    strace_counts = count_strace_results(strace_results)
    plot_strace_counts(strace_counts)

    scan_results = load_scan_results()
    scan_counts = count_scan_results(scan_results)
    plot_scan_counts(scan_counts)
    summarize_scan_results(scan_results)
