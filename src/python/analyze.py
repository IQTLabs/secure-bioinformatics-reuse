import json
import logging
import numpy as np
from pathlib import Path
import pprint


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
            for detection in scan_result["detections"]:
                if detection["score"] > 0:
                    detections.append(detection)
            scan_result["detections"] = detections
            scan_results.append(scan_result)
        logger.info("Dumping scan results file: {0}".format(SCAN_RESULTS_FILE))
        with SCAN_RESULTS_FILE.open("w") as fp:
            json.dump(scan_results, fp, indent=4)
    return scan_results


def summarize_aura_scan_results(scan_results):
    with SCAN_SUMMARY_FILE.open("w") as fp:
        fp.write(
            "score,detection type,severity,location,line number\n"
        )
        for scan_result in scan_results:
            name = scan_result["name"].replace("/home/", "")
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
                fp.write(
                    f"{score},{det_type},{severity},{location},{line_no}\n"
                )


if __name__ == "__main__":
    scan_results = load_aura_scan_results()
    summarize_aura_scan_results(scan_results)
