from glob import glob
import json
import logging
import numpy as np
from pathlib import Path
import re

# TARGET_DIR = Path("/home/ubuntu/target")
TARGET_DIR = Path("/Users/raymondleclair/target-2021-06-17")

SCAN_RESULTS_DIR = TARGET_DIR / "scan"
SCAN_RESULTS_FILE = TARGET_DIR / SCAN_RESULTS_DIR.with_suffix(".json").name
SCAN_SUMMARY_FILE = TARGET_DIR / SCAN_RESULTS_DIR.with_suffix(".csv").name

STRACE_RESULTS_DIR = TARGET_DIR
STRACE_RESULTS_FILE = TARGET_DIR / STRACE_RESULTS_DIR.with_suffix(".json").name
STRACE_SUMMARY_FILE = TARGET_DIR / STRACE_RESULTS_DIR.with_suffix(".csv").name

root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
                            # Found nonzero and an equal number of addresses and ports, or only addresses, as for recvmsg()
                            inet_addr = {}
                            inet_addr["line"] = line
                            inet_addr["addr"] = s_inet_addr
                            inet_addr["port"] = s_htons
                            strace_result["inet_addrs"].append(inet_addr)
                        else:
                            # Found nonzero but an unequal number of addresses and ports, which is unexpected
                            logger.error("Found {0} addresses and {1} ports, which is unexpected".format(len(s_inet_addr), len(s_htons)))

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
    strace_results = load_strace_results(force=True)

    """
    import socket

    target = "104.17.92.24"
    port = 443

    print(socket.getaddrinfo(target, port))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((target, port))

    sock.settimeout(2)

    query = "GET / HTTPS/1.1\nHost: " + target + "\n\n"

    http_get = bytes(query, 'utf-8')

    # sock.sendall(http_get)
    sock.send(bytes('GET HTTP/1.1 \r\n', 'utf-8'))

    # data = sock.recvfrom(1024)
    data = sock.recv(1024)

    # data = data[0]
    # print(data)
    print('[+]' + str(data))

    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    t_host = "104.17.92.24"
    t_port = 443

    sock.connect((t_host, t_port))
    sock.send('GET HTTP/1.1 \r\n')

    ret = sock.recv(1024)
    print('[+]' + str(ret))
    """
