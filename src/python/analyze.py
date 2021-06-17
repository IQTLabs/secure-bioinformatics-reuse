from glob import glob
import json
import logging
import numpy as np
from pathlib import Path
import re

TARGET_DIR = Path("/home/ubuntu/target")
SCAN_RESULTS_DIR = TARGET_DIR / "scan"
SCAN_RESULTS_FILE = TARGET_DIR / SCAN_RESULTS_DIR.with_suffix(".json").name
SCAN_SUMMARY_FILE = TARGET_DIR / SCAN_RESULTS_DIR.with_suffix(".csv").name

root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
root.addHandler(ch)

logger = logging.getLogger("analyze")


def load_strace_results(target_dir=TARGET_DIR):

    # Define patterns for finding internet addresses
    # TODO: identify how to handle IPv6 as well as IPv4
    p_inet_addr = re.compile('inet_addr\("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"')
    # p_connect - covered by pattern above
    # p_getpeername - covered by pattern above
    # p_getsockname - covered by pattern above
    # p_recvfrom - covered by pattern above
    # p_recvmsg - covered by pattern above
    # p_sendmsg - does not appear to be needed
    # p_sendto - does not appear to be needed

    # Define pattern for finding files whose mode has been changed
    # p_chmod - does not appear to be needed

    # Define pattern for finding files to be executed
    p_exec_file = re.compile('^exec.*\("(.*?)"')

    strace_results = []
    for log_file in glob(target_dir.name + "/*/strace-*.log"):
        strace_result = {}
        strace_result['log_file'] = log_file

        strace_result['inet_addrs'] = []
        strace_result['exec_files'] = []
        with open(log_file, "r") as fp:
            line = fp.readline()
            while line is not None:

                s = p_inet_addr.search(line)
                if s is not None:
                    inet_addr = {}
                    inet_addr['line'] = line
                    inet_addr['addr'] = s.group(1)
                    strace_result['inet_addrs'].append(inet_addr)

                s = p_exec_file.search(line)
                if s is not None:
                    exec_file = {}
                    exec_file['line'] = line
                    exec_file['file'] = s.group(1)
                    strace_result['exec_files'].append(exec_file)

    return strace_results


def load_aura_scan_results(force=False):
    """Deserialize Aura scan results and retain detections with a
    non-zero score. Collect the scan results and serialize to JSON for
    faster deserialization.
    """
    if SCAN_RESULTS_FILE.exists() and not force:
        logger.info("Loading scan results file: {0}".format(SCAN_RESULTS_FILE))
        with SCAN_RESULTS_FILE.open("r") as fp:
            scan_results = json.load(fp)
    else:
        scan_results = []
        for scan_path in SCAN_RESULTS_DIR.iterdir():
            logger.info("Loading scan path: {0}".format(scan_path))
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


def summarize_aura_scan_results(scan_results):
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


if __name__ == "__main__":
    # scan_results = load_aura_scan_results()
    # summarize_aura_scan_results(scan_results)
    strace_results = load_strace_results()
